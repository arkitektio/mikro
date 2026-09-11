"""A synthetic hyperspectral acquisition — the first SPECTRUM axis in the repo.

A 32-bin lambda stack ``(l, y, x)`` of three fluorophores whose emission spectra
overlap far too much to split by bandpass — which is the whole reason spectral
detectors exist — plus broad autofluorescence. Composed into one scene three ways:

- the **raw cube** through a **spectral phasor layer**: the same phasor the FLIM
  scripts take over MICROTIME, taken over SPECTRUM — where the phase reads as the
  spectral centre of mass instead of a lifetime. The SDL has advertised this since
  the phasor landed ("a spectral one over a hyperspectral cube"); nothing has ever
  run it,
- a **(g, s) phasor histogram** attached to the cube, so the frontend can range the
  overlay without reading it — the spectral twin of ``upload_flim.py``'s decay
  histogram,
- the **linearly unmixed** abundances ``(c, y, x)``, least-squares against the known
  spectra, drawn as one intensity layer per channel.

The lambda axis is 500-660 nm in 5 nm bins. Its 500 nm origin and 5 nm step live on
the registration edge (scale + offset), so the scene's ``l`` axis reads in real
nanometers — and like FLIM's microtime, the spectral axis is **never** in the
pyramid: re-binning it would change what a phase means between levels.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first.

Run:  python generator_hyperspectral.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import xarray as xr

from mikro_next import Unit, create_space
from arkitekt_next import easy
from mikro_next.api.schema import (
    AxisInput,
    AxisType,
    Blending,
    ColorMap,
    CoordinateAnchorInput,
    PhasorColorMode,
    PhasorTransferInput,
    PhysicalAxisInput,
    ScaleInput,
    TransferFunctionInput,
    create_array_dataset,
    create_intensity_layer,
    create_phasor_histogram,
    create_phasor_layer,
    create_scene,
)
from mikro_next import dataset_arrays

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 47
RNG = np.random.default_rng(SEED)

FIELD_SHAPE = (160, 220)  # (y, x) px, deliberately non-square
PIXEL_UM = 0.2

N_BINS = 32
LAMBDA_0 = 500.0  # nm, the first bin's centre
BIN_NM = 5.0  # nm per bin -> 500..655 nm
LAMBDAS = LAMBDA_0 + BIN_NM * np.arange(N_BINS)

# The three fluorophores: (name, emission peak nm, sigma nm, colormap for its
# unmixed channel). The first two are 30 nm apart with 13/15 nm sigmas — heavily
# overlapped, unmixable only spectrally.
FLUOROPHORES = (
    ("green-ish", 515.0, 13.0, ColorMap.GREEN),
    ("yellow-ish", 545.0, 15.0, ColorMap.MAGENTA),
    ("red-ish", 600.0, 18.0, ColorMap.CYAN),
)
AF_LEVEL = 0.06  # autofluorescence amplitude relative to the brightest signal

BRIGHTNESS = 3000.0  # expected photons in a fully-labelled pixel, over the spectrum
LEVELS = 3  # y/x-only pyramid depth

HARMONIC = 1
PHASOR_BINS = 256
MIN_PHOTONS = 200  # below this the (g, s) is shot noise, not a spectrum


# --------------------------------------------------------------------------- #
# Ground truth: three structures, three spectra
# --------------------------------------------------------------------------- #
def abundance_maps() -> np.ndarray:
    """Per-fluorophore abundance in [0, 1] — ``(3, y, x)``.

    Each fluorophore labels a different structure so the unmixed picture is
    legible at a glance: blobs (nuclei-ish), diagonal filaments, and rings."""
    yy, xx = np.mgrid[0 : FIELD_SHAPE[0], 0 : FIELD_SHAPE[1]].astype(np.float64)
    maps = np.zeros((len(FLUOROPHORES), *FIELD_SHAPE))

    # Blobs.
    for _ in range(12):
        cy, cx = RNG.uniform(10, FIELD_SHAPE[0] - 10), RNG.uniform(10, FIELD_SHAPE[1] - 10)
        r = RNG.uniform(6, 11)
        maps[0] += np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * (r / 2) ** 2)))

    # Filaments: soft ridges along wandering lines.
    for _ in range(7):
        y0 = RNG.uniform(0, FIELD_SHAPE[0])
        slope = RNG.uniform(-0.7, 0.7)
        phase, amp = RNG.uniform(0, 2 * np.pi), RNG.uniform(3, 10)
        centre = y0 + slope * xx + amp * np.sin(xx / 25 + phase)
        maps[1] += np.exp(-((yy - centre) ** 2) / (2 * 1.8**2))

    # Rings.
    for _ in range(9):
        cy, cx = RNG.uniform(15, FIELD_SHAPE[0] - 15), RNG.uniform(15, FIELD_SHAPE[1] - 15)
        r = RNG.uniform(8, 16)
        dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        maps[2] += np.exp(-((dist - r) ** 2) / (2 * 1.6**2))

    return np.clip(maps, 0.0, 1.0)


def emission_spectra() -> np.ndarray:
    """Unit-sum emission spectrum per fluorophore — ``(3, l)``."""
    spectra = np.stack(
        [np.exp(-((LAMBDAS - peak) ** 2) / (2 * sigma**2)) for _, peak, sigma, _ in FLUOROPHORES]
    )
    return spectra / spectra.sum(axis=1, keepdims=True)


def autofluorescence_spectrum() -> np.ndarray:
    """A broad, featureless downslope over the window — unit sum, ``(l,)``."""
    af = np.exp(-(LAMBDAS - LAMBDA_0) / 120.0)
    return af / af.sum()


def render_cube(maps: np.ndarray, spectra: np.ndarray, af: np.ndarray) -> xr.DataArray:
    """The detector's view: ``(l, y, x)`` uint16 photon counts with shot noise."""
    expected = np.tensordot(spectra.T, maps, axes=(1, 0)) * BRIGHTNESS
    expected += af[:, None, None] * BRIGHTNESS * AF_LEVEL
    return xr.DataArray(
        RNG.poisson(expected).astype(np.uint16), dims=("l", "y", "x"), name="lambda_stack"
    )


# --------------------------------------------------------------------------- #
# The spectral phasor and the unmixing
# --------------------------------------------------------------------------- #
def phasor(cube: np.ndarray, harmonic: int = HARMONIC):
    """Per-pixel spectral phasor ``(g, s, intensity)`` of an ``(l, y, x)`` cube.

    The same first-Fourier-coefficient-over-the-axis the FLIM scripts compute over
    microtime; over a spectrum the angle encodes the centre of mass of the emission
    and the modulus its narrowness."""
    k = np.arange(cube.shape[0], dtype=np.float64)
    angle = 2.0 * np.pi * harmonic * k / cube.shape[0]
    counts = cube.astype(np.float64)
    total = counts.sum(axis=0)
    safe = np.where(total > 0, total, 1.0)
    g = np.tensordot(np.cos(angle), counts, axes=(0, 0)) / safe
    s = np.tensordot(np.sin(angle), counts, axes=(0, 0)) / safe
    return g, s, total


def phasor_density(g: np.ndarray, s: np.ndarray, intensity: np.ndarray) -> dict:
    """The (g, s) density over pixels bright enough to mean anything.

    Bounds are the padded unit square rather than FLIM's universal semicircle: a
    spectrum peaked anywhere in the window can put its phasor in any quadrant, so
    the semicircle would clip most of the plane a spectral cloud lives in."""
    keep = intensity >= MIN_PHOTONS
    gk, sk = g[keep], s[keep]

    g_min, g_max = -1.1, 1.1
    s_min, s_max = -1.1, 1.1
    density, _, _ = np.histogram2d(
        gk, sk, bins=PHASOR_BINS, range=[[g_min, g_max], [s_min, s_max]]
    )
    # PhasorHistogram.counts is row-major with s outermost; histogram2d returns [g, s].
    return dict(
        counts=[float(c) for c in density.T.ravel()],
        bins=PHASOR_BINS,
        g_min=g_min,
        g_max=g_max,
        s_min=s_min,
        s_max=s_max,
        total=int(density.sum()),
        calibrated=False,  # no spectral flat-field measured, exactly like FLIM's IRF
    )


def unmix(cube: np.ndarray, spectra: np.ndarray, af: np.ndarray) -> np.ndarray:
    """Least-squares abundances against the known spectra — ``(3, y, x)`` float32.

    The design matrix carries the autofluorescence spectrum as a fourth component so
    the haze is absorbed there instead of leaking into whichever fluorophore slopes
    the same way; only the three real channels are returned."""
    design = np.column_stack([spectra.T, af])  # (l, 4)
    pixels = cube.reshape(cube.shape[0], -1).astype(np.float64)
    solution, *_ = np.linalg.lstsq(design, pixels, rcond=None)
    return np.clip(solution[:3], 0.0, None).astype(np.float32).reshape(3, *FIELD_SHAPE)


def spectral_pyramid(cube: xr.DataArray, levels: int) -> list[xr.DataArray]:
    """A pyramid halving only ``y``/``x`` by photon-conserving sums.

    Hand-rolled for the same reason ``upload_flim.py`` hand-rolls its own: the
    spectral axis must never be re-binned — every level would otherwise carry a
    different bin width, and the bin width is what a phase *means*. No
    ``scale_method`` is recorded because SUM is not a resampling filter."""
    arrays = [cube]
    for _ in range(levels - 1):
        current = arrays[-1]
        coarsen = {d: 2 for d in ("y", "x") if current.sizes[d] >= 2}
        if not coarsen:
            break
        down = current.coarsen(**coarsen, boundary="trim").sum().astype(cube.dtype)
        down.name = cube.name
        arrays.append(down)
    return arrays


# --------------------------------------------------------------------------- #
# Self-checks
# --------------------------------------------------------------------------- #
def check(
    cube: xr.DataArray,
    maps: np.ndarray,
    estimated: np.ndarray,
    g: np.ndarray,
    s: np.ndarray,
    intensity: np.ndarray,
) -> None:
    if cube.shape != (N_BINS, *FIELD_SHAPE):
        raise SystemExit(f"cube is {cube.shape}, expected {(N_BINS, *FIELD_SHAPE)} — transposed?")

    # The unmixing must recover the ground truth, or the spectra/maps disagree.
    for i, (name, *_rest) in enumerate(FLUOROPHORES):
        corr = float(np.corrcoef(maps[i].ravel(), estimated[i].ravel())[0, 1])
        if corr < 0.95:
            raise SystemExit(f"unmixed '{name}' correlates {corr:.3f} < 0.95 with truth")

    # The spectral phasor must (a) separate the three fluorophores and (b) order
    # them by wavelength: the phase angle is the centre of mass, so redder emission
    # means a larger angle within the window. This is the check that the phasor is
    # a *spectral* statement and not just any invertible hash of the spectrum.
    dominant = maps.argmax(axis=0)
    pure = (maps.max(axis=0) > 0.8) & (intensity >= MIN_PHOTONS)
    centers, phases = [], []
    for i in range(len(FLUOROPHORES)):
        sel = pure & (dominant == i)
        if sel.sum() < 50:
            raise SystemExit(f"fewer than 50 pure pixels for fluorophore {i} — regenerate")
        centers.append((float(g[sel].mean()), float(s[sel].mean())))
        phases.append(float(np.angle(g[sel].mean() + 1j * s[sel].mean()) % (2 * np.pi)))
    for i in range(len(centers)):
        for j in range(i + 1, len(centers)):
            dist = float(np.hypot(centers[i][0] - centers[j][0], centers[i][1] - centers[j][1]))
            if dist < 0.15:
                raise SystemExit(
                    f"phasor centres {i} and {j} are {dist:.3f} apart — spectra not separated"
                )
    if not (phases[0] < phases[1] < phases[2]):
        raise SystemExit(f"phasor phases {phases} do not increase with emission wavelength")

    print(
        f"  checks pass: unmixing r>0.95 for all three, phasor centres separated, "
        f"phase increases with wavelength ({', '.join(f'{p:.2f}' for p in phases)} rad)"
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Rendering the lambda stack ({N_BINS} bins x {FIELD_SHAPE} px)…")
    maps = abundance_maps()
    spectra = emission_spectra()
    af = autofluorescence_spectrum()
    cube = render_cube(maps, spectra, af)
    print(f"  cube {cube.shape} {cube.dtype} (~{cube.nbytes / 1e6:.1f} MB)")

    print("Computing the spectral phasor and unmixing…")
    g, s, intensity = phasor(np.asarray(cube.data))
    density = phasor_density(g, s, intensity)
    estimated = unmix(np.asarray(cube.data), spectra, af)

    check(cube, maps, estimated, g, s, intensity)

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy(identifier="neuron-overlay") as app:
        # One world with a real wavelength axis. The 5 nm bin width AND the 500 nm
        # origin live on the cube's registration edge (scale + offset), which is what
        # makes the scene's `l` read in absolute nanometers.
        world = create_space(
            "Hyperspectral · field",
            [
                PhysicalAxisInput(name="l", type=AxisType.SPECTRUM, unit=Unit("nanometer")),
                PhysicalAxisInput(name="y", type=AxisType.SPACE, unit=Unit("micrometer")),
                PhysicalAxisInput(name="x", type=AxisType.SPACE, unit=Unit("micrometer")),
            ],
        )

        print("Uploading lambda stack…")
        pyramid = spectral_pyramid(cube, LEVELS)
        cube_ds = create_array_dataset(
            data=pyramid[0],
            scales=[ScaleInput(level=i, array=level) for i, level in enumerate(pyramid) if i > 0],
            name="Hyperspectral · lambda stack (500-655 nm)",
            # `l` is not an inferable name, so the type is stated.
            axes=[
                AxisInput(name="l", type=AxisType.SPECTRUM),
                AxisInput(name="y", type=AxisType.SPACE),
                AxisInput(name="x", type=AxisType.SPACE),
            ],
            anchors=[CoordinateAnchorInput.histogram_anchor(cube)],
        )
        world.register(
            cube_ds,
            scale={"l": BIN_NM, "y": PIXEL_UM, "x": PIXEL_UM},
            l=LAMBDA_0,
        )

        # The (g, s) density, so the frontend can range the overlay without reading
        # the cube — the first SPECTRUM-axis phasor histogram (the server's
        # `_assert_phasor_axis` allows MICROTIME or SPECTRUM; only MICROTIME ever ran).
        print("Attaching spectral phasor histogram…")
        histogram = create_phasor_histogram(
            dataset=cube_ds,
            axis="l",
            harmonic=HARMONIC,
            profile=[float(v) for v in np.asarray(cube.data).sum(axis=(1, 2))],  # the spectrum
            **density,
        )
        print(f"  harmonic {histogram.harmonic}, {histogram.bins}² grid over {histogram.total:,} px")

        print("Uploading unmixed abundances…")
        unmixed = xr.DataArray(estimated, dims=("c", "y", "x"), name="unmixed")
        unmixed_data, unmixed_scales = dataset_arrays(unmixed, levels=LEVELS, method="max")
        unmixed_ds = create_array_dataset(
            data=unmixed_data,
            scales=unmixed_scales,
            name="Hyperspectral · unmixed abundances",
            axes=["c", "y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(unmixed)],
        )
        world.register(unmixed_ds, scale={"y": PIXEL_UM, "x": PIXEL_UM})

        print("Composing the scene…")
        scene = create_scene(name="Hyperspectral · synthetic", coordinate_system=world.id)

        # The spectral phasor overlay: phase = spectral centre of mass, mapped over
        # the emission window, faded out where too few photons back it.
        create_phasor_layer(
            lens=cube_ds.lens(),
            scene=scene,
            phasor_axis="l",
            harmonic=HARMONIC,
            transfer=PhasorTransferInput(
                mode=PhasorColorMode.PHASE,
                min=f"{LAMBDA_0:.0f} nm",
                max=f"{LAMBDAS[-1]:.0f} nm",
                colormap=ColorMap.RAINBOW,
                weight_by_intensity=True,
                intensity=TransferFunctionInput(colormap=ColorMap.GREY),
            ),
            blending=Blending.NORMAL,
            order=0,
        )

        # One intensity layer per unmixed channel — a CHANNEL position is a
        # fluorophore, and each gets its own layer, never a packed composite.
        clim = float(np.percentile(estimated, 99.5))
        for index, (name, _peak, _sigma, colormap) in enumerate(FLUOROPHORES):
            create_intensity_layer(
                lens=unmixed_ds.lens(),
                scene=scene,
                intensity_axis="c",
                intensity_index=index,
                colormap=colormap,
                clim_min=0.0,
                clim_max=clim,
                order=index + 1,
                visible=False,  # the scene opens on the phasor; unmixing is one click away
            )

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  lambda stack: dataset {cube_ds.id} ({N_BINS} bins, phasor histogram {histogram.id})")
        print(f"  unmixed     : dataset {unmixed_ds.id} (3 channels)")
