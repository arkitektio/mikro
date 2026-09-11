"""A synthetic high-content-screening plate — many fields, one world, a dose curve.

The multi-position shape no generator covers, and the first working consumer of
``world.grid_cell(...)`` — the only prior callers (debug_scenes.py) use the removed
``scene.grid_cell`` and raise. A plate is the case the grid API exists for: one
field per well, laid out in reading order on a shared physical stage.

- **24 fields** (4 rows x 6 columns, A1..D6), each a small nuclei image; a dose
  gradient across the columns drives the biology — cell count and staining
  intensity fall with dose,
- each field is its own dataset, placed by ONE ``world.grid_cell(field, index,
  cols, pitch, scale=...)`` call — the pixel size and the well position live
  together on that one edge,
- a **per-well table** whose SPACE columns are the well-centre world coordinates:
  drawn as a point layer over the plate, coloured by cell count — the plate
  heat-map every screening tool shows, here as an ordinary table over the same
  world the fields sit in.

Fields are deliberately non-square so a y/x transpose breaks the grid visibly and
the checks loudly.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first.

Run:  python generator_hcs_plate.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import xarray as xr
from scipy import ndimage

from mikro import Unit, space_2d
from arkitekt_next import easy
from mikro.api.schema import (
    AxisType,
    ColorMap,
    ColumnColorByInput,
    ColumnInput,
    ColumnRole,
    CoordinateAnchorInput,
    create_array_dataset,
    create_intensity_layer,
    create_point_layer,
    create_scene,
    create_table_dataset,
)

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 67
RNG = np.random.default_rng(SEED)

ROWS, COLS = 4, 6
ROW_NAMES = "ABCD"

FIELD_SHAPE = (192, 256)  # (y, x) px per field, deliberately non-square
PIXEL_UM = 0.65
FIELD_UM = (FIELD_SHAPE[0] * PIXEL_UM, FIELD_SHAPE[1] * PIXEL_UM)  # (124.8, 166.4)

# Centre-to-centre spacing. One number for both directions — that is grid_cell's
# contract — so it must clear the larger field extent.
PITCH_UM = 200.0

# The screen: dose doubles per column, and the response is a clean exponential
# decline in both cell count and staining brightness.
BASE_CELLS = 60
COUNT_DECAY = 0.35  # per dose step
BRIGHT_DECAY = 0.15

NUCLEUS_R_PX = (4.0, 7.0)
BASE_AMPLITUDE = 2500.0
BACKGROUND = 120.0


# --------------------------------------------------------------------------- #
# One well
# --------------------------------------------------------------------------- #
def well_name(row: int, col: int) -> str:
    return f"{ROW_NAMES[row]}{col + 1}"


def render_well(col: int) -> tuple[xr.DataArray, int, float]:
    """One field of stained nuclei under this column's dose.

    Returns the image, the number of nuclei placed, and their mean amplitude —
    the ground truth the table and the checks are built from. Nuclei are placed
    non-overlapping so a connected-component count equals the placed count."""
    n_cells = int(RNG.poisson(BASE_CELLS * np.exp(-COUNT_DECAY * col)))
    amplitude = BASE_AMPLITUDE * np.exp(-BRIGHT_DECAY * col)

    yy, xx = np.mgrid[0 : FIELD_SHAPE[0], 0 : FIELD_SHAPE[1]].astype(np.float64)
    image = np.zeros(FIELD_SHAPE)
    placed: list[tuple[float, float, float]] = []
    attempts = 0
    while len(placed) < n_cells and attempts < n_cells * 60:
        attempts += 1
        r = RNG.uniform(*NUCLEUS_R_PX)
        cy = RNG.uniform(r + 2, FIELD_SHAPE[0] - r - 2)
        cx = RNG.uniform(r + 2, FIELD_SHAPE[1] - r - 2)
        if any((cy - py) ** 2 + (cx - px) ** 2 < (r + pr + 4) ** 2 for py, px, pr in placed):
            continue
        placed.append((cy, cx, r))
        image += amplitude * RNG.uniform(0.7, 1.3) * np.exp(
            -(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * (r / 1.8) ** 2))
        )

    noisy = RNG.poisson(image + BACKGROUND).astype(np.uint16)
    return (
        xr.DataArray(noisy, dims=("y", "x"), name="nuclei"),
        len(placed),
        float(amplitude),
    )


# --------------------------------------------------------------------------- #
# Self-checks
# --------------------------------------------------------------------------- #
def check(wells: list[dict]) -> None:
    if len(wells) != ROWS * COLS:
        raise SystemExit(f"{len(wells)} wells, expected {ROWS * COLS}")

    # The image must carry the biology: a connected-component count over a simple
    # threshold has to equal the number of nuclei placed, per well.
    for well in wells:
        if well["image"].shape != FIELD_SHAPE:
            raise SystemExit(f"{well['well']}: field {well['image'].shape} != {FIELD_SHAPE} — transposed?")
        # Thresholded against the well's own staining level, not a global constant:
        # neighbouring Gaussian tails sum to ~0.25 of the amplitude, so a global
        # threshold either merges bright wells or misses dim ones.
        binary = well["image"].values > BACKGROUND + 0.35 * well["mean_amplitude"]
        _, measured = ndimage.label(binary)
        if measured != well["cell_count"]:
            raise SystemExit(
                f"{well['well']}: {measured} segmented vs {well['cell_count']} placed nuclei"
            )

    # The dose-response must be recoverable: counts against dose strongly negative.
    counts = np.array([w["cell_count"] for w in wells], dtype=np.float64)
    doses = np.array([w["dose_step"] for w in wells], dtype=np.float64)
    corr = float(np.corrcoef(doses, counts)[0, 1])
    if not corr <= -0.8:
        raise SystemExit(f"dose/count correlation {corr:.2f} > -0.8 — the screen shows nothing")

    # The grid math the table's coordinates are built from: reading order.
    for index, well in enumerate(wells):
        row, col = divmod(index, COLS)
        if (well["row"], well["col"]) != (row, col):
            raise SystemExit(f"well {index} is ({well['row']}, {well['col']}), expected ({row}, {col})")

    print(
        f"  checks pass: {len(wells)} wells, segmentation matches placement, "
        f"dose/count r = {corr:.2f}"
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Rendering the plate ({ROWS}x{COLS} wells, dose gradient across columns)…")
    wells: list[dict] = []
    for index in range(ROWS * COLS):
        row, col = divmod(index, COLS)
        image, count, amplitude = render_well(col)
        wells.append(
            {
                "index": index,
                "row": row,
                "col": col,
                "well": well_name(row, col),
                "dose_step": col,
                "image": image,
                "cell_count": count,
                "mean_amplitude": amplitude,
                # Well-centre world coordinates — where grid_cell will put the field.
                "cy_um": row * PITCH_UM + FIELD_UM[0] / 2,
                "cx_um": col * PITCH_UM + FIELD_UM[1] / 2,
            }
        )
    total = sum(w["cell_count"] for w in wells)
    print(f"  {total} nuclei over {len(wells)} fields ({wells[0]['cell_count']} in A1, "
          f"{wells[-1]['cell_count']} in {wells[-1]['well']})")

    check(wells)

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy(identifier="neuron-overlay") as app:
        # The stage the whole plate sits on. Every well is placed into THIS one
        # space — a plate is one place, not 24.
        world = space_2d("HCS · plate stage", unit=Unit("micrometer"))

        print("Uploading and grid-placing the fields…")
        clim_max = max(float(np.percentile(w["image"].values, 99.8)) for w in wells)
        scene = None
        field_ids = []
        for well in wells:
            field_ds = create_array_dataset(
                data=well["image"],
                scales=[],  # a 192x256 field needs no pyramid
                name=f"HCS · well {well['well']}",
                axes=["y", "x"],
                anchors=[CoordinateAnchorInput.histogram_anchor(well["image"])],
            )
            # The one call this generator exists to prove: cell index in reading
            # order, the pitch in stage micrometers, and the pixel size on the same
            # edge — position and scale are one claim about one field.
            world.grid_cell(
                field_ds,
                well["index"],
                COLS,
                PITCH_UM,
                scale={"y": PIXEL_UM, "x": PIXEL_UM},
                name=f"{well['well']} -> stage",
            )
            field_ids.append(field_ds)

        print("Uploading the per-well table…")
        table = create_table_dataset(
            name="HCS · wells",
            data=pd.DataFrame(
                {
                    "y": [w["cy_um"] for w in wells],
                    "x": [w["cx_um"] for w in wells],
                    "well": [w["well"] for w in wells],
                    "row": np.array([w["row"] for w in wells], dtype=np.int64),
                    "col": np.array([w["col"] for w in wells], dtype=np.int64),
                    "dose_step": np.array([w["dose_step"] for w in wells], dtype=np.int64),
                    "cell_count": np.array([w["cell_count"] for w in wells], dtype=np.int64),
                    "mean_amplitude": [w["mean_amplitude"] for w in wells],
                }
            ),
            description=(
                f"Per-well measurements of a synthetic {ROWS}x{COLS} screen "
                f"(generator_hcs_plate.py, seed {SEED}); dose doubles per column."
            ),
            columns=[
                ColumnInput(name="y", axis_type=AxisType.SPACE, unit="micrometer"),
                ColumnInput(name="x", axis_type=AxisType.SPACE, unit="micrometer"),
                ColumnInput(name="well", role=ColumnRole.LABEL, long_name="well"),
                ColumnInput(name="row", role=ColumnRole.ATTRIBUTE),
                ColumnInput(name="col", role=ColumnRole.ATTRIBUTE),
                ColumnInput(name="dose_step", role=ColumnRole.ATTRIBUTE, long_name="dose step"),
                ColumnInput(name="cell_count", role=ColumnRole.ATTRIBUTE, long_name="nuclei per field"),
                ColumnInput(name="mean_amplitude", role=ColumnRole.ATTRIBUTE, long_name="mean nuclear intensity"),
            ],
        )
        world.register(table)  # already in stage micrometers

        print("Composing the scene…")
        scene = create_scene(name="HCS · synthetic plate", coordinate_system=world.id)

        for order, (well, field_ds) in enumerate(zip(wells, field_ids)):
            create_intensity_layer(
                lens=field_ds.lens(),
                scene=scene,
                colormap=ColorMap.GREY,
                clim_min=float(BACKGROUND),
                clim_max=clim_max,  # one shared window: the dose dimming must be VISIBLE
                order=order,
            )

        # The plate heat-map: one dot per well over its field, coloured by count.
        point_layer = create_point_layer(
            scene=scene,
            table_dataset=table,
            point_size=30.0,  # stage micrometers
            colormap=ColorMap.VIRIDIS,
            opacity=0.9,
            order=len(wells),
            color_bys=[
                ColumnColorByInput(table=table.id, column="cell_count", colormap=ColorMap.VIRIDIS,
                                   min=0.0, max=float(max(w["cell_count"] for w in wells)),
                                   label="Cell count"),
                ColumnColorByInput(table=table.id, column="mean_amplitude", colormap=ColorMap.INFERNO,
                                   min=0.0, max=float(BASE_AMPLITUDE), label="Staining intensity"),
            ],
            active_color_by=0,
        )
        if (point_layer.y_column, point_layer.x_column) != ("y", "x"):
            raise SystemExit(
                f"well table derived ({point_layer.y_column}, {point_layer.x_column}) — "
                f"declaration did not land"
            )

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  {len(field_ids)} fields grid-placed at {PITCH_UM:.0f} µm pitch")
        print(f"  well table {table.id}, heat-map point layer {point_layer.id}")
