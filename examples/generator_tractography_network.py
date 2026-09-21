"""Tractography again — the same streamlines, this time as a NetworkLayer.

The sibling of :mod:`generator_dti_tractography`, which drew its streamlines as a
TrackLayer (a table of rows). Here the SAME phantom, the same tracker and the same
glass brain ship the streamlines through **konnektion** instead: every streamline
is one network object — a chain of nodes and edges with per-node FA in the
collection's own vocabulary and a per-node radius — drawn by a NetworkLayer whose
segments taper and whose picker mixes all three colouring sources:

- ``graph_color_by("fa")``: per-NODE colour from the vocabulary the collection
  itself carries — the colouring a table cannot express,
- ``measure_color_by(table, ...)``: per-STREAMLINE colour through the object table
  (mean FA, length), keyed by the NETWORK_COLLECTION identification,
- categorical bundle membership from the same table.

Why both scripts exist: a TrackLayer is rows (cheap, ordered, no topology); a
network collection is a graph (octree-tiled, level-of-detail, per-node vocabulary,
taper). Same anatomy, two honest encodings — and having both over one phantom is
what makes the difference visible instead of theoretical.

The phantom, the tracker, the glass brain and their self-checks are imported from
the track-layer script, not copied — one ground truth, two scenes.

Deterministic — same seed as the sibling, no network beyond the upload.

Run:  python generator_tractography_network.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import xarray as xr

import konnektion
from arkitekt import easy
from mikro import Unit, dataset_arrays, space_3d, mikro_service
from mikro.mikro import Mikro
from mikro.api.schema import (
    AxisInput,
    AxisType,
    ColorMap,
    ColumnInput,
    ColumnRole,
    CoordinateAnchorInput,
    GraphTarget,
    NetworkCollectionIdentifiesInput,
    PlacementState,
    ProjectionMode,
    ValueRelation,
)
from fabriks import build_collection
from mikro.inputs.picker import graph_color_by, graph_filter_by, measure_color_by, network_filter_by

# One ground truth, two scripts: the phantom, tracker, mesh and their checks come
# from the TrackLayer sibling. Its module level holds only constants, so the
# import runs no simulation.
from generator_dti_tractography import (
    LEVELS,
    SEED,
    SHAPE,
    VOX_MM,
    check,
    glass_brain,
    make_bundles,
    make_fields,
    track,
)

COLLECTION_AXES = ("x", "y", "z")  # konnektion's frame; the array's is (z, y, x)


# --------------------------------------------------------------------------- #
# Streamlines -> one konnektion object per streamline
# --------------------------------------------------------------------------- #
def to_networks(tracks: pd.DataFrame) -> tuple[dict[int, konnektion.Network], pd.DataFrame]:
    """Each streamline as a chain: nodes in (x, y, z) VOXEL coordinates, edges
    between consecutive points, per-node ``fa`` in the vocabulary, radius from FA.

    Object ids are 1-based (0 is what a background would be everywhere else this
    convention appears). Returns the objects and the per-streamline table."""
    objects: dict[int, konnektion.Network] = {}
    rows = []
    extent_xyz = np.array(SHAPE, dtype=np.float64)[::-1] - 1e-6

    for track_id, one in tracks.groupby("track_id", sort=True):
        pts_vox = one[["z", "y", "x"]].to_numpy() / VOX_MM
        # (z, y, x) -> (x, y, z), component-wise; clamped to the positive octant
        # (Morton addressing refuses negatives, and a terminal step can poke a
        # hair past a face).
        nodes = np.clip(pts_vox[:, ::-1], 0.0, extent_xyz)
        fa = one["fa"].to_numpy(dtype=np.float64)
        edges = np.column_stack([np.arange(len(nodes) - 1), np.arange(1, len(nodes))])

        object_id = int(track_id) + 1
        objects[object_id] = konnektion.Network(
            nodes=nodes,
            edges=edges.astype(np.int64),
            radii=0.25 + 0.6 * fa,  # voxels: high-FA cores draw fatter
            root=0,
            attributes={"fa": fa},
        )
        length_mm = float(np.linalg.norm(np.diff(pts_vox, axis=0), axis=1).sum() * VOX_MM)
        rows.append(
            {
                "object_id": object_id,
                "bundle": str(one["bundle"].iloc[0]),
                "n_points": len(nodes),
                "length_mm": length_mm,
                "mean_fa": float(fa.mean()),
            }
        )
    return objects, pd.DataFrame(rows)


def check_networks(objects: dict[int, konnektion.Network], tracks: pd.DataFrame) -> None:
    """The conversion must be lossless: node counts per object equal the point
    counts per track, and the vocabulary rides one value per node."""
    per_track = tracks.groupby("track_id").size()
    for track_id, count in per_track.items():
        net = objects[int(track_id) + 1]
        if len(net.nodes) != count or len(net.edges) != count - 1:
            raise SystemExit(f"track {track_id}: {count} points became "
                             f"{len(net.nodes)} nodes / {len(net.edges)} edges")
        if len(net.attributes["fa"]) != len(net.nodes):
            raise SystemExit(f"track {track_id}: fa vocabulary is not one value per node")
    print(f"  network conversion lossless: {len(objects)} chains, "
          f"{sum(len(n.nodes) for n in objects.values())} nodes")


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

    check(fa, direction, brain, bundles, tracks, mesh)

    print("Converting to a konnektion collection…")
    objects, streamline_stats = to_networks(tracks)
    check_networks(objects, tracks)

    built = konnektion.build_collection(objects, axes=COLLECTION_AXES)
    store = konnektion.MemoryStore()
    built.write(store, "check")
    report = konnektion.verify(konnektion.open_collection(store, "check"), tier="topology")
    if not report.ok:
        raise SystemExit(f"the collection does not verify:\n{report}")
    print(f"  verify: {str(report).splitlines()[0]}")

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy("neuron-overlay", mikro_service) as mikro:
        world = space_3d(mikro, "DTI · head (network)", unit=Unit("millimeter"))

        print("Uploading FA map…")
        fa_xr = xr.DataArray((fa * 255).astype(np.uint8), dims=("z", "y", "x"), name="fa")
        fa_data, fa_scales = dataset_arrays(fa_xr, levels=LEVELS, method="mean")
        fa_ds = mikro.create_array_dataset(
            data=fa_data,
            scales=fa_scales,
            name="DTI · FA map (network scene)",
            axes=["z", "y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(fa_xr)],
        )
        world.register(fa_ds, scale={"z": VOX_MM, "y": VOX_MM, "x": VOX_MM})

        # No vector layer this time, so no bootstrap dance: every layer is authored.
        print("Composing the scene…")
        scene = mikro.create_scene(name="DTI · tractography (network)", coordinate_system=world.id)
        mikro.create_volume_layer(
            lens=fa_ds.lens(),
            scene=scene.id,
            mode=ProjectionMode.MIP,
            colormap=ColorMap.GREY,
            clim_min=0.0,
            clim_max=255.0,
            opacity=0.9,
            order=0,
        )

        print("Registering the network collection…")
        # The MAP_AXIS derivation is the load-bearing line: the collection is
        # (x, y, z) over a (z, y, x) source — an IDENTITY would pass the rank
        # check and draw every streamline transposed.
        collection = mikro.create_network_collection(
            version=f"v20260901-dti-streamlines-seed{SEED}",
            store=built,
            axes=list(COLLECTION_AXES),
            derived_from=[
                fa_ds.lens().derive(
                    input_axes=list(COLLECTION_AXES),
                    output_axes=list(COLLECTION_AXES),
                    value_relation=ValueRelation.TRANSFORMED,
                )
            ],
            provenance_metadata={
                "generator": "generator_tractography_network.py",
                "seed": SEED,
                "streamlines": len(objects),
            },
        )

        print("Attaching the per-streamline table…")
        table = mikro.create_table_dataset(
            name="DTI · streamline stats",
            data=streamline_stats,
            description="One row per streamline; object_id scopes into the collection.",
            columns=[
                ColumnInput(
                    name="object_id",
                    axis_type=AxisType.INDEX,
                    identified_by=[NetworkCollectionIdentifiesInput(network_collection=collection.id)],
                ),
                ColumnInput(name="bundle", role=ColumnRole.LABEL, long_name="bundle"),
                ColumnInput(name="n_points", role=ColumnRole.ATTRIBUTE),
                ColumnInput(name="length_mm", role=ColumnRole.ATTRIBUTE, long_name="length (mm)"),
                ColumnInput(name="mean_fa", role=ColumnRole.ATTRIBUTE, long_name="mean FA"),
            ],
        )

        network_layer = mikro.create_network_layer(
            scene=scene.id,
            network_collection=collection.id,
            material_color=[255, 200, 80, 255],
            show_nodes=False,  # streamlines are their segments; node glyphs are noise here
            directed=False,
            opacity=0.95,
            order=2,
            color_bys=[
                graph_color_by("fa", colormap=ColorMap.INFERNO, min=0.0, max=1.0,
                               label="FA (per point)"),
                graph_color_by("radius", label="Calibre"),
                measure_color_by(table.id, "mean_fa", colormap=ColorMap.VIRIDIS, min=0.0,
                                 max=1.0, label="Mean FA (per streamline)"),
                measure_color_by(table.id, "length_mm", colormap=ColorMap.PLASMA, min=0.0,
                                 max=float(streamline_stats["length_mm"].max()),
                                 label="Streamline length"),
            ],
            active_color_by=0,
            filter_bys=[
                graph_filter_by("fa", min=0.5, label="High-FA cores"),
                network_filter_by(table.id, "length_mm",
                                  min=float(streamline_stats["length_mm"].median()),
                                  label="Long streamlines"),
            ],
        )
        if network_layer.placement != PlacementState.PLACED:
            raise SystemExit(f"the streamlines did not reach the world: {network_layer.placement}")
        published = network_layer.network_color_bys
        if len(published) != 4:
            raise SystemExit(f"layer offers {len(published)} colourings, expected 4")

        print("Uploading glass brain…")
        built_mesh = build_collection({1: mesh}, levels=LEVELS)
        mesh_collection = mikro.create_mesh_collection(
            version=f"v20260901-dti-glass-brain-network-seed{SEED}",
            store=built_mesh,
            axes=[AxisInput(name=d, type=AxisType.SPACE) for d in COLLECTION_AXES],
            derived_from=[
                fa_ds.lens().derive(
                    input_axes=list(COLLECTION_AXES),
                    output_axes=list(COLLECTION_AXES),
                    value_relation=ValueRelation.TRANSFORMED,
                )
            ],
        )
        mesh_layer = mikro.create_mesh_layer(
            scene=scene.id,
            mesh_collection=mesh_collection.id,
            material_color=[205, 215, 255, 255],
            wireframe=False,
            opacity=0.18,
            order=1,
        )
        if mesh_layer.placement != PlacementState.PLACED:
            raise SystemExit(f"glass brain did not reach the world: {mesh_layer.placement}")

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  FA {fa_ds.id}, streamline collection {collection.id} "
              f"({len(objects)} objects), layer {network_layer.id}")
        print(f"  stats table {table.id}, glass brain {mesh_collection.id}")
