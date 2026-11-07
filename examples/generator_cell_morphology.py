"""Cells in an image, measured, reduced by a PCA and clustered -- every step linked.

The chain a phenotypic screen walks, end to end, on data whose answer is known:

- a **field of ~300 cells** in two channels (DAPI nuclei, actin cytoplasm) and a
  **label mask**, three phenotypes drawn with distinct shapes and staining -- small round
  *quiescent* cells, large round *dividing* cells with bright DNA, elongated *migrating*
  cells with bright actin -- and a *drug* half of the field that shifts their proportions,
- a **measurement table** read off the mask (area, perimeter, eccentricity, solidity,
  axis lengths, nuclear area, mean intensities) and **keyed to it**: a mask id is a row,
  so the scene's label layer colours each cell by a column,
- a **PCA table derived from it row for row** -- IDENTITY over the table's frame,
  TRANSFORMED values, the loadings in its description -- with a **k-means cluster** per
  cell beside the simulated ground truth. Derived, the PCA rows are placed in the
  measurements' world: one chart draws `area` against `eccentricity` and `pc1` against
  `pc2` for the same cells, as two panels (`ChartLayout.STACKED`), because a micrometre
  and a principal component are not one axis,
- charts of values: the PCA scatter coloured by cluster, the area per phenotype (a
  histogram, retuned into a box), and the large cells through a gate (`area >= q75`).

Deterministic -- fixed seed; the PCA and k-means are computed here, in numpy. The field is
deliberately non-square so a y/x transpose fails the checks. Run `--dry-run` first.

Run:  python generator_cell_morphology.py [--dry-run]
"""

from __future__ import annotations

import itertools
import sys

import numpy as np
import pandas as pd
import xarray as xr
from scipy import ndimage
from skimage.draw import ellipse
from skimage.measure import regionprops_table

from mikro import Unit, create_space, dataset_arrays, mikro_service
from mikro.mikro import Mikro
from mikro.api.schema import (
    AxisType,
    Blending,
    ChartKind,
    ChartLayout,
    ChartMark,
    ColorMap,
    ColumnInput,
    ColumnRole,
    DatasetIdentifiesInput,
    IdentityTransformInput,
    PlacementState,
    TableDatasetDerivedFromInput,
    ValueRelation,
)
from mikro.inputs.picker import categorical_color_by, label_render, measure_color_by

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 73
RNG = np.random.default_rng(SEED)

FIELD_SHAPE = (1536, 2048)  # (y, x) px, deliberately non-square
PIXEL_UM = 0.325
GRID = (15, 20)  # one cell per slot, jittered: 300 slots, no overlaps

PHENOTYPES = ("quiescent", "dividing", "migrating")
# (major radius px, minor/major ratio, nucleus/minor ratio, DAPI level, actin level)
SHAPES = {
    "quiescent": ((15.0, 1.2), (0.92, 0.04), 0.62, 0.45, 0.30),
    "dividing": ((29.0, 1.8), (0.90, 0.04), 0.72, 1.00, 0.40),
    "migrating": ((38.0, 2.2), (0.34, 0.04), 0.80, 0.40, 1.00),
}
# The drug half of the field shifts the mix towards dividing cells.
MIX = {"ctrl": (0.45, 0.20, 0.35), "drug": (0.25, 0.45, 0.30)}

BACKGROUND = 120.0
SIGNAL = 2400.0

FEATURES = [
    # (column, unit, long name)
    ("area_um2", "micrometer ** 2", "cell area"),
    ("perimeter_um", "micrometer", "cell perimeter"),
    ("major_axis_um", "micrometer", "major axis length"),
    ("minor_axis_um", "micrometer", "minor axis length"),
    ("eccentricity", None, "eccentricity"),
    ("solidity", None, "solidity"),
    ("nuclear_area_um2", "micrometer ** 2", "nuclear area"),
    ("dapi_mean", None, "mean DAPI intensity"),
    ("actin_mean", None, "mean actin intensity"),
]
N_COMPONENTS = 4
K = 3


# --------------------------------------------------------------------------- #
# The field
# --------------------------------------------------------------------------- #
def draw_field() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    """The two channels, the cell mask, the nucleus mask, and what was drawn where."""
    mask = np.zeros(FIELD_SHAPE, dtype=np.uint32)
    nuclei = np.zeros(FIELD_SHAPE, dtype=np.uint32)
    dapi = np.zeros(FIELD_SHAPE, dtype=np.float64)
    actin = np.zeros(FIELD_SHAPE, dtype=np.float64)

    pitch_y = FIELD_SHAPE[0] / GRID[0]
    pitch_x = FIELD_SHAPE[1] / GRID[1]
    cells: list[dict] = []
    for row, col in itertools.product(range(GRID[0]), range(GRID[1])):
        cy = (row + 0.5) * pitch_y + RNG.uniform(-0.08, 0.08) * pitch_y
        cx = (col + 0.5) * pitch_x + RNG.uniform(-0.08, 0.08) * pitch_x
        condition = "ctrl" if cx < FIELD_SHAPE[1] / 2 else "drug"
        phenotype = PHENOTYPES[RNG.choice(3, p=MIX[condition])]
        (major_mu, major_sd), (ratio_mu, ratio_sd), nucleus_ratio, dapi_level, actin_level = SHAPES[phenotype]
        major = float(np.clip(RNG.normal(major_mu, major_sd), 8.0, 0.46 * min(pitch_y, pitch_x)))
        minor = float(np.clip(major * RNG.normal(ratio_mu, ratio_sd), 6.0, major))
        angle = float(RNG.uniform(0.0, np.pi))

        cell_id = len(cells) + 1
        rr, cc = ellipse(cy, cx, major, minor, shape=FIELD_SHAPE, rotation=angle)
        mask[rr, cc] = cell_id
        nucleus_r = minor * nucleus_ratio
        nr, nc = ellipse(cy, cx, nucleus_r * (1.15 if phenotype == "migrating" else 1.0), nucleus_r, shape=FIELD_SHAPE, rotation=angle)
        nuclei[nr, nc] = cell_id

        jitter = RNG.normal(1.0, 0.06)
        dapi[nr, nc] = dapi_level * jitter
        actin[rr, cc] = actin_level * jitter
        cells.append({"cell_id": cell_id, "phenotype": phenotype, "condition": condition, "drawn_area_px": len(rr), "ellipse_area_px": np.pi * major * minor})

    # A migrating cell's actin piles up at its edge: a ring, brighter than its body.
    migrating = np.isin(mask, [c["cell_id"] for c in cells if c["phenotype"] == "migrating"])
    edge = migrating & ~ndimage.binary_erosion(migrating, iterations=3)
    actin[edge] *= 1.6

    def stain(level: np.ndarray, sigma: float) -> np.ndarray:
        blurred = ndimage.gaussian_filter(level, sigma) * SIGNAL + BACKGROUND
        return np.clip(RNG.poisson(blurred), 0, 65535).astype(np.uint16)

    return stain(dapi, 1.4), stain(actin, 1.8), mask, nuclei, cells


def measure(dapi: np.ndarray, actin: np.ndarray, mask: np.ndarray, nuclei: np.ndarray, cells: list[dict]) -> pd.DataFrame:
    """One row per cell of the mask: its shape, its nucleus, its mean staining."""
    props = pd.DataFrame(
        regionprops_table(
            mask.astype(np.int32),
            intensity_image=np.stack([dapi, actin], axis=-1).astype(np.float64),
            properties=("label", "area", "perimeter", "axis_major_length", "axis_minor_length", "eccentricity", "solidity", "intensity_mean"),
        )
    ).set_index("label")
    nuclear_px = np.bincount(nuclei.ravel(), minlength=mask.max() + 1)
    truth = pd.DataFrame(cells).set_index("cell_id")
    px2 = PIXEL_UM**2
    return pd.DataFrame(
        {
            "cell_id": props.index.to_numpy(dtype=np.int64),
            "area_um2": props["area"].to_numpy() * px2,
            "perimeter_um": props["perimeter"].to_numpy() * PIXEL_UM,
            "major_axis_um": props["axis_major_length"].to_numpy() * PIXEL_UM,
            "minor_axis_um": props["axis_minor_length"].to_numpy() * PIXEL_UM,
            "eccentricity": props["eccentricity"].to_numpy(),
            "solidity": props["solidity"].to_numpy(),
            "nuclear_area_um2": nuclear_px[props.index.to_numpy()] * px2,
            "dapi_mean": props["intensity_mean-0"].to_numpy(),
            "actin_mean": props["intensity_mean-1"].to_numpy(),
            "phenotype": truth.loc[props.index, "phenotype"].to_numpy(),
            "condition": truth.loc[props.index, "condition"].to_numpy(),
        }
    )


# --------------------------------------------------------------------------- #
# PCA and k-means, in numpy
# --------------------------------------------------------------------------- #
def pca(table: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Scores, explained-variance ratios and loadings of the z-scored features."""
    values = table[[name for name, _, _ in FEATURES]].to_numpy(dtype=np.float64)
    z = (values - values.mean(axis=0)) / values.std(axis=0)
    _, s, vt = np.linalg.svd(z, full_matrices=False)
    # A component's sign is arbitrary: fix it so the largest loading is positive.
    signs = np.sign(vt[np.arange(len(vt)), np.abs(vt).argmax(axis=1)])
    vt = vt * signs[:, None]
    scores = z @ vt.T
    explained = s**2 / np.sum(s**2)
    return scores[:, :N_COMPONENTS], explained[:N_COMPONENTS], vt[:N_COMPONENTS]


def kmeans(points: np.ndarray, k: int, iterations: int = 100) -> np.ndarray:
    """Lloyd's algorithm from a k-means++ start, seeded: the cluster of each point, 1..k."""
    rng = np.random.default_rng(SEED)
    centres = [points[rng.integers(len(points))]]
    for _ in range(k - 1):
        d2 = np.min([np.sum((points - c) ** 2, axis=1) for c in centres], axis=0)
        centres.append(points[rng.choice(len(points), p=d2 / d2.sum())])
    centres = np.array(centres)
    labels = np.zeros(len(points), dtype=np.int64)
    for _ in range(iterations):
        labels = np.argmin(((points[:, None, :] - centres[None]) ** 2).sum(axis=2), axis=1)
        moved = np.array([points[labels == j].mean(axis=0) if np.any(labels == j) else centres[j] for j in range(k)])
        if np.allclose(moved, centres):
            break
        centres = moved
    return labels + 1


def agreement(found: np.ndarray, truth: np.ndarray) -> float:
    """The fraction of cells whose cluster matches their phenotype, under the best matching of the two."""
    names = sorted(set(truth))
    best = 0.0
    for perm in itertools.permutations(range(1, len(names) + 1)):
        mapping = dict(zip(perm, names))
        best = max(best, float(np.mean([mapping.get(int(c)) == t for c, t in zip(found, truth)])))
    return best


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    """Draw, measure and analyse locally; check; then upload unless `--dry-run`."""
    dry_run = "--dry-run" in sys.argv

    print("Drawing the field…")
    dapi, actin, mask, nuclei, cells = draw_field()
    measurements = measure(dapi, actin, mask, nuclei, cells)
    scores, explained, loadings = pca(measurements)
    clusters = kmeans(scores[:, :3], K)
    accuracy = agreement(clusters, measurements["phenotype"].to_numpy())

    # --- local checks ---------------------------------------------------------
    if FIELD_SHAPE[0] == FIELD_SHAPE[1]:
        raise SystemExit("the field must be non-square, or a y/x transpose goes unnoticed")
    if len(measurements) != len(cells):
        raise SystemExit(f"the mask holds {len(measurements)} cells, {len(cells)} were drawn")
    drawn = pd.DataFrame(cells).set_index("cell_id").loc[measurements["cell_id"]]
    measured_px = measurements["area_um2"].to_numpy() / PIXEL_UM**2
    if not np.allclose(measured_px, drawn["drawn_area_px"].to_numpy()):
        raise SystemExit("cells overlap: a mask region is smaller than the ellipse drawn for it")
    area_error = float(np.max(np.abs(measured_px - drawn["ellipse_area_px"].to_numpy()) / drawn["ellipse_area_px"].to_numpy()))
    if area_error > 0.05:
        raise SystemExit(f"measured areas are off the ellipses' (pi a b) by up to {area_error:.1%}")
    if explained[:2].sum() < 0.60:
        raise SystemExit(f"PC1+PC2 explain only {explained[:2].sum():.0%} of the variance")
    if accuracy < 0.90:
        raise SystemExit(f"k-means agrees with the phenotypes for only {accuracy:.0%} of the cells")
    counts = measurements["phenotype"].value_counts().to_dict()
    print(f"  {len(measurements)} cells: " + ", ".join(f"{counts.get(p, 0)} {p}" for p in PHENOTYPES))
    print(f"  PC1..PC{N_COMPONENTS} explain " + ", ".join(f"{v:.0%}" for v in explained) + f" (PC1+PC2 {explained[:2].sum():.0%})")
    print(f"  k-means (k={K}) matches the phenotypes for {accuracy:.0%} of the cells; areas within {area_error:.1%} of pi a b")

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Imported here, so a dry run needs nothing but the science stack.
    from arkitekt import easy

    with easy("cell-morphology", mikro_service) as mikro:
        upload(mikro, dapi, actin, mask, measurements, scores, explained, loadings, clusters, accuracy)


def upload(
    mikro: Mikro,
    dapi: np.ndarray,
    actin: np.ndarray,
    mask: np.ndarray,
    measurements: pd.DataFrame,
    scores: np.ndarray,
    explained: np.ndarray,
    loadings: np.ndarray,
    clusters: np.ndarray,
    accuracy: float,
) -> None:
    """The image, the mask, both tables and their links, the scene and the charts -- and the round trip."""
    world = create_space(mikro, "Cell morphology · field", {"y": Unit("micrometer"), "x": Unit("micrometer")})
    scale = {"y": PIXEL_UM, "x": PIXEL_UM}

    print("Uploading the channels and the mask…")
    channels = {}
    for name, image in (("DAPI", dapi), ("actin", actin)):
        data, scales = dataset_arrays(xr.DataArray(image, dims=("y", "x"), name=name), levels=3, method="mean")
        channels[name] = mikro.create_array_dataset(data=data, scales=scales, name=f"Cell morphology · {name}", axes=["y", "x"])
        world.register(channels[name], scale=scale)
    mask_ds = mikro.create_array_dataset(
        data=xr.DataArray(mask, dims=("y", "x")),
        scales=[],  # no pyramid: the average of two cell ids is a third cell's id
        name="Cell morphology · cells",
        axes=["y", "x"],
    )
    world.register(mask_ds, scale=scale)

    print("Uploading the measurements, keyed to the mask…")
    table = mikro.create_table_dataset(
        name="Cell morphology · measurements",
        description=f"Per-cell shape and staining read off the mask (generator_cell_morphology.py, seed {SEED}).",
        data=measurements,
        columns=[
            # The key: a mask id is a row, so the label layer's picker reads these columns.
            ColumnInput(name="cell_id", axis_type=AxisType.INDEX, long_name="cell", identified_by=[DatasetIdentifiesInput(dataset=mask_ds.id)]),
            *(ColumnInput(name=name, role=ColumnRole.ATTRIBUTE, unit=unit, long_name=long) if unit else ColumnInput(name=name, role=ColumnRole.ATTRIBUTE, long_name=long) for name, unit, long in FEATURES),
            ColumnInput(name="phenotype", role=ColumnRole.LABEL, long_name="phenotype (simulated truth)"),
            ColumnInput(name="condition", role=ColumnRole.ATTRIBUTE, long_name="condition"),
        ],
    )
    if [axis.name for axis in table.coordinate_system.axes] != ["cell_id"]:
        raise SystemExit(f"the measurements' space is {[a.name for a in table.coordinate_system.axes]}, not its frame (cell_id)")

    print("Uploading the PCA, derived row for row…")
    loading_text = "; ".join(f"PC{i + 1} ({explained[i]:.0%}): " + ", ".join(f"{name} {loadings[i, j]:+.2f}" for j, (name, _, _) in enumerate(FEATURES)) for i in range(N_COMPONENTS))
    pca_table = mikro.create_table_dataset(
        name="Cell morphology · PCA",
        description=f"PCA of the z-scored measurements and a k-means clustering (k={K}) of PC1-PC3. {loading_text}",
        data=pd.DataFrame(
            {
                "cell_id": measurements["cell_id"].to_numpy(dtype=np.int64),
                **{f"pc{i + 1}": scores[:, i] for i in range(N_COMPONENTS)},
                "cluster": clusters.astype(np.int64),
            }
        ),
        columns=[
            # Keyed to the mask too, so the scene can colour each cell by its cluster.
            ColumnInput(name="cell_id", axis_type=AxisType.INDEX, long_name="cell", identified_by=[DatasetIdentifiesInput(dataset=mask_ds.id)]),
            *(ColumnInput(name=f"pc{i + 1}", role=ColumnRole.ATTRIBUTE, long_name=f"principal component {i + 1}") for i in range(N_COMPONENTS)),
            ColumnInput(name="cluster", role=ColumnRole.GROUP_ID, long_name="k-means cluster"),
        ],
        # The link: the same rows, new numbers. Placed in the measurements' world by it.
        derived_from=[
            TableDatasetDerivedFromInput(table_dataset=table.id, transform=IdentityTransformInput(), value_relation=ValueRelation.TRANSFORMED)
        ],
    )

    print("Composing the scene…")
    scene = mikro.create_scene(name="Cell morphology · field", coordinate_system=world.id)
    for order, (name, colormap) in enumerate((("DAPI", ColorMap.GREY), ("actin", ColorMap.MAGENTA))):
        image = dapi if name == "DAPI" else actin
        mikro.create_intensity_layer(
            lens=channels[name].lens(),
            scene=scene,
            colormap=colormap,
            clim_min=float(BACKGROUND),
            clim_max=float(np.percentile(image, 99.8)),
            blending=Blending.ADDITIVE,
            order=order,
        )
    color_bys = [
        categorical_color_by(table, "phenotype", label="Phenotype (truth)"),
        categorical_color_by(pca_table, "cluster", label="k-means cluster"),
        measure_color_by(pca_table, "pc1", colormap=ColorMap.VIRIDIS, min=float(scores[:, 0].min()), max=float(scores[:, 0].max()), label="PC1"),
        measure_color_by(table, "area_um2", colormap=ColorMap.INFERNO, min=0.0, max=float(measurements["area_um2"].max()), label="Area"),
    ]
    label_layer = mikro.create_label_layer(
        lens=mask_ds.lens().id,
        scene=scene.id,
        render=label_render(color_bys, active=1, background=0),
        opacity=0.55,
        order=2,
    )
    published = label_layer.label_render.color_bys if label_layer.label_render else ()
    if len(published) != len(color_bys):
        raise SystemExit(f"the label layer offers {len(published)} colourings, {len(color_bys)} were given")

    print("Plotting…")
    scatter = pca_table.plot("pc1", "pc2", "cluster", name="PCA · PC1 vs PC2 by cluster")

    side_by_side = mikro.create_chart(
        name="Cell morphology · measurements & PCA",
        kind=ChartKind.VALUES,
        coordinate_system=table.coordinate_system.id,
        layout=ChartLayout.STACKED,
    )
    mikro.create_points_chart_layer(chart=side_by_side.id, lens=table.lens().id, x_column="area_um2", y_column="eccentricity", name="Area vs eccentricity")
    mikro.create_points_chart_layer(chart=side_by_side.id, lens=pca_table.lens().id, x_column="pc1", y_column="pc2", z_column="cluster", name="PC1 vs PC2")

    per_phenotype = table.plot("area_um2", group="phenotype", bins=30, name="Area per phenotype")
    mikro.update_distribution_chart_layer(per_phenotype.layers[0].id, mark=ChartMark.BOX)

    q75 = float(np.percentile(measurements["area_um2"], 75))
    gate = table.lens(area_um2=(q75, None))
    large = table.plot("area_um2", "eccentricity", lens=gate, name="Large cells (area ≥ q75)")

    # --- round trip -----------------------------------------------------------
    shared = mikro.get_chart(side_by_side.id)
    if shared.layout != ChartLayout.STACKED:
        raise SystemExit(f"the shared chart reads back as {shared.layout}, not STACKED")
    for layer in shared.layers:
        if layer.placement != PlacementState.PLACED or not (layer.as_affine and layer.as_affine.total):
            raise SystemExit(f"layer '{layer.name}' is {layer.placement} in the measurements' world: the derivation did not place the PCA rows")
    boxed = mikro.get_chart(per_phenotype.id).layers[0]
    if boxed.mark != ChartMark.BOX:
        raise SystemExit(f"the distribution reads back as {boxed.mark}, not BOX")
    for chart in (scatter, shared, per_phenotype, large):
        if chart.kind != ChartKind.VALUES:
            raise SystemExit(f"chart '{chart.name}' is {chart.kind}, not a chart of values")

    print(f"\nDone — scene '{scene.name}' ({scene.id}):")
    print(f"  channels   : DAPI {channels['DAPI'].id}, actin {channels['actin'].id}; mask {mask_ds.id} ({len(measurements)} cells)")
    print(f"  tables     : measurements {table.id} -> PCA {pca_table.id} (derived row for row; k-means matches {accuracy:.0%})")
    print(f"  label layer: {label_layer.id}, {len(published)} colourings (active: k-means cluster)")
    print(f"  charts     : PCA {scatter.id}, side by side {shared.id}, per phenotype {per_phenotype.id}, large cells {large.id}")


if __name__ == "__main__":
    main()
