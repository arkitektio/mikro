"""A synthetic SMLM acquisition — table, points, reconstruction and raw movie in one scene.

Four artifacts, each a different face of the same ground truth:

- the **localization table**: one row per blink event, with the physical (y, x) in
  micrometers plus photons, precision and the emitter it came from,
- a **point layer** drawing that table directly — the coordinates come from the table's
  own axis columns, the layer only styles them,
- the **super-resolution render**: a 10 nm-per-pixel image reconstructed from nothing
  but the localizations,
- the **raw camera movie** ``(t, y, x)``: the diffraction-limited blinking frames the
  localizations were fitted from, at 100 nm pixels.

All three data grids share one world; each pixel size lives on its registration edge,
which is what makes a 100 nm movie, a 10 nm render and a table in plain micrometers
land on top of each other.

The field is deliberately non-square (14 x 20 µm) so a y/x transpose anywhere — the
histogram, the table's axis-column order, the raw render — fails the self-checks
loudly instead of drawing rotated.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first:
everything is generated and checked locally before anything is uploaded.

Run:  python generator_smlm.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import gaussian_filter

from mikro import Unit, create_space, dataset_arrays
from arkitekt_next import easy
from mikro.api.schema import (
    AxisType,
    ColorMap,
    ColumnColorByInput,
    ColumnInput,
    ColumnRole,
    CoordinateAnchorInput,
    LabelFilterByInput,
    ProjectionMode,
    create_array_dataset,
    create_intensity_layer,
    create_layer,
    create_lens,
    create_point_layer,
    create_scene,
    create_table_dataset,
)
from mikro.render import channel_graph

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 23
RNG = np.random.default_rng(SEED)

# Camera grid: (y, x) in pixels, deliberately non-square.
CAM_SHAPE = (140, 200)
CAM_PX = 0.1  # µm per camera pixel
FIELD = (CAM_SHAPE[0] * CAM_PX, CAM_SHAPE[1] * CAM_PX)  # (14, 20) µm

FRAMES = 300
EXPOSURE = 0.03  # seconds per frame

# The reconstruction grid: 10x finer than the camera.
SR_FACTOR = 10
SR_PX = CAM_PX / SR_FACTOR  # 10 nm
SR_SHAPE = (CAM_SHAPE[0] * SR_FACTOR, CAM_SHAPE[1] * SR_FACTOR)

# Optics and photophysics.
PSF_SIGMA = 1.3 * CAM_PX  # diffraction-limited PSF sigma, µm (1.3 px)
PHOTON_MEAN = 1200.0  # lognormal mean of an on-event's photon count
BACKGROUND = 100.0  # camera counts per pixel per frame
# Localization precision: PSF / sqrt(N), with a factor for background and pixelation.
# ~1200 photons lands at ~15 nm, the classic dSTORM regime.
PRECISION_FACTOR = 4.0

MARGIN = 1.5  # µm the structures keep from the field edge
EMITTER_JITTER = 0.020  # µm of labelling jitter around the true structure
LOCS_PER_FRAME = 40.0  # mean blink events per camera frame

PHOTON_CUT = 800.0  # the offered-but-inactive "bright only" filter threshold


# --------------------------------------------------------------------------- #
# Ground truth: filaments and rings, emitters sampled along them
# --------------------------------------------------------------------------- #
def bezier(p0, p1, p2, n: int) -> np.ndarray:
    """``n`` points along a quadratic Bézier — ``(n, 2)`` in (y, x)."""
    t = np.linspace(0.0, 1.0, n)[:, None]
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t**2 * p2


def random_point() -> np.ndarray:
    """A (y, x) position inside the field, off the margin."""
    return np.array(
        [RNG.uniform(MARGIN, extent - MARGIN) for extent in FIELD], dtype=np.float64
    )


def emitter_positions() -> np.ndarray:
    """The labelled structures — microtubule-like curves and a few rings — as
    ``(n_emitters, 2)`` (y, x) positions in micrometers.

    Emitters sit on the structure plus labelling jitter, the way an antibody
    does: the jitter is part of the truth, not of the measurement."""
    pieces = []

    # Four filaments crossing the field, curvature from a wandering control point.
    for _ in range(4):
        p0, p2 = random_point(), random_point()
        mid = (p0 + p2) / 2 + RNG.normal(0.0, 2.5, size=2)
        mid = np.clip(mid, MARGIN, np.array(FIELD) - MARGIN)
        length = float(np.linalg.norm(p2 - p0))
        pieces.append(bezier(p0, mid, p2, max(int(length * 60), 60)))

    # Three rings, nuclear-pore-ish but grown up to stay resolvable.
    for _ in range(3):
        center = random_point()
        radius = RNG.uniform(0.4, 0.8)
        angles = np.linspace(0.0, 2 * np.pi, int(radius * 2 * np.pi * 60), endpoint=False)
        ring = center + radius * np.stack([np.sin(angles), np.cos(angles)], axis=1)
        pieces.append(np.clip(ring, MARGIN / 2, np.array(FIELD) - MARGIN / 2))

    positions = np.concatenate(pieces, axis=0)
    return positions + RNG.normal(0.0, EMITTER_JITTER, size=positions.shape)


def blink(emitters: np.ndarray) -> pd.DataFrame:
    """Every blink event over the acquisition — the localization table.

    Each frame every emitter fires independently with a probability tuned to the
    target event rate. An event's photon count draws the localization error: the
    measured position is the emitter plus noise at sigma = PSF * factor / sqrt(N),
    and that sigma is recorded as the row's precision, the way a fitter reports it."""
    n = len(emitters)
    p_on = LOCS_PER_FRAME / n

    frames_col, rows = [], []
    for frame in range(FRAMES):
        on = np.nonzero(RNG.random(n) < p_on)[0]
        frames_col.append(np.full(len(on), frame, dtype=np.int64))
        rows.append(on)
    frames_col = np.concatenate(frames_col)
    emitter_id = np.concatenate(rows)

    photons = RNG.lognormal(np.log(PHOTON_MEAN), 0.45, size=len(emitter_id))
    sigma = PSF_SIGMA * PRECISION_FACTOR / np.sqrt(photons)
    measured = emitters[emitter_id] + RNG.normal(0.0, 1.0, size=(len(emitter_id), 2)) * sigma[:, None]

    frame = pd.DataFrame(
        {
            # Axis columns first, in (y, x) order — the file's column order IS the
            # table's axis order, and x-before-y would transpose silently.
            "y": measured[:, 0],
            "x": measured[:, 1],
            "frame": frames_col,
            "photons": photons,
            "sigma": sigma,
            "emitter_id": emitter_id.astype(np.int64),
        }
    )
    # An error can carry a dim localization off the field; those rows a real fitter
    # would also drop, and keeping them would fail the in-field check below.
    inside = (
        (frame["y"] >= 0) & (frame["y"] < FIELD[0]) & (frame["x"] >= 0) & (frame["x"] < FIELD[1])
    )
    return frame[inside].reset_index(drop=True)


# --------------------------------------------------------------------------- #
# The two images: raw blinking movie and super-resolution render
# --------------------------------------------------------------------------- #
def raw_movie(locs: pd.DataFrame) -> xr.DataArray:
    """The camera's view: each blink a diffraction-limited Gaussian, ``(t, y, x)`` uint16.

    Rendered per event into a small window (±4 PSF sigma) rather than over the whole
    frame; the event's photons are spread over the Gaussian, so the peak is
    photons / (2 pi sigma^2) above a Poisson background."""
    sigma_px = PSF_SIGMA / CAM_PX
    half = int(np.ceil(4 * sigma_px))
    win = np.arange(-half, half + 1, dtype=np.float64)

    movie = np.zeros((FRAMES, *CAM_SHAPE), dtype=np.float64)
    y_px = locs["y"].to_numpy() / CAM_PX
    x_px = locs["x"].to_numpy() / CAM_PX
    frames = locs["frame"].to_numpy()
    photons = locs["photons"].to_numpy()

    for frame, yc, xc, n_ph in zip(frames, y_px, x_px, photons):
        iy, ix = int(round(yc)), int(round(xc))
        gy = np.exp(-((win + iy - yc) ** 2) / (2 * sigma_px**2))
        gx = np.exp(-((win + ix - xc) ** 2) / (2 * sigma_px**2))
        patch = n_ph / (2 * np.pi * sigma_px**2) * np.outer(gy, gx)

        y0, y1 = max(iy - half, 0), min(iy + half + 1, CAM_SHAPE[0])
        x0, x1 = max(ix - half, 0), min(ix + half + 1, CAM_SHAPE[1])
        movie[frame, y0:y1, x0:x1] += patch[
            y0 - (iy - half) : y1 - (iy - half), x0 - (ix - half) : x1 - (ix - half)
        ]

    noisy = RNG.poisson(movie + BACKGROUND).astype(np.uint16)
    return xr.DataArray(noisy, dims=("t", "y", "x"), name="raw")


def sr_render(locs: pd.DataFrame) -> tuple[xr.DataArray, np.ndarray]:
    """The reconstruction: a 10 nm histogram of the localizations, blurred at the
    median precision — ``(y, x)`` uint16. Returns the raw counts too, for the check
    that every localization landed in a bin."""
    counts, _, _ = np.histogram2d(
        locs["y"],
        locs["x"],
        bins=SR_SHAPE,
        range=[[0.0, FIELD[0]], [0.0, FIELD[1]]],
    )
    blurred = gaussian_filter(counts, sigma=float(locs["sigma"].median()) / SR_PX)
    image = (blurred / blurred.max() * 65535.0).astype(np.uint16)
    return xr.DataArray(image, dims=("y", "x"), name="sr"), counts


# --------------------------------------------------------------------------- #
# Self-checks — everything that can be wrong locally, checked locally
# --------------------------------------------------------------------------- #
def check(locs: pd.DataFrame, movie: xr.DataArray, sr: xr.DataArray, counts: np.ndarray) -> None:
    if not ((locs[["y", "x"]] >= 0).all().all() and (locs["y"] < FIELD[0]).all() and (locs["x"] < FIELD[1]).all()):
        raise SystemExit("localizations fall outside the field — do not upload")

    # The transpose canary: the field is non-square, so a (y, x) swap anywhere
    # changes this shape.
    if sr.shape != SR_SHAPE:
        raise SystemExit(f"SR render is {sr.shape}, expected {SR_SHAPE} — transposed?")

    bin_y = np.minimum((locs["y"] / SR_PX).astype(int), SR_SHAPE[0] - 1)
    bin_x = np.minimum((locs["x"] / SR_PX).astype(int), SR_SHAPE[1] - 1)
    if not (counts[bin_y, bin_x] > 0).all():
        raise SystemExit("a localization's own SR bin is empty — histogram axes disagree")

    # The movie must actually contain the blinks: the time-mean at emitter pixels
    # has to stand clear of the background.
    mean_img = movie.values.mean(axis=0)
    at_locs = mean_img[
        np.minimum((locs["y"] / CAM_PX).astype(int), CAM_SHAPE[0] - 1),
        np.minimum((locs["x"] / CAM_PX).astype(int), CAM_SHAPE[1] - 1),
    ].mean()
    if at_locs < BACKGROUND * 1.05:
        raise SystemExit(
            f"emitter pixels average {at_locs:.1f} vs background {BACKGROUND} — "
            f"the movie and the table disagree, do not upload"
        )

    print(
        f"  checks pass: {len(locs)} localizations in-field and binned, "
        f"emitter pixels at {at_locs:.0f} counts over background {BACKGROUND:.0f}"
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Sampling emitters ({FIELD[0]:.0f}x{FIELD[1]:.0f} µm field)…")
    emitters = emitter_positions()
    print(f"  {len(emitters)} emitters on 4 filaments + 3 rings")

    print(f"Blinking over {FRAMES} frames…")
    locs = blink(emitters)
    print(f"  {len(locs)} localizations, median precision {locs['sigma'].median() * 1000:.0f} nm")

    print("Rendering the raw movie and the reconstruction…")
    movie = raw_movie(locs)
    sr, counts = sr_render(locs)
    print(f"  raw {movie.shape} {movie.dtype} (~{movie.nbytes / 1e6:.0f} MB), SR {sr.shape} {sr.dtype}")

    check(locs, movie, sr, counts)

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's identifier, the established pattern (see
    # generator_flow_volume / generator_turbulence): its grant is cached, so the
    # run needs no device-code round.
    with easy(identifier="neuron-overlay") as app:
        # One world for all of it. Each grid's pixel size is a fact about its
        # registration edge, not about the space — which is the only way a 100 nm
        # movie, a 10 nm render and a table in micrometers share one frame.
        world = create_space(
            "SMLM · field",
            {"t": Unit("second"), "y": Unit("micrometer"), "x": Unit("micrometer")},
        )

        print("Uploading raw movie…")
        raw_data, raw_scales = dataset_arrays(movie, levels=3, method="max")
        raw_ds = create_array_dataset(
            data=raw_data,
            scales=raw_scales,
            name="SMLM · raw blinking movie",
            axes=["t", "y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(movie)],
        )
        world.register(raw_ds, scale={"t": EXPOSURE, "y": CAM_PX, "x": CAM_PX})

        print("Uploading reconstruction…")
        # MAX pyramid: the render is sparse dots on black, and an averaged level
        # dims them out of existence long before it runs out of resolution.
        sr_data, sr_scales = dataset_arrays(sr, levels=6, method="max")
        sr_ds = create_array_dataset(
            data=sr_data,
            scales=sr_scales,
            name="SMLM · reconstruction (10 nm)",
            axes=["y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(sr)],
        )
        world.register(sr_ds, scale={"y": SR_PX, "x": SR_PX})

        print("Uploading localization table…")
        table = create_table_dataset(
            name="SMLM · localizations",
            data=locs,
            description=(
                f"Synthetic dSTORM-style blink events (generator_smlm.py, seed {SEED}): "
                f"{len(locs)} localizations over {FRAMES} frames of a "
                f"{FIELD[0]:.0f}x{FIELD[1]:.0f} µm field."
            ),
            columns=[
                # The two axis columns, in (y, x) order — this order IS the table's space.
                ColumnInput(name="y", axis_type=AxisType.SPACE, unit="micrometer"),
                ColumnInput(name="x", axis_type=AxisType.SPACE, unit="micrometer"),
                ColumnInput(name="frame", role=ColumnRole.ATTRIBUTE, long_name="camera frame index"),
                ColumnInput(name="photons", role=ColumnRole.ATTRIBUTE, long_name="photon count"),
                ColumnInput(
                    name="sigma",
                    role=ColumnRole.ATTRIBUTE,
                    unit="micrometer",
                    long_name="localization precision",
                ),
                # GROUP_ID, not TRACK_ID: the blinks of one emitter are a cluster,
                # not a trajectory — their frames carry no path.
                ColumnInput(name="emitter_id", role=ColumnRole.GROUP_ID, long_name="ground-truth emitter"),
            ],
        )
        # Already in micrometers, so the edge is an identity over (y, x).
        world.register(table)

        print("Composing the scene…")
        scene = create_scene(name="SMLM · synthetic", coordinate_system=world.id)

        # Bottom: the raw movie. The time slider walks t; MIP is what a projection
        # over the *scrubbed* axis would look like elsewhere — here intensity_axis
        # stays null because a TIME axis is not a CHANNEL axis.
        create_layer(
            scene=scene,
            lens=create_lens(raw_ds, slices=[]),
            render_graph=channel_graph(
                colormap=ColorMap.GREY,
                intensity_axis=None,
                mode=ProjectionMode.MIP,
                clim_min=float(BACKGROUND),
                clim_max=float(np.percentile(movie.values, 99.9)),
            ),
            order=0,
        )

        create_intensity_layer(
            lens=create_lens(sr_ds, slices=[]),
            scene=scene,
            colormap=ColorMap.MAGMA,
            clim_min=0.0,
            clim_max=float(np.percentile(sr.values, 99.9)),
            order=1,
            visible=False,  # start on points over raw; the render is one click away
        )

        point_layer = create_point_layer(
            scene=scene,
            table_dataset=table,
            point_size=0.05,  # scene units = µm; 50 nm dots
            colormap=ColorMap.VIRIDIS,
            opacity=0.8,
            order=2,
            color_bys=[
                ColumnColorByInput(
                    table=table.id,
                    column="photons",
                    colormap=ColorMap.VIRIDIS,
                    min=0.0,
                    max=float(np.percentile(locs["photons"], 99.0)),
                    label="Photons",
                ),
                ColumnColorByInput(
                    table=table.id,
                    column="frame",
                    colormap=ColorMap.PLASMA,
                    min=0.0,
                    max=float(FRAMES),
                    label="Appearance time",
                ),
                ColumnColorByInput(
                    table=table.id,
                    column="sigma",
                    colormap=ColorMap.INFERNO,
                    min=0.0,
                    max=float(locs["sigma"].quantile(0.99)),
                    label="Precision",
                ),
            ],
            active_color_by=0,
            filter_bys=[
                LabelFilterByInput(
                    table=table.id, column="photons", min=PHOTON_CUT, label="Bright only"
                )
            ],
        )

        # The point layer's coordinate columns are derived from the table's
        # declaration, never stored — so their coming back named is the round-trip
        # proof that the table's space is what the layer draws from.
        if (point_layer.y_column, point_layer.x_column) != ("y", "x"):
            raise SystemExit(
                f"point layer derived columns ({point_layer.y_column}, {point_layer.x_column}) "
                f"instead of ('y', 'x') — the table declaration did not land"
            )

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  raw movie  : dataset {raw_ds.id} ({FRAMES} frames)")
        print(f"  SR render  : dataset {sr_ds.id} {SR_SHAPE}")
        print(f"  table      : {table.id} ({len(locs)} localizations)")
        print(f"  point layer: {point_layer.id} (colored by photons)")
