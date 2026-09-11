"""A synthetic fMRI session — BOLD, an activation map, and per-region dynamics.

Functional MRI closes the MRI trio: a 4D acquisition whose signal of interest is a
2% wiggle on top of everything else, and whose deliverables are *derived* maps.

- the **BOLD series** ``(t, z, y, x)`` at 3 mm / TR 2 s: a brain ellipsoid with a
  block-design task (30 s on/off) driving two active regions through a canonical
  double-gamma HRF, over baseline, slow drift and noise — drawn as a grey MIP
  underlay whose time slider scrubs the session,
- the **activation z-map**: a voxelwise GLM (constant + drift + HRF regressor) fit
  against the rendered series, as its own volume layer with `clim_min` at the
  significance threshold — thresholding-by-window, since a layer has no z-cutoff
  field,
- the **regions** as a label layer whose picker carries the ROI statistics table
  (peak z, response amplitude) and — the calcium pattern gone volumetric — sparse
  percent-signal-change slices at the block peaks ("response at t = N s"),
- self-checks that re-derive the science: the GLM must light the regions it was
  pointed at (min z in cores ≫ threshold, background quiet) and the recovered HRF
  must peak at the physiological lag.

Conventions as the other MRI generators: (z, y, x) array axes, mm world, seconds.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first.

Run:  python generator_fmri.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import scipy.sparse as sp
import xarray as xr
from scipy.stats import gamma
from sporadik import SparseArray

from mikro_next import Unit, create_space, dataset_arrays
from arkitekt_next import easy
from mikro_next.api.schema import (
    AxisType,
    Blending,
    ColorMap,
    ColumnInput,
    ColumnRole,
    CoordinateAnchorInput,
    DatasetIdentifiesInput,
    PlacementState,
    ProjectionMode,
    SparseAxisInput,
    TableIdentifiesInput,
    ValueRelation,
    create_array_dataset,
    create_label_layer,
    create_layer,
    create_lens,
    create_scene,
    create_sparse_dataset,
    create_table_dataset,
    create_volume_layer,
)
from mikro_next.picker import label_render, measure_color_by, sparse_color_by
from mikro_next.render import channel_graph

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 97
RNG = np.random.default_rng(SEED)

SHAPE = (40, 56, 64)  # (z, y, x), deliberately non-cubic
VOX_MM = 3.0
FRAMES = 150
TR = 2.0  # seconds

BRAIN_RADII = (16.0, 24.0, 27.0)
BLOCK_S = 30.0  # task block length, on and off alike

REGIONS = {  # id -> (name, centre offset from brain centre (z,y,x) vox, radius vox, amplitude %)
    1: ("motor", (6.0, -8.0, -12.0), 4.5, 2.5),
    2: ("visual", (-4.0, 16.0, 8.0), 5.5, 3.0),
}

BASELINE = 800.0
DRIFT_PCT = 1.0
NOISE = 8.0
Z_THRESHOLD = 3.0


# --------------------------------------------------------------------------- #
# The design and the physiology
# --------------------------------------------------------------------------- #
def hrf(t: np.ndarray) -> np.ndarray:
    """The canonical double-gamma HRF (SPM shape): peak ~5 s, undershoot ~15 s."""
    h = gamma.pdf(t, 6) - gamma.pdf(t, 16) / 6.0
    return h / h.max()


def design() -> tuple[np.ndarray, np.ndarray]:
    """The block boxcar and the HRF-convolved regressor, one value per frame."""
    times = np.arange(FRAMES) * TR
    boxcar = ((times % (2 * BLOCK_S)) >= BLOCK_S).astype(np.float64)
    kernel = hrf(np.arange(0, 32, TR))
    regressor = np.convolve(boxcar, kernel)[:FRAMES]
    return boxcar, regressor / regressor.max()


def make_anatomy() -> tuple[np.ndarray, np.ndarray]:
    """Brain mask and region label map (0 background)."""
    zz, yy, xx = np.mgrid[0 : SHAPE[0], 0 : SHAPE[1], 0 : SHAPE[2]].astype(np.float64)
    cz, cy, cx = SHAPE[0] / 2, SHAPE[1] / 2, SHAPE[2] / 2
    brain = (
        ((zz - cz) / BRAIN_RADII[0]) ** 2
        + ((yy - cy) / BRAIN_RADII[1]) ** 2
        + ((xx - cx) / BRAIN_RADII[2]) ** 2
    ) <= 1.0

    labels = np.zeros(SHAPE, dtype=np.int32)
    for region_id, (_name, offset, radius, _amp) in REGIONS.items():
        blob = (
            (zz - (cz + offset[0])) ** 2 + (yy - (cy + offset[1])) ** 2 + (xx - (cx + offset[2])) ** 2
        ) <= radius**2
        labels[blob & brain] = region_id
    return brain, labels


def render_bold(brain, labels, regressor) -> xr.DataArray:
    """The acquisition: baseline + task response + drift + noise, uint16."""
    times = np.arange(FRAMES) * TR
    drift = 1.0 + (DRIFT_PCT / 100.0) * (
        times / times[-1] - 0.5 + 0.3 * np.sin(2 * np.pi * times / 180.0)
    )

    base = np.where(brain, BASELINE * (1.0 + 0.05 * RNG.standard_normal(SHAPE)), 40.0)
    response = np.zeros(SHAPE)
    for region_id, (_n, _o, _r, amplitude) in REGIONS.items():
        response[labels == region_id] = amplitude / 100.0

    series = (
        base[None] * drift[:, None, None, None] * (1.0 + response[None] * regressor[:, None, None, None])
        + RNG.normal(0, NOISE, (FRAMES, *SHAPE))
    )
    return xr.DataArray(np.clip(series, 0, None).astype(np.uint16), dims=("t", "z", "y", "x"), name="bold")


def glm_zmap(bold: np.ndarray, regressor: np.ndarray) -> np.ndarray:
    """Voxelwise t-statistic of the HRF regressor (constant + linear drift + task)."""
    times = np.arange(FRAMES) * TR
    X = np.column_stack([np.ones(FRAMES), times / times[-1], regressor])
    pinv = np.linalg.pinv(X)
    flat = bold.reshape(FRAMES, -1).astype(np.float64)
    betas = pinv @ flat
    residuals = flat - X @ betas
    dof = FRAMES - X.shape[1]
    sigma2 = (residuals**2).sum(axis=0) / dof
    task_var = np.linalg.inv(X.T @ X)[2, 2]
    t_stat = betas[2] / np.sqrt(np.maximum(sigma2 * task_var, 1e-12))
    return t_stat.reshape(SHAPE).astype(np.float32)


# --------------------------------------------------------------------------- #
# Self-checks
# --------------------------------------------------------------------------- #
def check(bold, zmap, labels, brain, boxcar, regressor, headline) -> None:
    if bold.shape != (FRAMES, *SHAPE):
        raise SystemExit(f"BOLD is {bold.shape}, expected {(FRAMES, *SHAPE)} — transposed?")

    # The GLM must find what was planted, and nothing else.
    for region_id, (name, *_rest) in REGIONS.items():
        core = zmap[labels == region_id]
        if not core.min() >= 5.0:
            raise SystemExit(f"{name}: min z {core.min():.1f} < 5 — the response did not survive")
    background = zmap[brain & (labels == 0)]
    quiet = float(np.percentile(background, 99))
    if not quiet <= Z_THRESHOLD:
        raise SystemExit(f"99th percentile background z {quiet:.2f} > {Z_THRESHOLD} — false positives")

    # The physiology: the regressor must lag the boxcar by a hemodynamic delay.
    lags = np.arange(0, 8)
    xc = [np.corrcoef(np.roll(boxcar, lag), regressor)[0, 1] for lag in lags]
    best_lag_s = float(lags[int(np.argmax(xc))] * TR)
    if not 4.0 <= best_lag_s <= 8.0:
        raise SystemExit(f"HRF lag {best_lag_s:.0f} s outside 4-8 s — the convolution is wrong")

    for frame in headline:
        if regressor[frame] < 0.8:
            raise SystemExit(f"headline frame {frame} is not at a response peak")

    print(
        f"  checks pass: regions z ≥ 5, background q99 = {quiet:.2f}, "
        f"HRF lag {best_lag_s:.0f} s, headline frames on-peak"
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Simulating the session ({FRAMES} frames @ TR {TR:.0f} s, {SHAPE} @ {VOX_MM:.0f} mm)…")
    boxcar, regressor = design()
    brain, labels = make_anatomy()
    bold = render_bold(brain, labels, regressor)
    print(f"  BOLD {bold.shape} {bold.dtype} (~{bold.nbytes / 1e6:.0f} MB)")

    print("Fitting the GLM…")
    zmap = glm_zmap(bold.values, regressor)

    # Per-region percent signal change over time (detrended against the off blocks),
    # and the block-peak frames the picker will publish.
    psc = np.zeros((len(REGIONS), FRAMES))
    for row, region_id in enumerate(REGIONS):
        trace = bold.values[:, labels == region_id].mean(axis=1)
        off = trace[boxcar == 0].mean()
        psc[row] = 100.0 * (trace - off) / off
    headline = [int(f) for f in np.argsort(regressor)[-40:][:: 40 // 3][:3]]
    headline = sorted(set(headline))

    check(bold, zmap, labels, brain, boxcar, regressor, headline)

    matrix = SparseArray.from_matrix(sp.csr_matrix(np.where(psc >= 0.3, psc, 0.0).astype(np.float32)))
    print(f"  psc matrix: {matrix.nnz} nnz of {psc.size}")

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy(identifier="neuron-overlay") as app:
        world = create_space(
            "fMRI · head",
            {"t": Unit("second"), "z": Unit("millimeter"), "y": Unit("millimeter"), "x": Unit("millimeter")},
        )

        print("Uploading BOLD…")
        bold_data, bold_scales = dataset_arrays(bold, levels=2, method="max")
        bold_ds = create_array_dataset(
            data=bold_data,
            scales=bold_scales,
            name="fMRI · BOLD",
            axes=["t", "z", "y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(bold)],
        )
        world.register(bold_ds, scale={"t": TR, "z": VOX_MM, "y": VOX_MM, "x": VOX_MM})

        print("Uploading z-map and regions…")
        zmap_ds = create_array_dataset(
            data=xr.DataArray(zmap, dims=("z", "y", "x"), name="zmap"),
            scales=[],
            name="fMRI · activation z-map",
            axes=["z", "y", "x"],
            derived_from=[
                bold_ds.lens().derive(
                    kind="BY_DIMENSION",
                    input_axes=["z", "y", "x"],
                    output_axes=["z", "y", "x"],
                    value_relation=ValueRelation.TRANSFORMED,
                )
            ],
        )
        labels_ds = create_array_dataset(
            data=xr.DataArray(labels, dims=("z", "y", "x")),
            scales=[],
            name="fMRI · regions",
            axes=["z", "y", "x"],
            derived_from=[
                bold_ds.lens().derive(
                    kind="BY_DIMENSION",
                    input_axes=["z", "y", "x"],
                    output_axes=["z", "y", "x"],
                    value_relation=ValueRelation.CATEGORIZED,
                )
            ],
        )

        print("Uploading ROI stats, frame table and psc matrix…")
        stats = pd.DataFrame(
            {
                "region_id": list(REGIONS),
                "name": [name for name, *_ in REGIONS.values()],
                "peak_z": [float(zmap[labels == r].max()) for r in REGIONS],
                "amplitude_pct": [amp for *_, amp in REGIONS.values()],
            }
        )
        table = create_table_dataset(
            name="fMRI · ROI stats",
            data=stats,
            columns=[
                ColumnInput(name="region_id", axis_type=AxisType.INDEX,
                            identified_by=[DatasetIdentifiesInput(dataset=labels_ds.id)]),
                ColumnInput(name="name", role=ColumnRole.LABEL, long_name="region"),
                ColumnInput(name="peak_z", role=ColumnRole.ATTRIBUTE, long_name="peak z"),
                ColumnInput(name="amplitude_pct", role=ColumnRole.ATTRIBUTE, long_name="response amplitude (%)"),
            ],
        )
        frame_table = create_table_dataset(
            name="fMRI · frames",
            data={"frame": np.arange(FRAMES, dtype=np.int64),
                  "time_s": (np.arange(FRAMES) * TR).astype(np.float64),
                  "task_on": (boxcar > 0).astype(np.int64)},
            columns=[
                ColumnInput(name="frame", axis_type=AxisType.INDEX, long_name="frame index"),
                ColumnInput(name="time_s", role=ColumnRole.ATTRIBUTE, long_name="time (s)"),
                ColumnInput(name="task_on", role=ColumnRole.ATTRIBUTE, long_name="task block"),
            ],
        )
        psc_matrix = create_sparse_dataset(
            name="fMRI · percent signal change",
            store=matrix,
            axes=[
                SparseAxisInput(name="region", long_name="region id",
                                identified_by=[DatasetIdentifiesInput(dataset=labels_ds.id, name="regions -> psc")]),
                SparseAxisInput(name="frame", long_name="frame index",
                                identified_by=[TableIdentifiesInput(table=frame_table.id)]),
            ],
            description=f"{len(REGIONS)} regions x {FRAMES} frames, thresholded at 0.3 %",
        )

        print("Composing the scene…")
        scene = create_scene(name="fMRI · block design", coordinate_system=world.id)

        # The anatomy underlay: the BOLD series itself, grey, MIP through z while
        # the time slider walks t (the timelapse-3D pattern).
        create_layer(
            scene=scene,
            lens=create_lens(bold_ds, slices=[]),
            render_graph=channel_graph(
                colormap=ColorMap.GREY,
                intensity_axis=None,
                mode=ProjectionMode.MIP,
                clim_min=0.0,
                clim_max=float(np.percentile(bold.values, 99.5)),
            ),
            order=0,
        )
        # The activation overlay: thresholded by its contrast window — clim_min at
        # the significance cutoff is what a layer has instead of a z threshold.
        create_volume_layer(
            lens=zmap_ds.lens(),
            scene=scene.id,
            mode=ProjectionMode.MIP,
            colormap=ColorMap.INFERNO,
            clim_min=Z_THRESHOLD,
            clim_max=float(zmap.max()),
            blending=Blending.ADDITIVE,
            opacity=0.9,
            order=1,
        )
        label_layer = create_label_layer(
            lens=labels_ds.lens().id,
            scene=scene.id,
            render=label_render(
                [
                    measure_color_by(table, "peak_z", colormap=ColorMap.INFERNO, min=0.0,
                                     max=float(stats["peak_z"].max()), label="Peak z"),
                    measure_color_by(table, "amplitude_pct", colormap=ColorMap.VIRIDIS, min=0.0,
                                     max=float(stats["amplitude_pct"].max()), label="Amplitude"),
                    *(
                        sparse_color_by(psc_matrix, {"frame": frame}, colormap=ColorMap.MAGMA,
                                        min=0.0, max=float(psc.max()),
                                        label=f"Response at {frame * TR:.0f} s")
                        for frame in headline
                    ),
                ],
                active=0,
                background=0,
            ),
            opacity=0.5,
            order=2,
        )
        if label_layer.placement != PlacementState.PLACED:
            raise SystemExit(f"regions did not reach the world: {label_layer.placement}")
        published = label_layer.label_render.color_bys if label_layer.label_render else ()
        if len(published) != 2 + len(headline):
            raise SystemExit(f"label layer offers {len(published)} colourings, expected {2 + len(headline)}")

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  BOLD {bold_ds.id} ({FRAMES} frames), z-map {zmap_ds.id}, regions {labels_ds.id}")
        print(f"  ROI table {table.id}, psc sparse {psc_matrix.id} "
              f"(picker at t = {', '.join(f'{f * TR:.0f}' for f in headline)} s)")
