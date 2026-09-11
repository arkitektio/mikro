"""Building a dataset's resolution pyramid.

``create_array_dataset`` takes level 0 as ``data`` and every coarser level as a
``ScaleInput`` in ``scales``. Nothing enforces that split, so it gets restated in
prose everywhere it is used — and listing level 0 in both silently uploads the
base twice. ``dataset_arrays`` returns the two halves already separated, which
makes the rule structural instead of documented::

    data, scales = dataset_arrays(volume, levels=6, method="mean")
    create_array_dataset(data=data, scales=scales, name=..., axes=[...])

Three things this handles that hand-written pyramids get right only by accident:

* **Categorical axes keep their extent.** The server refuses to downsample a
  CHANNEL / COORDINATE / INDEX axis — a fractional coordinate between two
  categories means nothing — so only spatial axes coarsen by default.
* **The reduction is a choice.** ``max`` keeps thin bright structures visible,
  ``mean`` is the honest mipmap, ``sum`` conserves photon counts, ``nearest``
  just subsamples. Picking one per dataset is the caller's business; it is also
  recorded as provenance on the level's edge.
* **A lazy base is computed once.** See ``dataset_arrays``.
"""

from __future__ import annotations

import atexit
import shutil
import tempfile
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Final

import xarray as xr

from mikro_next.vocabulary import (
    COARSENABLE_AXIS_TYPES,
    AxisTypeName,
    Reduction,
    axis_type_rank,
    default_axis_type,
)

if TYPE_CHECKING:
    from mikro_next.api.schema import AxisInput, ScaleInput, ScaleMethod


# The reductions xarray's ``coarsen`` can apply, plus ``nearest`` which is a
# stride rather than a reduction, mapped to the ``ScaleMethod`` each one is
# recorded as on the level's transformation. The two vocabularies are not the
# same list: ``mean`` is what xarray calls it and ``AREA`` is what the server
# calls the same operation, and ``sum`` has no member at all — pooling that
# conserves counts is not a resampling filter, so it travels with no method
# rather than being misreported as one of the others.
_REDUCTIONS: Final[Mapping[Reduction, str | None]] = {
    "max": "MAX",
    "mean": "AREA",
    "sum": None,
    "min": "MIN",
    "nearest": "NEAREST",
}


def canonical(
    array: xr.DataArray, types: Mapping[str, AxisTypeName] | None = None
) -> xr.DataArray:
    """Reorder an array's dimensions into the axis order the server requires:
    time, then channel and custom types, then space.

    The order is load-bearing rather than cosmetic — the render axes are derived
    from the *position* of the spatial axes (x is the last one, y the one before
    it), so a mis-ordered array does not fail to render, it renders wrongly. The
    server rejects anything out of order for exactly that reason.

    Axis types are inferred from the names (``t``/``time`` -> TIME,
    ``c``/``channel`` -> CHANNEL, everything else SPACE); pass ``types`` to name
    them explicitly where the convention does not hold. Axes of the same rank
    keep their relative order, so ``(z, y, x)`` is left alone.

    This is lazy — for a dask-backed array no data moves.
    """
    types = types or {}
    dims = [str(d) for d in array.dims]
    ordered = sorted(
        dims,
        key=lambda d: axis_type_rank(_axis_type_of(d, types)),
    )
    if ordered == dims:
        return array
    return array.transpose(*ordered)


def _axis_type_of(name: str, types: Mapping[str, AxisTypeName]) -> AxisTypeName:
    """The declared type of an axis, falling back to the bare-name convention.

    Written out rather than ``types.get(name, default_axis_type(name))`` because
    that evaluates the fallback eagerly — and the fallback now raises on a name
    the convention does not know, so a caller who *did* declare the type would
    still hit it.
    """
    if name in types:
        return types[name]
    return default_axis_type(name)


def axes_for(
    array: xr.DataArray,
    *,
    types: Mapping[str, AxisTypeName] | None = None,
    long_names: Mapping[str, str] | None = None,
) -> list[AxisInput]:
    """The `AxisInput` list describing an array's dimensions, in array order.

    The type of each axis comes from ``types`` where the caller states it and from the
    bare-name convention otherwise — so the axes a converter has to *think* about are
    the ones it names, and the rest follow. Stating a type is not optional decoration:
    the pyramid coarsens exactly the SPACE axes, so an axis left to a guess that guesses
    wrong is downsampled away.

        axes_for(data, types={"tile": "INDEX"}, long_names=AXIS_LONG_NAMES)

    Args:
        array: The array whose ``dims`` are being described.
        types: Axis name -> `AxisType` name, for the axes the convention does not know
            or would get wrong.
        long_names: Axis name -> human-readable label. Defaults to the axis name.

    Returns:
        One `AxisInput` per dimension, in the array's own order.

    Raises:
        UnknownAxisName: If an axis is neither in ``types`` nor known to the convention.
    """
    from mikro_next.api.schema import AxisInput, AxisType

    declared = types or {}
    labels = long_names or {}
    return [
        AxisInput(
            name=dim,
            type=AxisType(_axis_type_of(dim, declared)),
            # The alias, not `long_name=`: both populate the same field, but the
            # generated model declares the alias, so this is the spelling the type
            # checker can see.
            long_name=labels.get(dim, dim),
        )
        for dim in (str(d) for d in array.dims)
    ]


def _coarsen_dims(
    array: xr.DataArray,
    axes: Sequence[str] | None,
    types: Mapping[str, AxisTypeName],
) -> list[str]:
    """Which of the array's dimensions this pyramid halves.

    By default the spatial ones: a pyramid is a level-of-detail structure, and
    stepping through time or compositing channels is not what zooming does. A
    caller who does want another axis coarsened names it in ``axes``.
    """
    dims = [str(d) for d in array.dims]

    if axes is None:
        return [d for d in dims if _axis_type_of(d, types) == "SPACE"]

    chosen = [str(a) for a in axes]
    unknown = [a for a in chosen if a not in dims]
    if unknown:
        raise ValueError(
            f"Cannot coarsen along {unknown}: the array has dimensions {dims}"
        )
    categorical = [
        a
        for a in chosen
        if _axis_type_of(a, types) not in COARSENABLE_AXIS_TYPES
    ]
    if categorical:
        raise ValueError(
            f"Cannot coarsen along {categorical}: only continuously sampled axes "
            f"(SPACE, TIME, MICROTIME) may be downsampled. A position halfway "
            f"between two channels — or two object ids — is not a thing, so the "
            f"server rejects a pyramid whose categorical axes change extent."
        )
    return chosen


def _downsample(
    array: xr.DataArray, dims: Sequence[str], method: Reduction
) -> xr.DataArray:
    """One pyramid step: halve `dims`, reducing with `method`."""
    if method == "nearest":
        out = array.isel({d: slice(None, None, 2) for d in dims})
    else:
        coarsened = array.coarsen({d: 2 for d in dims}, boundary="trim")  # type: ignore[arg-type]
        out = getattr(coarsened, method)()
    # `mean` on an integer array promotes to float; a pyramid level that changes
    # dtype halfway up is not the same image at a lower resolution.
    out = out.astype(array.dtype)
    out.name = array.name
    return out


def _materialize(array: xr.DataArray) -> xr.DataArray:
    """Write a lazy array to a scratch Zarr store once and read it back.

    Every coarser level is a lazy view chained back to level 0, and dask does not
    cache results across separate top-level computations — so without this, each
    of the ``levels`` uploads re-derives the whole base expression from scratch.
    For a generated or heavily-computed base that turns "build level 0 once" into
    "build it once per level", which is the difference between a large upload
    being slow and being unusable.

    The scratch directory is removed at interpreter exit rather than here: the
    levels read from it lazily, all the way through the upload.
    """
    import dask.array as da

    scratch = tempfile.mkdtemp(prefix="mikro_pyramid_")
    atexit.register(shutil.rmtree, scratch, ignore_errors=True)

    path = f"{scratch}/level0.zarr"
    array.data.to_zarr(path, overwrite=True)  # one streamed pass, chunk by chunk
    on_disk = xr.DataArray(da.from_zarr(path), dims=array.dims, name=array.name)
    on_disk.attrs.update(array.attrs)
    return on_disk


def _is_lazy(array: xr.DataArray) -> bool:
    """Whether the array is dask-backed, and so re-derived on every compute."""
    return hasattr(array.data, "dask")


def build_pyramid(
    base: xr.DataArray,
    levels: int = 5,
    method: Reduction = "max",
    *,
    axes: Sequence[str] | None = None,
    types: Mapping[str, AxisTypeName] | None = None,
    materialize: bool | None = None,
) -> list[xr.DataArray]:
    """A resolution pyramid: `base` and each successive halving of it.

    Level *i* is a real downsample of level *i-1*, chained — which is what a
    scanner or a pyramid builder actually produces, and what the level-of-detail
    renderer walks on zoom. The returned list is level 0 first.

    Args:
        base: The full-resolution array, with named dimensions.
        levels: How many levels to produce, including the base. Halving stops
            early if no dimension is left with more than one sample.
        method: The reduction — one of ``max``, ``mean``, ``sum``, ``min`` or
            ``nearest``.
        axes: Which dimensions to halve. Defaults to the spatial ones.
        types: Axis name -> type, where the naming convention does not hold
            (e.g. ``{"m": "MICROTIME"}``).
        materialize: Write a lazy base to a scratch Zarr store first, so it is
            computed once rather than once per level. Defaults to doing so
            exactly when it pays off — a dask-backed base with more than one
            level.
    """
    if levels < 1:
        raise ValueError(f"levels must be at least 1, got {levels}")
    if method not in _REDUCTIONS:
        raise ValueError(
            f"Unknown reduction {method!r}. Pick one of {', '.join(_REDUCTIONS)}."
        )

    types = dict(types or {})
    dims = _coarsen_dims(base, axes, types)

    if materialize is None:
        materialize = levels > 1 and _is_lazy(base)
    if materialize:
        base = _materialize(base)

    pyramid = [base]
    for _ in range(levels - 1):
        current = pyramid[-1]
        halvable = [d for d in dims if current.sizes[d] >= 2]
        if not halvable:
            break  # nothing left big enough to halve
        pyramid.append(_downsample(current, halvable, method))
    return pyramid


def scales_from(
    pyramid: Sequence[xr.DataArray], method: Reduction = "max"
) -> list[ScaleInput]:
    """The ``scales`` argument for a pyramid you already hold.

    Levels 1..N only: ``data`` *is* level 0, so listing it here as well would
    upload it twice. Use this when you need the level arrays for something else
    too — a histogram off the coarsest level, say — and so want
    :func:`build_pyramid` rather than :func:`dataset_arrays`::

        pyramid = build_pyramid(base, levels=8, method="mean")
        dataset = create_array_dataset(data=pyramid[0],
                                   scales=scales_from(pyramid, "mean"), ...)
    """
    from mikro_next.api.schema import ScaleInput, ScaleMethod

    if method not in _REDUCTIONS:
        raise ValueError(
            f"Unknown reduction {method!r}. Pick one of {', '.join(_REDUCTIONS)}."
        )

    recorded = _REDUCTIONS[method]
    scale_method: ScaleMethod | None = (
        ScaleMethod(recorded) if recorded is not None else None
    )
    return [
        ScaleInput(level=level, array=array, scale_method=scale_method)
        for level, array in enumerate(pyramid)
        if level > 0
    ]


def dataset_arrays(
    base: xr.DataArray,
    levels: int = 5,
    method: Reduction = "max",
    *,
    axes: Sequence[str] | None = None,
    types: Mapping[str, AxisTypeName] | None = None,
    materialize: bool | None = None,
) -> tuple[xr.DataArray, list[ScaleInput]]:
    """The ``(data, scales)`` pair ``create_array_dataset`` wants.

    Level 0 is returned separately from the rest because that is how the mutation
    takes it: ``data`` *is* level 0, and ``scales`` carries only what is coarser
    than it. Passing the base in both uploads it twice.

    No scale factor is supplied for any level — the server derives each one from
    the level's actual shape against level 0's, so a pyramid whose axes do not
    halve cleanly (36 -> 18 -> 9 -> 4) is described exactly rather than
    plausibly. ``method`` is passed along as provenance on each level's edge.

        data, scales = dataset_arrays(volume, levels=6, method="mean")

    Takes the same arguments as :func:`build_pyramid`.
    """
    pyramid = build_pyramid(
        base,
        levels=levels,
        method=method,
        axes=axes,
        types=types,
        materialize=materialize,
    )
    return pyramid[0], scales_from(pyramid, method)


__all__ = [
    "axes_for",
    "build_pyramid",
    "canonical",
    "dataset_arrays",
    "scales_from",
]
