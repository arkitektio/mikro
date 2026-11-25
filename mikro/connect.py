"""How ``Mikro`` reaches a resolved deployment: its links and upload middleware."""

from arkitekt_spec.declare.wiring import Alias, TokenLoader
from fakts.contrib.rath.auth import FaktsAuthLink
from rath.links.aiohttp import AIOHttpLink
from rath.links.compose import compose
from rath.links.dictinglink import DictingLink
from rath.links.file import FileExtraction
from rath.links.graphql_ws import GraphQLWSLink
from rath.links.split import SplitLink

from graphql import OperationType
from mikro.datalayer import DataLayer
from mikro.middleware.upload import UploadMiddleware
from mikro.rath import MikroRath


def mikro_rath(mikro: Alias, datalayer: DataLayer, tokens: TokenLoader) -> MikroRath:
    """The rath over http and ws, uploading files to ``datalayer`` first."""
    return MikroRath(
        link=compose(
            FileExtraction(),
            DictingLink(),
            FaktsAuthLink(token_loader=tokens),
            SplitLink(
                left=AIOHttpLink(
                    endpoint_url=mikro.to_http_path("graphql"),
                    proxy=mikro.proxy,
                    ssl_context=mikro.ssl_context(),
                ),
                right=GraphQLWSLink(
                    ws_endpoint_url=mikro.to_ws_path("graphql"),
                    proxy=mikro.proxy,
                    ssl_context=mikro.ssl_context(),
                ),
                split=lambda o: o.node.operation != OperationType.SUBSCRIPTION,
            ),
        ),
        middlewares=[UploadMiddleware(datalayer=datalayer)],
    )


__all__ = ["mikro_rath"]
