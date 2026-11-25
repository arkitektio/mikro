"""Run every example generator end-to-end against the dokker stack.

The scripts in ``examples/`` are not importable libraries -- each is a
``__main__``-guarded program that generates a synthetic dataset, checks its own
ground truth, uploads it, and then asserts the round trip (layer kinds,
placements, colorBys). Those built-in assertions ARE the test; this module only
supplies what ``connect(Mikro)`` would have supplied and lets each script run.

What the harness substitutes:

- ``arkitekt.connect`` is replaced with a stub that yields the deployment's client,
  which the scripts then call every operation on.
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
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from pathlib import Path

import pytest

from .conftest import DeployedMikro

# The example scripts are arkitekt apps -- they do `from arkitekt import connect`,
# and the harness below stubs that out. mikro cannot depend on arkitekt to get
# it: arkitekt depends on mikro, so declaring it here would close a cycle. So
# these run wherever arkitekt happens to be importable (a dev checkout) and skip
# where it is not (mikro's own CI), the same way alpaka guards its rekuest tests.
pytest.importorskip("arkitekt", reason="the example scripts are arkitekt apps")

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
    "generator_cell_morphology.py",
]


def _stub_connect_for(
    mikro: object,
) -> Callable[..., AbstractContextManager[object]]:
    @contextmanager
    def _stub_connect(*clients: type, **options: object) -> Iterator[object]:
        """Stand-in for ``arkitekt.connect(Mikro)``: the deployment's client."""
        assert len(clients) == 1, "the examples connect only Mikro"
        yield mikro

    return _stub_connect


@pytest.mark.integration
@pytest.mark.parametrize("script", SCRIPTS)
def test_example_uploads(
    deployed_app: DeployedMikro, script: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The scripts do `with connect(Mikro, ...) as mikro:`; the stub hands them the
    # deployment's client instead. They bind `connect` when they run, after this patch.
    import arkitekt

    monkeypatch.setattr(arkitekt, "connect", _stub_connect_for(deployed_app.mikro))
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
