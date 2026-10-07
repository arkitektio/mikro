import os
import sys
from collections.abc import Generator
from dataclasses import dataclass

import pytest
from dokker import Deployment
from dokker.log_watcher import LogWatcher

from mikro.mikro import Mikro

from .stack import MikroStack, start_mikro


def pytest_configure(config: pytest.Config) -> None:
    """Register custom platform markers."""
    config.addinivalue_line("markers", "linux_only: skip on non-Linux platforms")
    config.addinivalue_line("markers", "no_windows: skip on Windows")


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Skip tests marked linux_only or no_windows on the wrong platform."""
    for item in items:
        if item.get_closest_marker("linux_only") and sys.platform != "linux":
            item.add_marker(pytest.mark.skip(reason="Linux only"))
        if item.get_closest_marker("no_windows") and sys.platform == "win32":
            item.add_marker(pytest.mark.skip(reason="Not supported on Windows"))


# An untracked sibling override (see its own header): when a developer's checkout sits next
# to a live mikro source tree, it mounts that tree over the published image so the tests
# see the current schema instead of the last-pushed one. Absent (CI, anyone else), the
# published image is the schema under test, as before.
_local_override = os.path.join(os.path.dirname(__file__), "integration", "docker-compose.local.yml")


@pytest.fixture(scope="session")
def mikro_stack() -> Generator[MikroStack, None, None]:
    """Mikro, started once for the test session."""
    with start_mikro([_local_override] if os.path.exists(_local_override) else []) as stack:
        yield stack


@dataclass
class DeployedMikro:
    """Dataclass to hold the deployed Mikro application and its components."""

    deployment: Deployment
    mikro_watcher: LogWatcher
    rustfs_watcher: LogWatcher
    mikro: Mikro


@pytest.fixture(scope="session")
def deployed_app(mikro_stack: MikroStack) -> Generator[DeployedMikro, None, None]:
    """The session's mikro stack, with one client entered for the whole session.

    Yields:
        DeployedMikro: An instance containing the deployment, watchers, and Mikro instance

    """
    with mikro_stack.client() as mikro:
        yield DeployedMikro(
            deployment=mikro_stack.deployment,
            mikro_watcher=mikro_stack.mikro_watcher,
            rustfs_watcher=mikro_stack.rustfs_watcher,
            mikro=mikro,
        )


@pytest.fixture(scope="session")
def mikro(deployed_app: DeployedMikro) -> Mikro:
    """The deployment's client: API calls are its methods, nothing is ambient."""
    return deployed_app.mikro
