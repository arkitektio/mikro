"""A synthetic structural MRI — one head, three contrasts, one segmentation.

The multi-contrast shape every radiology viewer starts from: T1, T2 and FLAIR of
the SAME anatomy as three positions of a CHANNEL axis, so one calibrated dataset
carries the whole exam and the scene bootstrap peels it into one MIP layer per
contrast. Over it, the tissue segmentation as a label layer whose picker offers
the per-tissue relaxometry the phantom was built from.

The phantom: nested ellipsoids — WM interior, cortical GM shell, a CSF rim, two
ventricles — with a smooth multiplicative bias field and noise, and contrast
lookups that encode the actual physics ordering (T1: WM > GM > CSF; T2 reversed;
FLAIR = T2 with CSF suppressed). The self-checks recover exactly those orderings
from the rendered volumes, so a broken lookup or a transposed tissue map cannot
upload.

MRI conventions follow converter_nifti_dataset.py: array axes (z, y, x), world in
millimeters, non-cubic volume.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first.

Run:  python generator_mri_multicontrast.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import gaussian_filter

from mikro import Calibration, Unit, dataset_arrays
from arkitekt_next import easy
from mikro.api.schema import (
    AxisType,
    BootstrapLayerKind,
    ColorMap,
    ColumnInput,
    ColumnRole,
    CoordinateAnchorInput,
    DatasetIdentifiesInput,
    PlacementState,
    ScenePolicyInput,
    ValueRelation,
    create_array_dataset,
    create_label_layer,
    create_table_dataset,
)
from mikro.picker import categorical_color_by, label_render, measure_color_by
from mikro.rath import current_mikro_rath

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 89
RNG = np.random.default_rng(SEED)

SHAPE = (96, 128, 112)  # (z, y, x), deliberately non-cubic
VOX_MM = 1.5

BRAIN_RADII = (38.0, 54.0, 46.0)
CSF_RIM = 1.10  # outer CSF as a fraction of the brain ellipsoid
GM_SHELL = 0.78  # inside this normalized radius is WM

TISSUES = {1: "CSF", 2: "GM", 3: "WM"}
CONTRASTS = ("T1", "T2", "FLAIR")
# The physics, as lookups (uint16-ish means): the orderings below ARE the checks.
LOOKUP = {
    "T1": {0: 30, 1: 250, 2: 700, 3: 1000},
    "T2": {0: 30, 1: 1000, 2: 500, 3: 350},
    "FLAIR": {0: 30, 1: 80, 2: 550, 3: 400},
}
BIAS = 0.15
NOISE = 25.0
LEVELS = 3


# --------------------------------------------------------------------------- #
# The phantom
# --------------------------------------------------------------------------- #
def tissue_map() -> np.ndarray:
    """Per-voxel tissue id: 0 background, 1 CSF, 2 GM, 3 WM."""
    zz, yy, xx = np.mgrid[0 : SHAPE[0], 0 : SHAPE[1], 0 : SHAPE[2]].astype(np.float64)
    cz, cy, cx = SHAPE[0] / 2, SHAPE[1] / 2, SHAPE[2] / 2
    r = np.sqrt(
        ((zz - cz) / BRAIN_RADII[0]) ** 2
        + ((yy - cy) / BRAIN_RADII[1]) ** 2
        + ((xx - cx) / BRAIN_RADII[2]) ** 2
    )

    tissues = np.zeros(SHAPE, dtype=np.int32)
    tissues[r < CSF_RIM] = 1  # outer CSF
    tissues[r < 1.0] = 2  # cortical GM shell
    tissues[r < GM_SHELL] = 3  # WM interior

    # Two ventricles, CSF pockets inside the WM.
    for side in (-1.0, 1.0):
        vent = (
            ((zz - cz) / 9.0) ** 2
            + ((yy - (cy - 4)) / 22.0) ** 2
            + ((xx - (cx + side * 9)) / 6.0) ** 2
        ) <= 1.0
        tissues[vent] = 1
    return tissues


def render_exam(tissues: np.ndarray) -> xr.DataArray:
    """The three contrasts as ``(c, z, y, x)`` uint16, one shared bias field."""
    bias = 1.0 + BIAS * gaussian_filter(RNG.standard_normal(SHAPE), 18.0) / 0.02
    bias = np.clip(bias / bias.mean(), 0.7, 1.3)

    volumes = []
    for contrast in CONTRASTS:
        lookup = np.array([LOOKUP[contrast][t] for t in range(4)], dtype=np.float64)
        clean = lookup[tissues] * bias
        noisy = np.sqrt(
            (clean + RNG.normal(0, NOISE, SHAPE)) ** 2 + RNG.normal(0, NOISE, SHAPE) ** 2
        )  # Rician-ish, the way magnitude MRI noise actually behaves
        volumes.append(noisy)
    return xr.DataArray(
        np.stack(volumes).astype(np.uint16), dims=("c", "z", "y", "x"), name="exam"
    )


# --------------------------------------------------------------------------- #
# Self-checks
# --------------------------------------------------------------------------- #
def check(tissues: np.ndarray, exam: xr.DataArray, stats: pd.DataFrame) -> None:
    if exam.shape != (len(CONTRASTS), *SHAPE):
        raise SystemExit(f"exam is {exam.shape}, expected {(len(CONTRASTS), *SHAPE)} — transposed?")

    by_name = stats.set_index("name")
    # The physics orderings, recovered from the RENDERED volumes (via the stats
    # frame, which is measured off them): a broken lookup or a transposed tissue
    # map cannot pass this.
    if not (by_name.loc["WM", "mean_t1"] > by_name.loc["GM", "mean_t1"] > by_name.loc["CSF", "mean_t1"]):
        raise SystemExit("T1 ordering WM > GM > CSF does not hold")
    if not (by_name.loc["CSF", "mean_t2"] > by_name.loc["GM", "mean_t2"] > by_name.loc["WM", "mean_t2"]):
        raise SystemExit("T2 ordering CSF > GM > WM does not hold")
    if not (by_name.loc["CSF", "mean_flair"] < 0.4 * by_name.loc["WM", "mean_flair"]):
        raise SystemExit("FLAIR does not suppress CSF")

    for tissue_id, name in TISSUES.items():
        if int((tissues == tissue_id).sum()) != int(by_name.loc[name, "voxels"]):
            raise SystemExit(f"{name}: stats row disagrees with the tissue map")
    if not (tissues == 1).sum() > 2 * 3.14 * 9 * 22 * 6 / 6:  # ventricles exist
        raise SystemExit("ventricles missing from the CSF class")

    print(
        "  checks pass: T1/T2 orderings hold, FLAIR suppresses CSF "
        f"({by_name.loc['CSF', 'mean_flair']:.0f} vs WM {by_name.loc['WM', 'mean_flair']:.0f}), "
        "stats match the map"
    )


LAYERS_QUERY = """
query Layers($id: ID!) { scene(id: $id) { layers { __typename placement } } }
"""


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Building the head phantom ({SHAPE} @ {VOX_MM} mm)…")
    tissues = tissue_map()
    exam = render_exam(tissues)
    print(f"  exam {exam.shape} {exam.dtype} (~{exam.nbytes / 1e6:.0f} MB)")

    # Per-tissue relaxometry, measured off the rendered volumes.
    stats = pd.DataFrame(
        {
            "tissue_id": list(TISSUES),
            "name": list(TISSUES.values()),
            "voxels": [int((tissues == t).sum()) for t in TISSUES],
            "volume_mm3": [float((tissues == t).sum() * VOX_MM**3) for t in TISSUES],
            "mean_t1": [float(exam.values[0][tissues == t].mean()) for t in TISSUES],
            "mean_t2": [float(exam.values[1][tissues == t].mean()) for t in TISSUES],
            "mean_flair": [float(exam.values[2][tissues == t].mean()) for t in TISSUES],
        }
    )
    check(tissues, exam, stats)

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy(identifier="neuron-overlay") as app:
        print("Uploading the exam…")
        data, scales = dataset_arrays(exam, levels=LEVELS, method="mean")
        source = create_array_dataset(
            data=data,
            scales=scales,
            name="MRI · T1/T2/FLAIR exam",
            axes=["c", "z", "y", "x"],
            anchors=CoordinateAnchorInput.histogram_anchors(exam),  # already a list: one per channel
        )
        physical = source.calibrate(
            {
                "c": Calibration(1.0, Unit("dimensionless")),
                "z": Calibration(VOX_MM, Unit("millimeter")),
                "y": Calibration(VOX_MM, Unit("millimeter")),
                "x": Calibration(VOX_MM, Unit("millimeter")),
            },
            name="MRI · scanner",
        )

        print("Staging the scene (one MIP layer per contrast)…")
        scene = physical.stage(
            name="MRI · multicontrast",
            policy=ScenePolicyInput(kind=BootstrapLayerKind.VOLUME),
        )

        print("Uploading the segmentation…")
        labels_ds = create_array_dataset(
            data=xr.DataArray(tissues, dims=("z", "y", "x")),
            scales=[],  # the average of two tissue ids is a third tissue
            name="MRI · tissue segmentation",
            axes=["z", "y", "x"],
            # The rank-4 -> rank-3 hop: BY_DIMENSION naming the three shared axes.
            derived_from=[
                source.lens().derive(
                    kind="BY_DIMENSION",
                    input_axes=["z", "y", "x"],
                    output_axes=["z", "y", "x"],
                    value_relation=ValueRelation.CATEGORIZED,
                )
            ],
        )

        print("Uploading per-tissue stats…")
        table = create_table_dataset(
            name="MRI · tissue stats",
            data=stats,
            columns=[
                ColumnInput(
                    name="tissue_id",
                    axis_type=AxisType.INDEX,
                    identified_by=[DatasetIdentifiesInput(dataset=labels_ds.id)],
                ),
                ColumnInput(name="name", role=ColumnRole.LABEL, long_name="tissue"),
                ColumnInput(name="voxels", role=ColumnRole.ATTRIBUTE),
                ColumnInput(name="volume_mm3", role=ColumnRole.ATTRIBUTE, long_name="volume (mm³)"),
                ColumnInput(name="mean_t1", role=ColumnRole.ATTRIBUTE, long_name="mean T1 signal"),
                ColumnInput(name="mean_t2", role=ColumnRole.ATTRIBUTE, long_name="mean T2 signal"),
                ColumnInput(name="mean_flair", role=ColumnRole.ATTRIBUTE, long_name="mean FLAIR signal"),
            ],
        )

        label_layer = create_label_layer(
            lens=labels_ds.lens().id,
            scene=scene.id,
            render=label_render(
                [
                    categorical_color_by(table, "name", label="Tissue"),
                    measure_color_by(table, "mean_t1", colormap=ColorMap.VIRIDIS, min=0.0,
                                     max=float(stats["mean_t1"].max()), label="Mean T1"),
                    measure_color_by(table, "mean_t2", colormap=ColorMap.INFERNO, min=0.0,
                                     max=float(stats["mean_t2"].max()), label="Mean T2"),
                    measure_color_by(table, "volume_mm3", colormap=ColorMap.PLASMA, min=0.0,
                                     max=float(stats["volume_mm3"].max()), label="Volume"),
                ],
                active=0,
                background=0,
            ),
            opacity=0.45,
            order=len(CONTRASTS),
        )
        if label_layer.placement != PlacementState.PLACED:
            raise SystemExit(f"segmentation did not reach the world: {label_layer.placement}")

        result = current_mikro_rath.get().query(LAYERS_QUERY, {"id": scene.id})
        layers = result.data["scene"]["layers"]
        kinds = sorted(layer["__typename"] for layer in layers)
        if kinds != ["IntensityLayer"] * len(CONTRASTS) + ["LabelLayer"]:
            raise SystemExit(f"scene holds {kinds} — expected one MIP per contrast + labels")
        if any(layer["placement"] != "PLACED" for layer in layers):
            raise SystemExit(f"unplaced layers: {layers}")

        published = label_layer.label_render.color_bys if label_layer.label_render else ()
        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  exam {source.id} ({len(CONTRASTS)} contrasts), segmentation {labels_ds.id}")
        print(f"  stats table {table.id}, label layer {label_layer.id} ({len(published)} colourings)")
