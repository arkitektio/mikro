"""A synthetic DTI tractography scene — streamlines through a diffusion field.

The MRI flagship: one head, four datasets, four layer kinds, and the first
**three-dimensional TrackLayer** (SPT's tracks were planar; here `zColumn` derives
too, and with no time column each streamline draws in its parquet row order — which
is why rows are written in path order).

- the **FA map** ``(z, y, x)`` at 1.5 mm: bright fiber bundles in dim white matter
  inside a brain ellipsoid — the anatomical underlay, MIP'd by the bootstrap,
- the **principal-diffusion-direction field** ``(v, z, y, x)``, direction · FA on a
  DISPLACEMENT axis — the vector layer the scene bootstrap infers (a vector layer
  cannot be authored directly; staging is the only door),
- the **streamlines**: RK2 integration through that very field from seeds inside
  the bundles, one table row per point in millimeters — a 3D TrackLayer colored by
  per-point FA,
- a **glass brain**: marching cubes on the brain mask as a translucent mesh
  collection around everything.

Bundles are parametric tubes with tangent fields — a corpus-callosum arc, two
cingulum-like arcs, a fornix-like curve — so the tracker's output can be *checked*
against the geometry that generated its input: every streamline point must stay
inside its bundle's tube, and every step must align with the field.

MRI conventions follow converter_nifti_dataset.py: array axes (z, y, x), data
never permuted, world in millimeters. Volume deliberately non-cubic.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first.

Run:  python generator_dti_tractography.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import trimesh
import xarray as xr
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes

from mikro_next import Unit, dataset_arrays, space_3d
from arkitekt_next import easy
from mikro_next.api.schema import (
    AxisInput,
    AxisType,
    ColorMap,
    ColumnInput,
    ColumnRole,
    CoordinateAnchorInput,
    PlacementState,
    ProjectionMode,
    ScenePolicyInput,
    ValueRelation,
    create_array_dataset,
    create_mesh_collection,
    create_mesh_layer,
    create_table_dataset,
    create_track_layer,
    create_volume_layer,
)
from mikro_next.meshes import build_mesh_collection
from mikro_next.rath import current_mikro_next_rath

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 83
RNG = np.random.default_rng(SEED)

SHAPE = (96, 128, 112)  # (z, y, x) voxels, deliberately non-cubic
VOX_MM = 1.5

BRAIN_RADII = (40.0, 56.0, 48.0)  # voxels, (z, y, x)

# Bundles: (name, tube radius in voxels). Centerlines are built in make_bundles().
BUNDLE_RADII = {"corpus_callosum": 4.0, "cingulum_left": 3.0, "cingulum_right": 3.0, "fornix": 2.5}

FA_BUNDLE = 0.85
FA_WM = 0.2
FA_STOP = 0.15  # tracking termination threshold

STEP_VOX = 0.5  # integration step (0.75 mm)
MAX_STEPS = 400
SEEDS_PER_BUNDLE = 60
MIN_POINTS = 20

MESH_FACES = 40_000
LEVELS = 3


# --------------------------------------------------------------------------- #
# Ground truth: bundles as centerlines with tangents
# --------------------------------------------------------------------------- #
def _centerline(points_fn, n: int = 400) -> tuple[np.ndarray, np.ndarray]:
    """Sample a parametric curve and its unit tangents — two ``(n, 3)`` arrays (z,y,x)."""
    t = np.linspace(0.0, 1.0, n)
    pts = points_fn(t)
    tangents = np.gradient(pts, axis=0)
    tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    return pts, tangents


def make_bundles() -> dict[str, dict]:
    """The four bundles, each a centerline + tangents + radius, in voxel coords."""
    cz, cy, cx = SHAPE[0] / 2, SHAPE[1] / 2, SHAPE[2] / 2

    def cc(t):  # left-right arc, bowing up in z: the corpus-callosum shape
        return np.column_stack(
            [cz + 18 * np.sin(np.pi * t), cy - 6 + 4 * np.sin(2 * np.pi * t), cx - 38 + 76 * t]
        )

    def cingulum(side):
        def curve(t):  # anterior-posterior arc, clear ABOVE the callosum apex —
            # tubes must not intersect, or a tracker legitimately hops bundles at
            # the crossing and the containment check below cannot hold.
            return np.column_stack(
                [cz + 27 + 6 * np.sin(np.pi * t), cy - 40 + 80 * t, cx + side * 14 + 3 * np.sin(2 * np.pi * t)]
            )
        return curve

    def fornix(t):  # a C-curve dipping under
        return np.column_stack(
            [cz - 4 - 14 * np.sin(np.pi * t), cy - 26 + 52 * t, cx + 5 * np.sin(np.pi * t)]
        )

    curves = {
        "corpus_callosum": cc,
        "cingulum_left": cingulum(-1),
        "cingulum_right": cingulum(+1),
        "fornix": fornix,
    }
    bundles = {}
    for name, fn in curves.items():
        pts, tans = _centerline(fn)
        bundles[name] = {"points": pts, "tangents": tans, "radius": BUNDLE_RADII[name],
                         "tree": cKDTree(pts)}
    return bundles


def make_fields(bundles: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Per-voxel FA, direction field, brain mask, bundle-id map.

    Every brain voxel near a centerline takes that centerline's tangent as its
    principal direction and a high FA falling off toward the tube wall; other
    brain voxels are isotropic-ish white matter (low FA, no direction)."""
    zz, yy, xx = np.mgrid[0 : SHAPE[0], 0 : SHAPE[1], 0 : SHAPE[2]].astype(np.float64)
    cz, cy, cx = SHAPE[0] / 2, SHAPE[1] / 2, SHAPE[2] / 2
    brain = (
        ((zz - cz) / BRAIN_RADII[0]) ** 2
        + ((yy - cy) / BRAIN_RADII[1]) ** 2
        + ((xx - cx) / BRAIN_RADII[2]) ** 2
    ) <= 1.0

    voxels = np.column_stack([zz[brain], yy[brain], xx[brain]])
    fa_flat = np.full(len(voxels), FA_WM) + RNG.normal(0, 0.02, len(voxels))
    dir_flat = np.zeros((len(voxels), 3))
    bundle_flat = np.zeros(len(voxels), dtype=np.int32)

    for index, (name, bundle) in enumerate(bundles.items(), start=1):
        dist, nearest = bundle["tree"].query(voxels)
        inside = dist <= bundle["radius"]
        profile = 1.0 - (dist[inside] / bundle["radius"]) ** 2
        fa_flat[inside] = FA_WM + (FA_BUNDLE - FA_WM) * (0.4 + 0.6 * profile)
        dir_flat[inside] = bundle["tangents"][nearest[inside]]
        bundle_flat[inside] = index

    fa = np.zeros(SHAPE)
    fa[brain] = np.clip(fa_flat, 0.0, 1.0)
    direction = np.zeros((3, *SHAPE))
    for component in range(3):
        direction[component][brain] = dir_flat[:, component]
    bundle_map = np.zeros(SHAPE, dtype=np.int32)
    bundle_map[brain] = bundle_flat
    return fa, direction, brain, bundle_map


# --------------------------------------------------------------------------- #
# Tracking
# --------------------------------------------------------------------------- #
def track(fa: np.ndarray, direction: np.ndarray, bundle_map: np.ndarray, bundles: dict) -> pd.DataFrame:
    """Deterministic RK2 streamlines through the direction field.

    Seeds sit inside bundle tubes; each seed integrates both ways (tangents have a
    consistent orientation along a centerline, so the backward half is the forward
    half with the field negated) and the halves are joined into one path. A step
    keeps direction continuity by flipping any field sample that opposes the
    previous step — the field is an orientation, not a signed velocity."""

    def sample(p: np.ndarray) -> tuple[float, np.ndarray]:
        iz, iy, ix = (int(round(c)) for c in p)
        if not (0 <= iz < SHAPE[0] and 0 <= iy < SHAPE[1] and 0 <= ix < SHAPE[2]):
            return 0.0, np.zeros(3)
        return float(fa[iz, iy, ix]), direction[:, iz, iy, ix].copy()

    def integrate(seed: np.ndarray, sign: float) -> list[np.ndarray]:
        path, p = [], seed.copy()
        prev = None
        for _ in range(MAX_STEPS):
            fa_here, d = sample(p)
            if fa_here < FA_STOP or not d.any():
                break
            d = sign * d
            if prev is not None and np.dot(d, prev) < 0:
                d = -d
            mid_fa, dm = sample(p + 0.5 * STEP_VOX * d)
            if mid_fa < FA_STOP or not dm.any():
                break
            dm = dm if np.dot(dm, d) >= 0 else -dm
            p = p + STEP_VOX * dm
            prev = dm
            path.append(p.copy())
        return path

    names = list(bundles)
    rows, track_id = [], 0
    for index, name in enumerate(names, start=1):
        seed_pool = np.column_stack(np.nonzero(bundle_map == index)).astype(np.float64)
        chosen = seed_pool[RNG.choice(len(seed_pool), size=SEEDS_PER_BUNDLE, replace=False)]
        for seed in chosen:
            backward = integrate(seed, -1.0)[::-1]
            forward = integrate(seed, +1.0)
            path = backward + [seed] + forward
            if len(path) < MIN_POINTS:
                continue
            pts = np.array(path)
            iz = np.clip(np.round(pts).astype(int), 0, np.array(SHAPE) - 1)
            rows.append(
                pd.DataFrame(
                    {
                        # Axis columns first, (z, y, x) file order, in millimeters.
                        "z": pts[:, 0] * VOX_MM,
                        "y": pts[:, 1] * VOX_MM,
                        "x": pts[:, 2] * VOX_MM,
                        "track_id": np.full(len(pts), track_id, dtype=np.int64),
                        "fa": fa[iz[:, 0], iz[:, 1], iz[:, 2]],
                        "bundle": name,
                    }
                )
            )
            track_id += 1
    # Row order within a track IS the drawn path (no t column), so concat keeps
    # path order and the sort key is the track alone.
    return pd.concat(rows, ignore_index=True).sort_values("track_id", kind="stable", ignore_index=True)


# --------------------------------------------------------------------------- #
# The glass brain
# --------------------------------------------------------------------------- #
def glass_brain(brain: np.ndarray):
    """The brain mask as one decimated trimesh, vertices (x, y, z) in voxel coords."""
    smooth = gaussian_filter(brain.astype(np.float64), 2.0)
    padded = np.pad(smooth, 1)
    verts, faces, _, _ = marching_cubes(padded, level=0.5, step_size=1)
    verts -= 1.0  # undo the pad

    # (z, y, x) -> (x, y, z), component-wise; faces exactly as returned — the
    # component reversal is a reflection that already flips the winding.
    verts_xyz = verts[:, ::-1]
    extent_xyz = np.array(SHAPE, dtype=np.float64)[::-1]
    verts_xyz = np.clip(verts_xyz, 0.0, extent_xyz)

    mesh = trimesh.Trimesh(vertices=verts_xyz, faces=faces, process=False)
    if len(mesh.faces) > MESH_FACES:
        mesh = mesh.simplify_quadric_decimation(face_count=MESH_FACES)
    return mesh


# --------------------------------------------------------------------------- #
# Self-checks
# --------------------------------------------------------------------------- #
def check(fa, direction, brain, bundles, tracks: pd.DataFrame, mesh) -> None:
    if fa.shape != SHAPE:
        raise SystemExit(f"FA volume is {fa.shape}, expected {SHAPE} — transposed?")

    inside = fa[brain]
    if not (0.7 < inside.max() <= 1.0 and abs(np.median(inside) - FA_WM) < 0.05):
        raise SystemExit("FA histogram is not bundles-over-WM — the phantom is wrong")

    n_tracks = tracks["track_id"].nunique()
    if n_tracks < 150:
        raise SystemExit(f"only {n_tracks} streamlines survived — tracking is broken")

    # The tracker must have stayed inside the geometry that generated its field:
    # every point within its bundle's tube (plus a step of slack), and every step
    # aligned with the local field direction.
    for name, bundle in bundles.items():
        pts_mm = tracks.loc[tracks["bundle"] == name, ["z", "y", "x"]].to_numpy()
        if not len(pts_mm):
            raise SystemExit(f"bundle '{name}' produced no streamlines")
        dist, _ = bundle["tree"].query(pts_mm / VOX_MM)
        worst = float(dist.max())
        if worst > bundle["radius"] + 2 * STEP_VOX:
            raise SystemExit(f"'{name}': a streamline strayed {worst:.2f} vox from the tube")

    alignments = []
    for _, one in tracks.groupby("track_id"):
        pts = one[["z", "y", "x"]].to_numpy() / VOX_MM
        steps = np.diff(pts, axis=0)
        steps /= np.maximum(np.linalg.norm(steps, axis=1, keepdims=True), 1e-12)
        idx = np.clip(np.round(pts[:-1]).astype(int), 0, np.array(SHAPE) - 1)
        field = direction[:, idx[:, 0], idx[:, 1], idx[:, 2]].T
        norms = np.linalg.norm(field, axis=1)
        ok = norms > 0
        alignments.append(np.abs((steps[ok] * field[ok]).sum(axis=1) / norms[ok]).mean())
    mean_alignment = float(np.mean(alignments))
    if not mean_alignment >= 0.9:
        raise SystemExit(f"step/field alignment {mean_alignment:.3f} < 0.9 — the tracker wandered")

    verts = np.asarray(mesh.vertices)
    extent_xyz = np.array(SHAPE, dtype=np.float64)[::-1]
    if (verts < -1e-9).any() or (verts > extent_xyz + 1e-9).any():
        raise SystemExit("glass-brain vertices leave the volume — the (x,y,z) reversal is off")

    print(
        f"  checks pass: {n_tracks} streamlines / {len(tracks)} points, "
        f"alignment {mean_alignment:.3f}, mesh {len(mesh.faces)} faces in bounds"
    )


LAYERS_QUERY = """
query Layers($id: ID!) {
  scene(id: $id) {
    layers {
      __typename
      placement
      ... on VectorLayer { vectorAxis }
    }
  }
}
"""


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Building bundles and fields ({SHAPE} @ {VOX_MM} mm)…")
    bundles = make_bundles()
    fa, direction, brain, bundle_map = make_fields(bundles)

    print("Tracking streamlines…")
    tracks = track(fa, direction, bundle_map, bundles)
    print(f"  {tracks['track_id'].nunique()} streamlines, {len(tracks)} points")

    print("Meshing the glass brain…")
    mesh = glass_brain(brain)
    print(f"  {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

    check(fa, direction, brain, bundles, tracks, mesh)

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy(identifier="neuron-overlay") as app:
        world = space_3d("DTI · head", unit=Unit("millimeter"))

        print("Uploading principal-direction field…")
        pdd = (direction * fa[None]).astype(np.float32)
        pdd_ds = create_array_dataset(
            data=xr.DataArray(pdd, dims=("v", "z", "y", "x"), name="pdd"),
            scales=[],  # how a pyramid treats a DISPLACEMENT store is deliberately unresolved
            name="DTI · principal diffusion direction",
            axes=[
                AxisInput(name="v", type=AxisType.DISPLACEMENT),
                AxisInput(name="z", type=AxisType.SPACE),
                AxisInput(name="y", type=AxisType.SPACE),
                AxisInput(name="x", type=AxisType.SPACE),
            ],
        )
        world.register(pdd_ds, scale={"z": VOX_MM, "y": VOX_MM, "x": VOX_MM})

        # The bootstrap is the only door to a VectorLayer, and the policy must be
        # EMPTY: an explicit kind (e.g. VOLUME) overrides the DISPLACEMENT-axis
        # inference and draws the components as a grey intensity volume instead —
        # measured on the first run of this script. So the scene is staged while
        # ONLY the PDD is registered, and every other layer is authored by hand
        # on the returned scene, with its dataset registered afterwards.
        print("Staging the scene…")
        scene = world.stage(name="DTI · tractography", policy=ScenePolicyInput())

        print("Uploading FA map…")
        fa_xr = xr.DataArray((fa * 255).astype(np.uint8), dims=("z", "y", "x"), name="fa")
        fa_data, fa_scales = dataset_arrays(fa_xr, levels=LEVELS, method="mean")
        fa_ds = create_array_dataset(
            data=fa_data,
            scales=fa_scales,
            name="DTI · FA map",
            axes=["z", "y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(fa_xr)],
        )
        world.register(fa_ds, scale={"z": VOX_MM, "y": VOX_MM, "x": VOX_MM})
        create_volume_layer(
            lens=fa_ds.lens(),
            scene=scene.id,
            mode=ProjectionMode.MIP,
            colormap=ColorMap.GREY,
            clim_min=0.0,
            clim_max=255.0,
            opacity=0.9,
            order=0,
        )

        print("Uploading streamlines…")
        table = create_table_dataset(
            name="DTI · streamlines",
            data=tracks,
            description=(
                f"RK2 streamlines through the synthetic PDD field "
                f"(generator_dti_tractography.py, seed {SEED}); coordinates in mm, "
                f"row order within a track is the path order."
            ),
            columns=[
                ColumnInput(name="z", axis_type=AxisType.SPACE, unit="millimeter"),
                ColumnInput(name="y", axis_type=AxisType.SPACE, unit="millimeter"),
                ColumnInput(name="x", axis_type=AxisType.SPACE, unit="millimeter"),
                ColumnInput(name="track_id", role=ColumnRole.TRACK_ID, long_name="streamline"),
                ColumnInput(name="fa", role=ColumnRole.ATTRIBUTE, long_name="fractional anisotropy"),
                ColumnInput(name="bundle", role=ColumnRole.LABEL, long_name="bundle"),
            ],
        )
        world.register(table)

        track_layer = create_track_layer(
            scene=scene,
            table_dataset=table,
            color_by_column="fa",
            colormap=ColorMap.INFERNO,
            line_width=0.4,  # millimeters
            opacity=0.9,
            order=3,
        )
        derived = (track_layer.track_id_column, track_layer.z_column,
                   track_layer.y_column, track_layer.x_column, track_layer.t_column)
        if derived != ("track_id", "z", "y", "x", None):
            raise SystemExit(f"track layer derived {derived} — the 3D declaration did not land")

        print("Uploading glass brain…")
        built = build_mesh_collection({1: mesh}, levels=LEVELS)
        collection = create_mesh_collection(
            version=f"v20260901-dti-glass-brain-seed{SEED}",
            store=built,
            axes=[AxisInput(name=d, type=AxisType.SPACE) for d in ("x", "y", "z")],
            derived_from=[
                fa_ds.lens().derive(
                    input_axes=["x", "y", "z"],
                    output_axes=["x", "y", "z"],
                    value_relation=ValueRelation.TRANSFORMED,
                )
            ],
            provenance_metadata={"generator": "generator_dti_tractography.py", "seed": SEED},
        )
        mesh_layer = create_mesh_layer(
            scene=scene.id,
            mesh_collection=collection.id,
            material_color=[205, 215, 255, 255],
            wireframe=False,
            opacity=0.18,
            order=2,
        )
        if mesh_layer.placement != PlacementState.PLACED:
            raise SystemExit(f"glass brain did not reach the world: {mesh_layer.placement}")

        # The whole cast, read back through the interface: one of each kind, all placed.
        result = current_mikro_next_rath.get().query(LAYERS_QUERY, {"id": scene.id})
        layers = result.data["scene"]["layers"]
        kinds = sorted(layer["__typename"] for layer in layers)
        if kinds != ["IntensityLayer", "MeshLayer", "TrackLayer", "VectorLayer"]:
            raise SystemExit(f"scene holds {kinds} — expected exactly one of each kind")
        unplaced = [l["__typename"] for l in layers if l["placement"] != "PLACED"]
        if unplaced:
            raise SystemExit(f"unplaced layers: {unplaced}")
        vector = next(l for l in layers if l["__typename"] == "VectorLayer")
        if vector["vectorAxis"] != "v":
            raise SystemExit(f"vector layer derived axis {vector['vectorAxis']!r}, not 'v'")

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  FA {fa_ds.id}, PDD {pdd_ds.id} (vector layer bootstrapped)")
        print(f"  streamlines table {table.id} ({tracks['track_id'].nunique()} tracks), layer {track_layer.id}")
        print(f"  glass brain collection {collection.id}, layer {mesh_layer.id}")
