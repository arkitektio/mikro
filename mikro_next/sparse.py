"""Checking a sparse dataset's declaration against the matrix it is made of, before it moves.

``create_sparse_dataset`` takes the generated inputs directly -- ``SparseAxisInput`` per axis,
each carrying its own ``identifiedBy`` -- and this module is what checks them, the way
:mod:`mikro_next.tables` checks a table's. Nothing about the *matrix* is declared: its shape,
each layout's encoding and its chunking are read off the artifact when the upload is finished.
What a caller writes is one statement per axis of what its positions are::

    create_sparse_dataset(
        name="expression",
        store=[counts.tocsr(), counts.tocsc()],
        axes=[
            SparseAxisInput(name="object", identifiedBy=[DatasetIdentifiesInput(dataset=mask.id)]),
            SparseAxisInput(name="gene", identifiedBy=[TableIdentifiesInput(table=genes.id)]),
        ],
    )

Every refusal below mirrors one the server already makes, and none is stricter -- the client's
copy is what the caller wrote and the server's is what arrived, and the pair is worth more than
either alone. What the pair buys here that it does not buy on the table path is *order*.
``funcs.execute`` validates at ``:94`` and uploads at ``:97``, so a refusal raised here comes
before the bytes move; the server's comes after. On a matrix that is measured in gigabytes that
is the whole difference.

One of the six is not merely earlier here, it is **only** possible here:

* :func:`check_against_store` compares the declared axis count against the matrix's own shape.
  The server does the same at ``core/mutations/sparse_dataset.py:130`` -- but it reads that
  shape off a row recorded at ``finishSparseUpload``, so it has nothing to compare against
  until the upload has already happened. This side is holding the matrix. It is also the
  refusal with the worst silent failure: a declaration that disagrees with the bytes "places
  every lookup one position out and raises nothing".

Two entry points rather than one, and the split is not cosmetic. Only the shape check needs the
store; the other five are statements about the axes alone. Keeping them separable is what lets
the trait run them *above* its store guard -- and what lets them be tested without the optional
``sporadik`` extra installed.

Deliberately not re-checked here: two layouts compressing the same axis, and layouts of
differing shape. ``sporadik.layouts_of`` already refuses both, inside ``SporadikLike.validate``,
which runs before any of this. Stating the same refusal twice is how two copies drift apart.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from sporadik import Layout

    from mikro_next.api.schema import SparseAxisInput

#: The lowest rank a sparse dataset can have. Two, because a single compressed axis needs at
#: least one other axis to hold the positions. Mirrors the server's ``_MIN_RANK``
#: (``core/mutations/sparse_dataset.py:56``); ``sporadik.spec.MIN_RANK`` is the third copy, and
#: the three are one number because the format, the wire and this check are one rule.
#:
#: **There is no highest.** A layout is one axis made contiguous, so an array of rank *n* has up
#: to *n* of them, and a (cell, metabolite, adduct) tensor is an ordinary sparse dataset.
MIN_RANK: Final[int] = 2


class SparseDeclarationError(ValueError):
    """Raised when a declaration cannot describe the matrix it is made for."""


def _enum_value(value: object) -> str:
    """An enum-valued field's value, however it is spelled.

    The generated models set ``use_enum_values=True``, so a model constructed with an enum
    member holds the plain string. The normalizer stays because a field can also be read off a
    model built some other way, and the cost of being wrong here is a check that silently
    passes. A local copy on purpose: :mod:`mikro_next.tables`, :mod:`mikro_next.traits` and
    :mod:`mikro_next.specs` each carry their own, and sharing it is a change to five call sites
    rather than to this one.
    """
    # ``str(...)`` where :mod:`mikro_next.tables` returns the attribute directly. The same
    # answer for every input this sees, and it type-checks, where that copy carries a standing
    # ``reportReturnType`` complaint.
    return str(getattr(value, "value", value) or "")


def _identifications(axis: SparseAxisInput) -> tuple:
    """The identifications on one axis, under either spelling of the field.

    ``identifiedBy`` is the alias and ``identified_by`` the field name, and the models are
    ``populate_by_name=True``, so a model can have been built through either.
    """
    entries = getattr(axis, "identified_by", None)
    if entries is None:
        entries = getattr(axis, "identifiedBy", None)
    return tuple(entries or ())


def check_axes(axes: Sequence[SparseAxisInput]) -> None:
    """Refuse a set of axes that could not describe any matrix.

    Five refusals, in the order the server makes them, none of which needs the store:

    1. fewer than :data:`MIN_RANK` axes (``sparse_dataset.py:204``);
    2. a duplicate axis name (``:209``);
    3. an axis whose ``identifiedBy`` is empty (``:170``);
    4. nothing anywhere that keys the matrix (``:187``);
    5. more than one table identifying one axis (``core/logic/identification.py:81``).

    Args:
        axes: The declared axes, in the order the store's shape is written.

    Raises:
        SparseDeclarationError: If any of the five holds.
    """
    names = [axis.name for axis in axes]

    if len(axes) < MIN_RANK:
        raise SparseDeclarationError(
            f"A sparse dataset declares at least {MIN_RANK} axes and this one declares "
            f"{len(axes)} {names}: a single compressed axis needs at least one other to hold "
            "the positions. The count is checked against the store's own shape as well, so it "
            "is the matrix that decides the rank rather than the declaration."
        )

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise SparseDeclarationError(
            f"The axis {duplicates} is declared more than once. An axis name is how a "
            "colouring names a position along it, so it has to pick one axis."
        )

    empty = [axis.name for axis in axes if not _identifications(axis)]
    if empty:
        raise SparseDeclarationError(
            f"The axes {empty} have an empty `identifiedBy`. An axis of a sparse matrix is "
            "positions and nothing else, so one that does not say what they are is one no "
            "source could ever key -- there is no FIELD edge onto it and no colouring along "
            "it. Name a mask, a collection, or the table whose rows the positions are."
        )

    # `keyed` is not "the axes with no table on them". Fan-in is legal -- one axis may carry a
    # mask *and* the table its positions enumerate -- so an axis can have a table and still be
    # keyed. The server's own predicate is over every identification on every axis, and the
    # kinds that key are the kinds that author an edge (`core/inputs/identification.py:67`).
    if not any(_enum_value(entry.kind) != "TABLE" for axis in axes for entry in _identifications(axis)):
        raise SparseDeclarationError(
            "Every axis is identified by a table, so nothing keys this matrix: no FIELD edge "
            "is authored, no layer can reach it, and no colouring over it could ever be "
            "accepted. At least one axis has to be identified by a source whose own contents "
            "are the ids -- a mask's pixels, a collection's geometry."
        )

    for axis in axes:
        tables = [entry for entry in _identifications(axis) if _enum_value(entry.kind) == "TABLE"]
        if len(tables) > 1:
            raise SparseDeclarationError(
                f"Axis {axis.name!r} is identified by more than one table. An axis enumerates "
                "one thing: two tables would be two different answers to what a position "
                "along it is. Fan-in is only meaningful for the kinds that author an edge -- "
                "two masks may key one axis, because each edge stands on its own."
            )


def check_against_store(
    axes: Sequence[SparseAxisInput],
    layouts: Mapping[int, Layout],
) -> None:
    """Refuse a declaration that disagrees with the matrix's own shape.

    The one refusal the server cannot make first: it reads the shape off a row written at
    ``finishSparseUpload``, so it has no shape to compare against until the bytes have landed.
    Here the matrix is in hand.

    Takes the layouts as a plain mapping rather than reaching into ``SporadikLike``, because
    the only thing read off one is ``.shape`` -- which is what lets this be tested against a
    stub, with no ``sporadik`` installed.

    The shape is read off any layout: ``sporadik.layouts_of`` has already refused a set whose
    members disagree, so they are all the same. And it is ``Layout.shape``, the *array's* own,
    never ``declared_shape``, which is the raveled one a rank-three layout's group declares.

    Args:
        axes: The declared axes, in the order the store's shape is written.
        layouts: The store's layouts, keyed by the axis each makes contiguous.

    Raises:
        SparseDeclarationError: If the axis count disagrees with the matrix's rank.
    """
    if not layouts:
        return

    shape = tuple(int(size) for size in next(iter(layouts.values())).shape)
    if len(shape) != len(axes):
        names = [axis.name for axis in axes]
        raise SparseDeclarationError(
            f"{len(axes)} axes {names} are declared, but the matrix has shape {list(shape)}. "
            "The axes describe the store, so there are the same number of them -- and the "
            "order matters too: they are read in the order the shape is written. A "
            "declaration that disagrees with the bytes places every lookup one position out "
            "and raises nothing, which is why it is refused here rather than discovered later."
        )
