import json
from pathlib import Path
from typing import Any

from arkitekt_next.service_registry import (
    BaseArkitektService,
    Params,
    get_default_service_registry,
)
from fakts_next import Fakts
from fakts_next.contrib.rath.aiohttp import FaktsAIOHttpLink
from fakts_next.contrib.rath.auth import FaktsAuthLink
from fakts_next.contrib.rath.graphql_ws import FaktsGraphQLWSLink
from fakts_next.models import Requirement
from rath.links.compose import compose
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.split import SplitLink
from rekuest_next.links.context import ContextLink

from graphql import OperationType
from mikro_next.contrib.fakts.datalayer import FaktsDataLayer
from mikro_next.middleware.upload import UploadMiddleware
from mikro_next.mikro_next import MikroNext
from mikro_next.rath import MikroNextRath


def build_relative_path(*path: str) -> str:
    """Builds a relative path to the given path components, starting from the
    directory of this file. This is useful for building paths to files that are"""
    return str(Path(__file__).parent.joinpath(*path))


class MikroService(BaseArkitektService):
    """A service that allows you to connect to a MikroNext instance within your
    Arkitekt Application. This service will allow you to make requests to the"""

    def get_service_name(self) -> str:
        """Returns the name of the service."""
        return "mikro"

    def build_service(self, fakts: Fakts, params: Params) -> MikroNext:
        """Builds the MikroNext service with the given parameters.
        Args:
            fakts (Fakts): The Fakts instance to use for the service.
            params (Params): The parameters for the service.
        Returns:
            MikroNext: An instance of MikroNext with the configured links.
        """
        datalayer = FaktsDataLayer(fakts_group="s3", fakts=fakts)

        return MikroNext(
            rath=MikroNextRath(
                link=compose(
                    FileExtraction(),
                    DictingLink(),
                    ContextLink(),
                    FaktsAuthLink(
                        fakts=fakts,
                    ),
                    SplitLink(
                        left=FaktsAIOHttpLink(
                            fakts_group="mikro",
                            fakts=fakts,
                            endpoint_url="FAKE_URL",
                        ),
                        right=FaktsGraphQLWSLink(
                            fakts_group="mikro",
                            fakts=fakts,
                            ws_endpoint_url="FAKE_URL",
                        ),
                        split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
                    ),
                ),
                middlewares=[
                    UploadMiddleware(datalayer=datalayer),
                ],
            ),
            datalayer=datalayer,
        )

    def get_requirements(self) -> list[Requirement]:
        """Returns a list of requirements for the Mikro service."""
        return [
            Requirement(
                key="mikro",
                service="live.arkitekt.mikro",
                description="An instance of ArkitektNext Mikro to make requests to the user's data",
                optional=False,
            ),
            Requirement(
                key="s3",
                service="live.arkitekt.s3",
                description="An instance of ArkitektNext Datalayer to make requests to the user's data",
                optional=False,
            ),
        ]

    def get_graphql_schema(self) -> str:
        """Returns the GraphQL schema for the Mikro service."""
        schema_graphql_path = build_relative_path("api", "schema.graphql")
        with open(schema_graphql_path) as f:
            return f.read()

    def get_turms_project(self) -> dict[str, Any]:
        """Returns the Turms project configuration for the Mikro service.

        This will be used to generate the Turms project configuration when
        autogenerating code for the graphql queries and mutations for the Mikro service.

        """
        turms_prject = build_relative_path("api", "project.json")
        with open(turms_prject) as f:
            return json.loads(f.read())


# Register the MikroService with the default service registry
get_default_service_registry().register(MikroService())
