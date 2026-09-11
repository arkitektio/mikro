"""A synthetic single-particle-tracking acquisition — trajectories as a TrackLayer.

The sibling of ``generator_smlm.py``: where SMLM's emitters blink in place, these
particles *move*, and the deliverable is the trajectory rather than the position.

Three artifacts over one ground truth:

- the **track table**: one row per particle per frame, with a ``t`` TIME axis column
  in seconds, ``(y, x)`` SPACE columns in micrometers, and a TRACK_ID column grouping
  rows into trajectories — the three declarations `createTrackLayer` requires,
- a **track layer** drawing that table as one polyline per track, colored by the
  per-row instantaneous speed. The trajectory is the table's declaration: the layer
  derives its track/coordinate/time columns, it only styles them. The ``t`` axis
  column is load-bearing — the renderer orders rows by ``(track_id, t)``, and a time
  column named anything else would leave the draw at the mercy of row order,
- the **raw camera movie** ``(t, y, x)``: the diffusing spots the tracker would have
  linked, at 100 nm pixels.

Three motion populations, 8 particles each: slow Brownian, fast Brownian, and
directed transport (a motor-driven run that ends where it hits the field edge —
which also keeps its drift check clean of reflections). The Brownian particles
reflect. The field is non-square (12 x 18 µm) so a y/x transpose fails loudly.

Deterministic — fixed seed, no network beyond the upload. Run `--dry-run` first.

Run:  python generator_spt.py [--dry-run]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
import xarray as xr

from mikro import Unit, create_space, dataset_arrays
from arkitekt_next import easy
from mikro.api.schema import (
    AxisType,
    ColorMap,
    ColumnInput,
    ColumnRole,
    CoordinateAnchorInput,
    ProjectionMode,
    create_array_dataset,
    create_layer,
    create_lens,
    create_scene,
    create_table_dataset,
    create_track_layer,
)
from mikro.render import channel_graph

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
SEED = 31
RNG = np.random.default_rng(SEED)

CAM_SHAPE = (120, 180)  # (y, x) pixels, deliberately non-square
CAM_PX = 0.1  # µm per camera pixel
FIELD = (CAM_SHAPE[0] * CAM_PX, CAM_SHAPE[1] * CAM_PX)  # (12, 18) µm

FRAMES = 200
EXPOSURE = 0.05  # seconds per frame

PSF_SIGMA = 1.3 * CAM_PX  # µm
PHOTON_MEAN = 1500.0
BACKGROUND = 100.0
LOC_SIGMA = 0.015  # µm of localization error on every observation

MARGIN = 1.0  # µm the Brownian walkers reflect at; directed runs *end* there

# The three populations: (name, diffusion D in µm²/s, drift speed in µm/s).
POPULATIONS = (
    ("slow", 0.010, 0.0),
    ("fast", 0.080, 0.0),
    ("directed", 0.005, 1.5),
)
PER_POPULATION = 8
MIN_LIFETIME = 40  # frames a track must last to be worth linking


# --------------------------------------------------------------------------- #
# Ground truth: three kinds of walker
# --------------------------------------------------------------------------- #
def simulate() -> list[dict]:
    """Every particle's true path — a list of dicts with positions ``(n, 2)`` (y, x)
    in µm, the frame range it is alive, and its population.

    Brownian steps are N(0, sqrt(2 D dt)) per axis; a directed particle adds a
    constant drift v*dt along a heading drawn once. Brownian walkers reflect at the
    margin; a directed run is truncated where it leaves it, so its recorded steps
    are pure drift + diffusion and the self-check below can hold its mean step to
    v*dt without reflection artifacts."""
    dt = EXPOSURE
    lo = np.array([MARGIN, MARGIN])
    hi = np.array(FIELD) - MARGIN

    particles = []
    track_id = 0
    for name, diffusion, drift_speed in POPULATIONS:
        step_sigma = np.sqrt(2.0 * diffusion * dt)
        for _ in range(PER_POPULATION):
            birth = int(RNG.integers(0, FRAMES - MIN_LIFETIME))
            death = int(RNG.integers(birth + MIN_LIFETIME, FRAMES + 1))

            # Directed particles start well inside and head across the field, so the
            # run has room; Brownian ones start anywhere legal.
            pos = lo + RNG.random(2) * (hi - lo)
            heading = RNG.uniform(0.0, 2 * np.pi)
            drift = drift_speed * dt * np.array([np.sin(heading), np.cos(heading)])

            path = [pos.copy()]
            for _ in range(birth + 1, death):
                pos = pos + drift + RNG.normal(0.0, step_sigma, size=2)
                if drift_speed > 0.0:
                    if (pos < lo).any() or (pos > hi).any():
                        break  # the run ends at the edge
                else:
                    # reflect
                    for axis in range(2):
                        if pos[axis] < lo[axis]:
                            pos[axis] = 2 * lo[axis] - pos[axis]
                        elif pos[axis] > hi[axis]:
                            pos[axis] = 2 * hi[axis] - pos[axis]
                path.append(pos.copy())

            if len(path) < MIN_LIFETIME:
                continue  # a directed run that died too young; rare, and fine
            particles.append(
                {
                    "track_id": track_id,
                    "population": name,
                    "diffusion": diffusion,
                    "drift": drift_speed,
                    "birth": birth,
                    "path": np.array(path),
                }
            )
            track_id += 1
    return particles


def observe(particles: list[dict]) -> pd.DataFrame:
    """The tracker's output: one row per particle per frame it was seen.

    The measured position is the true one plus localization noise; `speed` is the
    backward difference of the *measured* positions over dt — noisy exactly the way
    a real per-frame speed is. Rows are sorted by (track_id, t): the renderer orders
    by these columns anyway, and sorting the file puts row-group statistics on the
    hot filter column."""
    rows = []
    for particle in particles:
        n = len(particle["path"])
        measured = particle["path"] + RNG.normal(0.0, LOC_SIGMA, size=(n, 2))
        frames = particle["birth"] + np.arange(n)
        steps = np.linalg.norm(np.diff(measured, axis=0), axis=1) / EXPOSURE
        speed = np.concatenate([[steps[0]], steps]) if n > 1 else np.zeros(n)
        rows.append(
            pd.DataFrame(
                {
                    # Axis columns first, in (t, y, x) order — the file's column
                    # order IS the table's axis order.
                    "t": frames * EXPOSURE,
                    "y": measured[:, 0],
                    "x": measured[:, 1],
                    "track_id": np.full(n, particle["track_id"], dtype=np.int64),
                    "frame": frames.astype(np.int64),
                    "photons": RNG.lognormal(np.log(PHOTON_MEAN), 0.35, size=n),
                    "speed": speed,
                }
            )
        )
    table = pd.concat(rows, ignore_index=True)
    return table.sort_values(["track_id", "t"], ignore_index=True)


def raw_movie(obs: pd.DataFrame) -> xr.DataArray:
    """The camera's view: each observation a diffraction-limited Gaussian,
    ``(t, y, x)`` uint16 with Poisson noise over a flat background."""
    sigma_px = PSF_SIGMA / CAM_PX
    half = int(np.ceil(4 * sigma_px))
    win = np.arange(-half, half + 1, dtype=np.float64)

    movie = np.zeros((FRAMES, *CAM_SHAPE), dtype=np.float64)
    for frame, yc, xc, n_ph in zip(
        obs["frame"], obs["y"] / CAM_PX, obs["x"] / CAM_PX, obs["photons"]
    ):
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


# --------------------------------------------------------------------------- #
# Self-checks — the physics, the bookkeeping, and the transpose canary
# --------------------------------------------------------------------------- #
def check(particles: list[dict], obs: pd.DataFrame, movie: xr.DataArray) -> None:
    # The motion is what this dataset exists to show, so hold the *true* paths to
    # their own parameters: per-axis step std to sqrt(2 D dt) for the Brownian
    # populations, mean step vector to v*dt for the directed one (whose runs were
    # truncated at the edge precisely so this holds without reflection artifacts).
    for name, diffusion, drift_speed in POPULATIONS:
        steps = np.concatenate(
            [np.diff(p["path"], axis=0) for p in particles if p["population"] == name]
        )
        if drift_speed == 0.0:
            expected = np.sqrt(2.0 * diffusion * EXPOSURE)
            got = steps.std(axis=0)
            if not np.allclose(got, expected, rtol=0.25):
                raise SystemExit(
                    f"{name}: step std {got} vs expected {expected:.4f} — the walk is wrong"
                )
        else:
            # Per particle, not pooled: each run has its own heading, and step
            # vectors averaged across headings cancel toward zero.
            expected = drift_speed * EXPOSURE
            for p in (p for p in particles if p["population"] == name):
                got = float(np.linalg.norm(np.diff(p["path"], axis=0).mean(axis=0)))
                if abs(got - expected) > 0.25 * expected:
                    raise SystemExit(
                        f"{name} track {p['track_id']}: mean step {got:.4f} µm vs drift "
                        f"{expected:.4f} µm — the run is not running"
                    )

    if not (
        (obs[["y", "x"]] >= 0).all().all()
        and (obs["y"] < FIELD[0]).all()
        and (obs["x"] < FIELD[1]).all()
    ):
        raise SystemExit("observations fall outside the field — do not upload")

    # The renderer orders by (track_id, t); the file claims to be sorted that way
    # already, and a duplicated t within a track would make the path ambiguous.
    per_track = obs.groupby("track_id")["t"]
    if not (per_track.apply(lambda s: s.is_monotonic_increasing and s.is_unique)).all():
        raise SystemExit("a track's t column is not strictly increasing — do not upload")

    if movie.shape != (FRAMES, *CAM_SHAPE):
        raise SystemExit(f"movie is {movie.shape}, expected {(FRAMES, *CAM_SHAPE)} — transposed?")

    at_obs = movie.values[
        obs["frame"],
        np.minimum((obs["y"] / CAM_PX).astype(int), CAM_SHAPE[0] - 1),
        np.minimum((obs["x"] / CAM_PX).astype(int), CAM_SHAPE[1] - 1),
    ].mean()
    if at_obs < BACKGROUND * 1.5:
        raise SystemExit(
            f"particle pixels average {at_obs:.1f} vs background {BACKGROUND} — "
            f"the movie and the table disagree, do not upload"
        )

    n_tracks = obs["track_id"].nunique()
    print(
        f"  checks pass: {n_tracks} tracks / {len(obs)} observations, motion holds "
        f"per population, particle pixels at {at_obs:.0f} counts over {BACKGROUND:.0f}"
    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv

    print(f"Simulating walkers ({FIELD[0]:.0f}x{FIELD[1]:.0f} µm field, {FRAMES} frames)…")
    particles = simulate()
    obs = observe(particles)
    print(
        f"  {len(particles)} tracks ({', '.join(f'{n} {name}' for name, n in obs.merge(pd.DataFrame(particles)[['track_id', 'population']], on='track_id').groupby('population')['track_id'].nunique().items())}), "
        f"{len(obs)} observations"
    )

    print("Rendering the raw movie…")
    movie = raw_movie(obs)
    print(f"  raw {movie.shape} {movie.dtype} (~{movie.nbytes / 1e6:.0f} MB)")

    check(particles, obs, movie)

    if dry_run:
        print("Dry run: everything local checks out, nothing uploaded.")
        raise SystemExit(0)

    # Reusing a sibling generator's cached grant (see generator_smlm.py).
    with easy(identifier="neuron-overlay") as app:
        world = create_space(
            "SPT · field",
            {"t": Unit("second"), "y": Unit("micrometer"), "x": Unit("micrometer")},
        )

        print("Uploading raw movie…")
        raw_data, raw_scales = dataset_arrays(movie, levels=3, method="max")
        raw_ds = create_array_dataset(
            data=raw_data,
            scales=raw_scales,
            name="SPT · raw particle movie",
            axes=["t", "y", "x"],
            anchors=[CoordinateAnchorInput.histogram_anchor(movie)],
        )
        world.register(raw_ds, scale={"t": EXPOSURE, "y": CAM_PX, "x": CAM_PX})

        print("Uploading track table…")
        table = create_table_dataset(
            name="SPT · tracks",
            data=obs,
            description=(
                f"Synthetic single-particle tracks (generator_spt.py, seed {SEED}): "
                f"{obs['track_id'].nunique()} trajectories over {FRAMES} frames — "
                f"slow/fast Brownian and directed transport."
            ),
            columns=[
                # The axis columns, in (t, y, x) file order. `t` by that exact name:
                # the layer's derived tColumn matches a COORDINATE column literally
                # named 't', and it is what the renderer orders each track by.
                ColumnInput(name="t", axis_type=AxisType.TIME, unit="second"),
                ColumnInput(name="y", axis_type=AxisType.SPACE, unit="micrometer"),
                ColumnInput(name="x", axis_type=AxisType.SPACE, unit="micrometer"),
                # TRACK_ID, not GROUP_ID: these rows have an order — they are a path.
                ColumnInput(name="track_id", role=ColumnRole.TRACK_ID, long_name="trajectory"),
                ColumnInput(name="frame", role=ColumnRole.ATTRIBUTE, long_name="camera frame index"),
                ColumnInput(name="photons", role=ColumnRole.ATTRIBUTE, long_name="photon count"),
                ColumnInput(
                    name="speed",
                    role=ColumnRole.ATTRIBUTE,
                    long_name="instantaneous speed (µm/s)",
                ),
            ],
        )
        # The route createTrackLayer's placeability check walks — before the layer.
        world.register(table)

        print("Composing the scene…")
        scene = create_scene(name="SPT · synthetic", coordinate_system=world.id)

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

        track_layer = create_track_layer(
            scene=scene,
            table_dataset=table,
            color_by_column="speed",
            colormap=ColorMap.VIRIDIS,
            line_width=0.05,  # scene units = µm
            opacity=0.9,
            order=1,
        )

        # All four trajectory columns are derived from the table's declaration,
        # never stored — their coming back named is the round-trip proof.
        derived = (
            track_layer.track_id_column,
            track_layer.t_column,
            track_layer.y_column,
            track_layer.x_column,
        )
        if derived != ("track_id", "t", "y", "x"):
            raise SystemExit(
                f"track layer derived {derived} instead of ('track_id', 't', 'y', 'x') — "
                f"the table declaration did not land"
            )

        print(f"\nDone — scene '{scene.name}' ({scene.id}):")
        print(f"  raw movie  : dataset {raw_ds.id} ({FRAMES} frames)")
        print(f"  table      : {table.id} ({obs['track_id'].nunique()} tracks, {len(obs)} rows)")
        print(f"  track layer: {track_layer.id} (colored by speed)")
