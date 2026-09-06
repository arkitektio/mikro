"""A synthetic calcium-imaging session — functional activity over a segmentation.

The functional-imaging shape no generator covers: a movie in which the *interesting*
signal is per-object over time, not per-pixel over space.

- the **movie** ``(t, y, x)``: ~40 somata whose brightness follows per-cell calcium
  transients (fast rise, ~0.6 s decay) over 600 frames at 20 Hz,
- the **cell masks** as a label dataset + label layer over the movie,
- a **per-cell stats table** (event rate, peak ΔF/F, ensemble membership) keyed to
  the mask by a Dataset identification — the colourings the label picker offers,
- the **ΔF/F matrix** as a sparse dataset (cell x frame, thresholded — calcium IS
  sparse in time), whose `cell` axis is identified by the mask and whose `frame`
  axis by a small frame table. Its picker entries are ``sparse_color_by`` slices at
  event-rich frames: **"activity at t = N s" as a colouring**, the first sparse
  ``at`` used as time anywhere (sparse axes are INDEX by design, so time is a frame
  index — the frame table is what maps it back to seconds).

Cells belong to three ensembles that share event times, so the colourings mean
something: an ensemble lights up *together* at its frames, and the categorical
ensemble colouring matches the pattern the sparse slices show.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first.

Run:  python generator_calcium.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import scipy.sparse as sp
import xarray as xr
from sporadik import SparseArray

from mikro_next import Unit, create_space, dataset_arrays
from arkitekt_next import easy
from mikro_next.api.schema import (
    AxisType,
    ColorMap,
    ColumnInput,
    ColumnRole,
    CoordinateAnchorInput,
    DatasetIdentifiesInput,
    ProjectionMode,
    SparseAxisInput,
    TableIdentifiesInput,
    create_array_dataset,
    create_label_layer,
    create_layer,
    create_lens,
    create_scene,
    create_sparse_dataset,
    create_table_dataset,
)
from mikro_next.picker import (
    categorical_color_by,
    label_render,
    measure_color_by,
    sparse_color_by,
)
from mikro_next.render import channel_graph

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 59
RNG = np.random.default_rng(SEED)

FIELD_SHAPE = (130, 190)  # (y, x) px, deliberately non-square
PIXEL_UM = 0.4

FRAMES = 600
RATE_HZ = 20.0
DT = 1.0 / RATE_HZ  # 30 s session

N_CELLS = 40
SOMA_RADIUS_PX = (4.0, 6.5)
ENSEMBLES = ("A", "B", "C")

ENSEMBLE_EVENT_RATE = 0.08  # shared events per second, per ensemble
SOLO_EVENT_RATE = 0.02  # private events per second, per cell
PARTICIPATION = 0.85  # chance a member joins its ensemble's event
DECAY_S = 0.6  # calcium indicator decay
AMPLITUDE = 1.0  # mean ΔF/F of one transient

BASELINE = 400.0  # counts of a resting soma pixel at its centre
BACKGROUND = 80.0
DFF_FLOOR = 0.05  # below this the matrix stores nothing — calcium is sparse in time
HEADLINE_FRAMES = 3  # sparse "activity at t" picker entries to publish


# --------------------------------------------------------------------------- #
# Ground truth: somata, ensembles, transients
# --------------------------------------------------------------------------- #
def place_cells() -> tuple[np.ndarray, list[dict]]:
    """The label mask (ids 1..N, 0 background) and per-cell facts.

    Somata are disks placed with rejection sampling so masks never touch; row i of
    every matrix below is cell id i+1 — the same off-by-one the Visium generator
    carries, because id 0 is the background."""
    yy, xx = np.mgrid[0 : FIELD_SHAPE[0], 0 : FIELD_SHAPE[1]]
    mask = np.zeros(FIELD_SHAPE, dtype=np.int32)
    weight = np.zeros(FIELD_SHAPE, dtype=np.float64)  # soma profile, for rendering
    cells = []

    while len(cells) < N_CELLS:
        r = RNG.uniform(*SOMA_RADIUS_PX)
        cy = RNG.uniform(r + 2, FIELD_SHAPE[0] - r - 2)
        cx = RNG.uniform(r + 2, FIELD_SHAPE[1] - r - 2)
        if any((cy - c["cy"]) ** 2 + (cx - c["cx"]) ** 2 < (r + c["r"] + 3) ** 2 for c in cells):
            continue
        cell_id = len(cells) + 1
        dist2 = (yy - cy) ** 2 + (xx - cx) ** 2
        disk = dist2 <= r**2
        mask[disk] = cell_id
        weight[disk] = np.exp(-dist2[disk] / (2 * (r / 1.6) ** 2))
        cells.append(
            {
                "cell_id": cell_id,
                "cy": cy,
                "cx": cx,
                "r": r,
                "ensemble": ENSEMBLES[(cell_id - 1) % len(ENSEMBLES)],
            }
        )
    return mask, cells, weight


def transients(cells: list[dict]) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Per-cell ΔF/F over time — ``(n_cells, frames)`` — from ensemble + solo spikes.

    Each ensemble draws shared event frames; each member joins one with probability
    PARTICIPATION and a jitter of a frame or two. Every spike is a kernel with an
    instant rise and an exponential decay."""
    kernel_len = int(6 * DECAY_S / DT)
    kernel = np.exp(-np.arange(kernel_len) * DT / DECAY_S)

    ensemble_frames = {
        name: np.nonzero(RNG.random(FRAMES) < ENSEMBLE_EVENT_RATE * DT)[0]
        for name in ENSEMBLES
    }

    dff = np.zeros((len(cells), FRAMES))
    for i, cell in enumerate(cells):
        spikes = np.zeros(FRAMES)
        for frame in ensemble_frames[cell["ensemble"]]:
            if RNG.random() < PARTICIPATION:
                jittered = frame + int(RNG.integers(-1, 2))
                if 0 <= jittered < FRAMES:
                    spikes[jittered] += RNG.lognormal(np.log(AMPLITUDE), 0.3)
        solo = np.nonzero(RNG.random(FRAMES) < SOLO_EVENT_RATE * DT)[0]
        for frame in solo:
            spikes[frame] += RNG.lognormal(np.log(AMPLITUDE), 0.3)
        if not spikes.any():
            # A silent cell has a constant trace, whose correlation with anything is
            # NaN — which slides through a `< threshold` check unnoticed. One
            # guaranteed event keeps every check well-defined.
            spikes[RNG.integers(0, FRAMES)] = RNG.lognormal(np.log(AMPLITUDE), 0.3)
        dff[i] = np.convolve(spikes, kernel)[:FRAMES]
    return dff, ensemble_frames


def render_movie(mask: np.ndarray, weight: np.ndarray, dff: np.ndarray) -> xr.DataArray:
    """The camera's view: baseline somata breathing with their ΔF/F, plus noise."""
    resting = BACKGROUND + BASELINE * weight
    movie = np.empty((FRAMES, *FIELD_SHAPE), dtype=np.uint16)
    gain = np.zeros(FIELD_SHAPE)
    for frame in range(FRAMES):
        gain[:] = 0.0
        inside = mask > 0
        gain[inside] = dff[mask[inside] - 1, frame]
        expected = resting * (1.0 + gain * (mask > 0))
        movie[frame] = RNG.poisson(expected).astype(np.uint16)
    return xr.DataArray(movie, dims=("t", "y", "x"), name="calcium")


# --------------------------------------------------------------------------- #
# Self-checks
# --------------------------------------------------------------------------- #
def check(
    mask: np.ndarray,
    cells: list[dict],
    dff: np.ndarray,
    movie: xr.DataArray,
    headline: list[int],
) -> None:
    if movie.shape != (FRAMES, *FIELD_SHAPE):
        raise SystemExit(f"movie is {movie.shape}, expected {(FRAMES, *FIELD_SHAPE)} — transposed?")
    if len(cells) != N_CELLS or mask.max() != N_CELLS:
        raise SystemExit(f"{len(cells)} cells, mask max {mask.max()} — expected {N_CELLS}")

    # The movie must carry the activity: a trace extracted the way an analysis
    # pipeline would (mean over the mask, ΔF/F against its own quiet baseline) has
    # to recover the ground truth per cell.
    frames = movie.values.astype(np.float64)
    for i, cell in enumerate(cells):
        sel = mask == cell["cell_id"]
        trace = frames[:, sel].mean(axis=1)
        f0 = np.percentile(trace, 20)
        est = (trace - f0) / (f0 - BACKGROUND * sel.mean() / max(sel.mean(), 1e-9))
        corr = float(np.corrcoef(est, dff[i])[0, 1])
        # `not >=` rather than `<`: a NaN correlation must fail, not slip through.
        if not corr >= 0.9:
            raise SystemExit(f"cell {cell['cell_id']}: extracted trace correlates {corr:.3f} < 0.9")

    # Ensembles must be real: within-ensemble correlation clearly above cross.
    corr = np.corrcoef(dff)
    same, cross = [], []
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            (same if cells[i]["ensemble"] == cells[j]["ensemble"] else cross).append(corr[i, j])
    gap = float(np.mean(same) - np.mean(cross))
    if not gap >= 0.25:  # `not >=`: a NaN gap must fail, not slip through
        raise SystemExit(f"ensemble correlation gap {gap:.3f} < 0.25 — ensembles not visible")

    for frame in headline:
        active = int((dff[:, frame] > 0.3).sum())
        if active < len(cells) // len(ENSEMBLES) // 2:
            raise SystemExit(f"headline frame {frame} has only {active} active cells")

    print(
        f"  checks pass: {N_CELLS} disjoint cells, traces recover ΔF/F (r>0.9), "
        f"ensemble gap {gap:.2f}, headline frames busy"
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Placing {N_CELLS} cells in {len(ENSEMBLES)} ensembles…")
    mask, cells, weight = place_cells()
    dff, ensemble_frames = transients(cells)

    # The frames the picker will publish: the busiest ensemble events, one per
    # ensemble, spread over the session.
    headline = sorted(
        int(frames_[np.argmax(dff[:, frames_].sum(axis=0))])
        for name, frames_ in ensemble_frames.items()
        if len(frames_)
    )[:HEADLINE_FRAMES]

    print(f"Rendering {FRAMES} frames at {RATE_HZ:.0f} Hz…")
    movie = render_movie(mask, weight, dff)
    print(f"  movie {movie.shape} {movie.dtype} (~{movie.nbytes / 1e6:.0f} MB)")

    check(mask, cells, dff, movie, headline)

    # The ΔF/F matrix, thresholded to its events — the honest sparse shape.
    thresholded = np.where(dff >= DFF_FLOOR, dff, 0.0).astype(np.float32)
    matrix = SparseArray.from_matrix(sp.csr_matrix(thresholded))
    density = matrix.nnz / (N_CELLS * FRAMES)
    print(f"  ΔF/F matrix: {matrix.nnz:,} nonzero ({100 * density:.1f} % dense)")
    if density > 0.5:
        raise SystemExit("ΔF/F matrix is over half dense — thresholding is not thresholding")

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy(identifier="neuron-overlay") as app:
        world = create_space(
            "Calcium · field",
            {"t": Unit("second"), "y": Unit("micrometer"), "x": Unit("micrometer")},
        )

        print("Uploading movie…")
        movie_data, movie_scales = dataset_arrays(movie, levels=3, method="max")
        movie_ds = create_array_dataset(
            data=movie_data,
            scales=movie_scales,
            name="Calcium · movie",
            axes=["t", "y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(movie)],
        )
        world.register(movie_ds, scale={"t": DT, "y": PIXEL_UM, "x": PIXEL_UM})

        print("Uploading cell masks…")
        labels_ds = create_array_dataset(
            data=xr.DataArray(mask, dims=("y", "x")),
            # No pyramid: the average of two cell ids is a third cell's id.
            scales=[],
            name="Calcium · cells",
            axes=["y", "x"],
        )
        world.register(labels_ds, scale={"y": PIXEL_UM, "x": PIXEL_UM})

        print("Uploading per-cell stats…")
        stats = create_table_dataset(
            name="Calcium · per-cell stats",
            data=pd.DataFrame(
                {
                    "cell_id": np.array([c["cell_id"] for c in cells], dtype=np.int64),
                    "event_rate": (dff > 0.3).sum(axis=1) / (FRAMES * DT),
                    "peak_dff": dff.max(axis=1),
                    "ensemble": [c["ensemble"] for c in cells],
                }
            ),
            columns=[
                # The identification is what lets the label layer's picker read the
                # data columns: a mask id is a row of this table.
                ColumnInput(
                    name="cell_id",
                    axis_type=AxisType.INDEX,
                    identified_by=[DatasetIdentifiesInput(dataset=labels_ds.id)],
                ),
                ColumnInput(name="event_rate", role=ColumnRole.ATTRIBUTE, long_name="events per second"),
                ColumnInput(name="peak_dff", role=ColumnRole.ATTRIBUTE, long_name="peak ΔF/F"),
                ColumnInput(name="ensemble", role=ColumnRole.LABEL, long_name="ensemble"),
            ],
        )

        print("Uploading frame table + ΔF/F matrix…")
        frame_table = create_table_dataset(
            name="Calcium · frames",
            data={
                "frame": np.arange(FRAMES, dtype=np.int64),
                "time_s": (np.arange(FRAMES) * DT).astype(np.float64),
            },
            columns=[
                ColumnInput(name="frame", axis_type=AxisType.INDEX, long_name="frame index"),
                ColumnInput(name="time_s", role=ColumnRole.ATTRIBUTE, long_name="time (s)"),
            ],
        )
        expression = create_sparse_dataset(
            name="Calcium · ΔF/F",
            store=matrix,
            axes=[
                SparseAxisInput(
                    name="cell",
                    long_name="cell id",
                    identified_by=[DatasetIdentifiesInput(dataset=labels_ds.id, name="cells -> ΔF/F")],
                ),
                SparseAxisInput(
                    name="frame",
                    long_name="frame index",
                    identified_by=[TableIdentifiesInput(table=frame_table.id)],
                ),
            ],
            description=f"{N_CELLS} cells x {FRAMES} frames, ΔF/F thresholded at {DFF_FLOOR}",
        )

        print("Composing the scene…")
        scene = create_scene(name="Calcium · synthetic", coordinate_system=world.id)

        create_layer(
            scene=scene,
            lens=create_lens(movie_ds, slices=[]),
            render_graph=channel_graph(
                colormap=ColorMap.GREY,
                intensity_axis=None,
                mode=ProjectionMode.MIP,
                clim_min=float(BACKGROUND),
                clim_max=float(np.percentile(movie.values, 99.9)),
            ),
            order=0,
        )

        # The label layer carries the whole functional picker: static per-cell
        # measures from the stats table, the categorical ensembles, and — the first
        # time anywhere — sparse slices whose position axis is *time*.
        label_layer = create_label_layer(
            lens=labels_ds.lens().id,
            scene=scene.id,
            render=label_render(
                [
                    measure_color_by(stats, "event_rate", colormap=ColorMap.VIRIDIS, min=0.0,
                                     max=float((dff > 0.3).sum(axis=1).max() / (FRAMES * DT)),
                                     label="Event rate"),
                    measure_color_by(stats, "peak_dff", colormap=ColorMap.INFERNO, min=0.0,
                                     max=float(dff.max()), label="Peak ΔF/F"),
                    categorical_color_by(stats, "ensemble", label="Ensemble"),
                    *(
                        sparse_color_by(expression, {"frame": frame}, colormap=ColorMap.MAGMA,
                                        min=0.0, max=float(dff.max()),
                                        label=f"ΔF/F at {frame * DT:.1f} s")
                        for frame in headline
                    ),
                ],
                active=0,
                background=0,
            ),
            opacity=0.65,
            order=1,
        )

        published = label_layer.label_render.color_bys if label_layer.label_render else ()
        expected = 3 + len(headline)
        if len(published) != expected:
            raise SystemExit(f"label layer offers {len(published)} colourings, expected {expected}")

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  movie   : dataset {movie_ds.id} ({FRAMES} frames @ {RATE_HZ:.0f} Hz)")
        print(f"  cells   : dataset {labels_ds.id} ({N_CELLS} masks), stats table {stats.id}")
        print(f"  ΔF/F    : sparse {expression.id} ({matrix.nnz:,} nnz), frames table {frame_table.id}")
        print(f"  pickers : {len(published)} colourings on layer {label_layer.id} "
              f"(sparse at t = {', '.join(f'{f * DT:.1f}' for f in headline)} s)")
