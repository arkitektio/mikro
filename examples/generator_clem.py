"""A synthetic CLEM pair — EM and fluorescence joined by a real affine.

Correlative light-electron microscopy is the registration story told honestly: two
instruments image the SAME specimen on different grids, at different scales, and
*rotated* relative to each other — and the claim that aligns them is an edge of the
coordinate graph, not a resampling. This generator authors the repo's first
top-level AFFINE registration (everything before it was BY_DIMENSION scale +
translation; the converters only ever nested an affine inside BY_DIMENSION).

One ground truth, rendered twice:

- **EM** ``(y, x)`` at 5 nm/px: Voronoi "membranes" as dark ridges, elliptical
  "mitochondria" darker still, grain everywhere,
- **LM**, two single-channel ``(y, x)`` datasets at 80 nm/px — a mito marker and a
  diffuse cytoplasm stain — acquired **rotated 7° and shifted** against the EM
  frame. Each LM pixel is rendered by pushing its centre through that transform and
  sampling the ground truth there, so the alignment is physically real. Two
  datasets rather than one ``(c, y, x)``, because a top-level AFFINE acts
  positionally on every axis of its input system: a channel axis has no business
  inside a rigid transform, and splitting the channels is the shape that says so.
- **Fiducials**: 8 beads visible in both modalities, as a table + point layer in
  world coordinates — the visual proof of the registration.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first.

Run:  python generator_clem.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import gaussian_filter

from mikro import Unit, space_2d, dataset_arrays
from arkitekt import easy
from mikro.api.schema import (
    AxisType,
    Blending,
    ColorMap,
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
SEED = 73
RNG = np.random.default_rng(SEED)

EM_SHAPE = (1800, 2400)  # (y, x) px, deliberately non-square
EM_PX = 0.005  # 5 nm
EM_FIELD = (EM_SHAPE[0] * EM_PX, EM_SHAPE[1] * EM_PX)  # (9, 12) µm

LM_SHAPE = (220, 300)  # (y, x) px
LM_PX = 0.08  # 80 nm
LM_PSF_UM = 0.15

# The acquisition offset the registration has to state: the LM frame is rotated
# and shifted against the EM/world frame.
THETA_DEG = 7.0
LM_ORIGIN_UM = (-2.0, -1.5)  # world position of LM pixel (0, 0)

N_MEMBRANE_SEEDS = 26
N_MITO = 22
MITO_R_UM = (0.25, 0.55)
N_FIDUCIALS = 8

EM_LEVELS = 4


# --------------------------------------------------------------------------- #
# The transform: LM pixel indices -> world micrometers
# --------------------------------------------------------------------------- #
def lm_affine() -> np.ndarray:
    """The 2x3 matrix taking an LM pixel (y, x, 1) into world (y, x) µm.

    Rows outermost and positional against (y, x) — the exact shape
    ``TransformInput.affine`` documents ("M x (N+1), rows outermost")."""
    theta = np.deg2rad(THETA_DEG)
    c, s = np.cos(theta), np.sin(theta)
    return np.array(
        [
            [LM_PX * c, -LM_PX * s, LM_ORIGIN_UM[0]],
            [LM_PX * s, LM_PX * c, LM_ORIGIN_UM[1]],
        ]
    )


def lm_pixel_world_coords(affine: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """World (y, x) µm of every LM pixel centre — two ``LM_SHAPE`` arrays."""
    yy, xx = np.mgrid[0 : LM_SHAPE[0], 0 : LM_SHAPE[1]].astype(np.float64)
    wy = affine[0, 0] * yy + affine[0, 1] * xx + affine[0, 2]
    wx = affine[1, 0] * yy + affine[1, 1] * xx + affine[1, 2]
    return wy, wx


# --------------------------------------------------------------------------- #
# Ground truth, as functions over world coordinates
# --------------------------------------------------------------------------- #
def make_truth():
    """The specimen: membrane seeds, mitochondria ellipses, fiducial beads.

    Everything is defined in world micrometers so both instruments can sample it —
    which is the entire premise of CLEM."""
    seeds = np.column_stack(
        [RNG.uniform(0, EM_FIELD[0], N_MEMBRANE_SEEDS), RNG.uniform(0, EM_FIELD[1], N_MEMBRANE_SEEDS)]
    )
    mitos = [
        {
            "cy": RNG.uniform(0.8, EM_FIELD[0] - 0.8),
            "cx": RNG.uniform(0.8, EM_FIELD[1] - 0.8),
            "ry": RNG.uniform(*MITO_R_UM),
            "rx": RNG.uniform(*MITO_R_UM) * RNG.uniform(1.2, 2.2),
            "angle": RNG.uniform(0, np.pi),
        }
        for _ in range(N_MITO)
    ]
    fiducials = np.column_stack(
        [RNG.uniform(1.0, EM_FIELD[0] - 1.0, N_FIDUCIALS), RNG.uniform(1.0, EM_FIELD[1] - 1.0, N_FIDUCIALS)]
    )
    return seeds, mitos, fiducials


def membrane_ridge(wy: np.ndarray, wx: np.ndarray, seeds: np.ndarray) -> np.ndarray:
    """Closeness to a Voronoi ridge in [0, 1]: 1 on the boundary between two
    nearest seeds, falling off with (d2 - d1)."""
    d1 = np.full(wy.shape, np.inf)
    d2 = np.full(wy.shape, np.inf)
    for sy, sx in seeds:
        d = np.hypot(wy - sy, wx - sx)
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        d1 = np.where(closer, d, d1)
    return np.exp(-(((d2 - d1) / 0.08) ** 2))


def mito_mask(wy: np.ndarray, wx: np.ndarray, mitos: list[dict]) -> np.ndarray:
    """Soft mitochondria occupancy in [0, 1]."""
    occ = np.zeros(wy.shape)
    for m in mitos:
        dy, dx = wy - m["cy"], wx - m["cx"]
        c, s = np.cos(m["angle"]), np.sin(m["angle"])
        u = (c * dy + s * dx) / m["ry"]
        v = (-s * dy + c * dx) / m["rx"]
        occ = np.maximum(occ, np.clip(1.2 - (u**2 + v**2), 0.0, 1.0))
    return np.clip(occ, 0.0, 1.0)


def bead_spots(wy: np.ndarray, wx: np.ndarray, fiducials: np.ndarray, sigma_um: float) -> np.ndarray:
    spots = np.zeros(wy.shape)
    for fy, fx in fiducials:
        spots += np.exp(-((wy - fy) ** 2 + (wx - fx) ** 2) / (2 * sigma_um**2))
    return spots


# --------------------------------------------------------------------------- #
# The two renders
# --------------------------------------------------------------------------- #
def render_em(seeds, mitos, fiducials) -> xr.DataArray:
    """The EM view: bright cytoplasm, dark membranes, darker textured mitochondria,
    and fiducial beads as small very dark disks."""
    yy, xx = np.mgrid[0 : EM_SHAPE[0], 0 : EM_SHAPE[1]].astype(np.float64)
    wy, wx = yy * EM_PX, xx * EM_PX

    image = np.full(EM_SHAPE, 190.0)
    image -= 120.0 * membrane_ridge(wy, wx, seeds)
    occ = mito_mask(wy, wx, mitos)
    image -= 70.0 * occ
    image += 18.0 * occ * RNG.standard_normal(EM_SHAPE)  # internal texture
    image -= 150.0 * np.clip(bead_spots(wy, wx, fiducials, 0.04), 0.0, 1.0)
    image += 8.0 * RNG.standard_normal(EM_SHAPE)  # grain
    return xr.DataArray(np.clip(image, 0, 255).astype(np.uint8), dims=("y", "x"), name="em")


def render_lm(affine, seeds, mitos, fiducials) -> tuple[xr.DataArray, xr.DataArray, np.ndarray]:
    """The LM view, channel by channel, each LM pixel sampled through the affine.

    Returns (mito channel, cyto channel, mito ground truth on the LM grid) — the
    truth array is what the cross-modal self-check correlates against."""
    wy, wx = lm_pixel_world_coords(affine)
    occ = mito_mask(wy, wx, mitos)
    beads = bead_spots(wy, wx, fiducials, 0.1)
    psf_px = LM_PSF_UM / LM_PX

    mito = gaussian_filter(2200.0 * occ + 3500.0 * beads, psf_px) + 60.0
    # Cytoplasm: everywhere the specimen is, fading at membranes, plus the beads.
    cyto = gaussian_filter(
        900.0 * (1.0 - 0.6 * membrane_ridge(wy, wx, seeds)) + 3500.0 * beads, psf_px
    ) + 60.0

    to_da = lambda a, name: xr.DataArray(
        RNG.poisson(a).astype(np.uint16), dims=("y", "x"), name=name
    )
    return to_da(mito, "lm_mito"), to_da(cyto, "lm_cyto"), occ


# --------------------------------------------------------------------------- #
# Self-checks
# --------------------------------------------------------------------------- #
def check(affine, em, lm_mito, lm_truth, fiducials) -> None:
    if em.shape != EM_SHAPE or lm_mito.shape != LM_SHAPE:
        raise SystemExit("a render came out the wrong shape — transposed?")

    # The affine must be a similarity at the LM pixel scale: |det| of its linear
    # part is the pixel area. A transposed or double-applied rotation breaks this.
    det = abs(float(np.linalg.det(affine[:, :2])))
    if abs(det - LM_PX**2) > 1e-12:
        raise SystemExit(f"|det| {det:.3e} != LM pixel area {LM_PX**2:.3e}")

    # Cross-modal content: the LM mito channel must BE the mito truth as seen
    # through the PSF — high correlation on the LM grid.
    corr = float(np.corrcoef(lm_mito.values.ravel().astype(float), lm_truth.ravel())[0, 1])
    if not corr >= 0.8:
        raise SystemExit(f"LM mito channel correlates {corr:.3f} < 0.8 with truth")

    # Round trip through the claim itself: each fiducial's world position, pushed
    # through the INVERSE affine into LM pixels and back through the affine, must
    # land where it started (numerical identity), and the inverse-mapped pixel
    # must actually be bright in the rendered channel.
    linear_inv = np.linalg.inv(affine[:, :2])
    for fy, fx in fiducials:
        py, px = linear_inv @ (np.array([fy, fx]) - affine[:, 2])
        if not (0 <= py < LM_SHAPE[0] and 0 <= px < LM_SHAPE[1]):
            continue  # a bead outside the LM field proves nothing either way
        back = affine[:, :2] @ np.array([py, px]) + affine[:, 2]
        if np.hypot(back[0] - fy, back[1] - fx) > 1e-9:
            raise SystemExit("affine round trip diverged — the matrix is inconsistent")
        neighbourhood = lm_mito.values[
            max(int(py) - 2, 0) : int(py) + 3, max(int(px) - 2, 0) : int(px) + 3
        ]
        if neighbourhood.max() < 500:
            raise SystemExit(
                f"fiducial at world ({fy:.2f}, {fx:.2f}) maps to LM ({py:.0f}, {px:.0f}) "
                f"but nothing is there — the render and the matrix disagree"
            )

    # And in EM: beads are dark holes at their world positions.
    for fy, fx in fiducials:
        iy, ix = int(round(fy / EM_PX)), int(round(fx / EM_PX))
        patch = em.values[max(iy - 4, 0) : iy + 5, max(ix - 4, 0) : ix + 5]
        if patch.min() > 120:
            raise SystemExit(f"no EM bead at world ({fy:.2f}, {fx:.2f})")

    print(f"  checks pass: |det| exact, LM/truth r = {corr:.2f}, all beads found in both modalities")


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Building the specimen ({EM_FIELD[0]:.0f}x{EM_FIELD[1]:.0f} µm)…")
    seeds, mitos, fiducials = make_truth()
    affine = lm_affine()

    print(f"Rendering EM ({EM_SHAPE[0]}x{EM_SHAPE[1]} @ {EM_PX * 1000:.0f} nm) "
          f"and LM ({LM_SHAPE[0]}x{LM_SHAPE[1]} @ {LM_PX * 1000:.0f} nm, {THETA_DEG:.0f}° rotated)…")
    em = render_em(seeds, mitos, fiducials)
    lm_mito, lm_cyto, lm_truth = render_lm(affine, seeds, mitos, fiducials)
    print(f"  EM {em.shape} {em.dtype} (~{em.nbytes / 1e6:.1f} MB), LM 2x {lm_mito.shape}")

    check(affine, em, lm_mito, lm_truth, fiducials)

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy(identifier="neuron-overlay") as app:
        world = space_2d("CLEM · specimen", unit=Unit("micrometer"))

        print("Uploading EM…")
        em_data, em_scales = dataset_arrays(em, levels=EM_LEVELS, method="mean")
        em_ds = create_array_dataset(
            data=em_data,
            scales=em_scales,
            name="CLEM · EM (5 nm)",
            axes=["y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(em)],
        )
        # The EM frame IS the world frame, up to its pixel size.
        world.register(em_ds, scale={"y": EM_PX, "x": EM_PX})

        print("Uploading LM channels…")
        lm_ids = []
        for arr, label in ((lm_mito, "mito marker"), (lm_cyto, "cytoplasm")):
            lm_ds = create_array_dataset(
                data=arr,
                scales=[],
                name=f"CLEM · LM {label} (80 nm)",
                axes=["y", "x"],
                anchors=[CoordinateAnchorInput.histogram_anchor(arr)],
            )
            # The load-bearing edge: a single top-level AFFINE from the LM pixel
            # grid into the world — rotation, pixel scale and stage offset as ONE
            # claim, exactly what a CLEM registration is.
            edge = lm_ds.intrinsic_system.transform_to(
                world,
                affine=[[float(v) for v in row] for row in affine],
                name=f"LM {label} -> specimen ({THETA_DEG:.0f}°)",
            )
            if edge is None:
                raise SystemExit(f"the AFFINE edge for '{label}' did not come back")
            lm_ids.append(lm_ds)

        print("Uploading fiducials…")
        beads = create_table_dataset(
            name="CLEM · fiducials",
            data=pd.DataFrame({"y": fiducials[:, 0], "x": fiducials[:, 1],
                               "bead": np.arange(1, N_FIDUCIALS + 1, dtype=np.int64)}),
            description="Bead positions in specimen micrometers, visible in both modalities.",
            columns=[
                ColumnInput(name="y", axis_type=AxisType.SPACE, unit="micrometer"),
                ColumnInput(name="x", axis_type=AxisType.SPACE, unit="micrometer"),
                ColumnInput(name="bead", role=ColumnRole.ID, long_name="bead"),
            ],
        )
        world.register(beads)

        print("Composing the scene…")
        scene = create_scene(name="CLEM · synthetic", coordinate_system=world.id)

        create_intensity_layer(
            lens=em_ds.lens(), scene=scene, colormap=ColorMap.GREY,
            clim_min=0.0, clim_max=255.0, blending=Blending.NORMAL, order=0,
        )
        for order, (lm_ds, colormap) in enumerate(zip(lm_ids, (ColorMap.GREEN, ColorMap.MAGENTA)), start=1):
            create_intensity_layer(
                lens=lm_ds.lens(), scene=scene, colormap=colormap,
                clim_min=100.0, clim_max=float(np.percentile(lm_mito.values, 99.8)),
                blending=Blending.ADDITIVE, opacity=0.7, order=order,
            )
        point_layer = create_point_layer(
            scene=scene, table_dataset=beads, point_size=0.25, colormap=ColorMap.YELLOW,
            opacity=0.9, order=3,
        )
        if (point_layer.y_column, point_layer.x_column) != ("y", "x"):
            raise SystemExit("fiducial table declaration did not land")

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  EM {em_ds.id}, LM {', '.join(d.id for d in lm_ids)} (AFFINE-registered, {THETA_DEG:.0f}°)")
        print(f"  fiducials table {beads.id}, point layer {point_layer.id}")
