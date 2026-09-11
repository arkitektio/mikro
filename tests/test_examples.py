"""Run every example generator end-to-end against the dokker stack.

The scripts in ``examples/`` are not importable libraries -- each is a
``__main__``-guarded program that generates a synthetic dataset, checks its own
ground truth, uploads it, and then asserts the round trip (layer kinds,
placements, colorBys). Those built-in assertions ARE the test; this module only
supplies what ``easy()`` would have supplied and lets each script run.

What the harness substitutes:

- ``arkitekt_next`` is replaced with a stub whose ``easy()`` yields nothing.
  The scripts only use ``easy`` to enter the mikro context; here the
  session-scoped ``deployed_app`` fixture has already entered
  ``current_mikro_rath`` (``with mikro as mikro:`` in conftest), so every
  bare ``create_*`` call inside the script lands on the test deployment. The
  stub is also load-bearing for a second reason: the real ``arkitekt_next`` in
  this venv does not import cleanly, so the scripts cannot even be loaded
  without it.
- ``sys.argv`` is pinned to the bare script name -- no ``--dry-run``, so the
  upload and read-back paths actually run.
- The examples directory goes on ``sys.path`` because
  ``generator_tractography_network`` imports its sibling
  ``generator_dti_tractography`` for the shared phantom.

Failure protocol: the scripts signal a failed self-check with
``raise SystemExit(<message>)`` and a clean dry-run with ``SystemExit(0)``, so
any exit code other than ``None``/``0`` is reported as a test failure carrying
the script's own message.

These runs are the first integration exercise of the mesh (fabriks), network
(konnektion) and sparse upload paths against a real server -- the extra buckets
in ``tests/integration/configs`` exist for them.
"""

import runpy
import sys
import types
from contextlib import contextmanager
from pathlib import Path

import pytest

from .conftest import DeployedMikro

EXAMPLES = Path(__file__).parent.parent / "examples"

# Explicit list rather than a glob: the suite should fail loudly when a new
# example is added without being wired in here (or an old one renamed).
# generator_dti_tractography must precede generator_tractography_network only
# in the sense that both must be present -- the latter imports the former as a
# module and rebuilds the phantom itself, so the tests stay independent.
SCRIPTS = [
    "generator_smlm.py",
    "generator_spt.py",
    "generator_hyperspectral.py",
    "generator_calcium.py",
    "generator_hcs_plate.py",
    "generator_clem.py",
    "generator_mri_multicontrast.py",
    "generator_fmri.py",
    "generator_dti_tractography.py",
    "generator_tractography_network.py",
]


@contextmanager
def _stub_easy(identifier: str | None = None, **kwargs: object):
    """Stand-in for ``arkitekt_next.easy``: the fixture already entered mikro."""
    yield None


@pytest.mark.integration
@pytest.mark.parametrize("script", SCRIPTS)
def test_example_uploads(
    deployed_app: DeployedMikro, script: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    stub = types.ModuleType("arkitekt_next")
    stub.easy = _stub_easy  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "arkitekt_next", stub)
    monkeypatch.setattr(sys, "argv", [script])
    monkeypatch.syspath_prepend(str(EXAMPLES))

    path = EXAMPLES / script
    assert path.exists(), f"example listed here but missing on disk: {path}"

    try:
        runpy.run_path(str(path), run_name="__main__")
    except SystemExit as stop:
        if stop.code not in (None, 0):
            pytest.fail(f"{script} refused its own scene: {stop.code}")


def test_every_example_is_listed() -> None:
    """A new example script must be added to SCRIPTS to be tested."""
    on_disk = sorted(p.name for p in EXAMPLES.glob("generator_*.py"))
    assert on_disk == sorted(SCRIPTS)
