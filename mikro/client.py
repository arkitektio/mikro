"""Which client a call on a mikro object goes through.

The one passed explicitly, else the one that fetched the object: every result
remembers its client (``Mikro._origin``), so a follow-up call from an object
reaches the same server, rath and datalayer that produced it. Nothing is looked up
in what happens to be current.
"""

from typing import TYPE_CHECKING, Any

from rath.origin import get_origin

from mikro.errors import NoMikroFound

if TYPE_CHECKING:
    from mikro.mikro import Mikro


def client_of(obj: Any, mikro: "Mikro | None" = None) -> "Mikro":  # noqa: ANN401
    """The client for a call on ``obj``: ``mikro`` if given, else the one that fetched it.

    Raises:
        NoMikroFound: If none was given and ``obj`` was not fetched through a
            client (built by hand, or unpickled: an origin does not travel).
    """
    if mikro is not None:
        return mikro

    from mikro.mikro import Mikro

    origin = get_origin(obj)
    client = origin.client if origin is not None else None
    if isinstance(client, Mikro):
        return client
    raise NoMikroFound(
        f"{type(obj).__name__} was not fetched through a Mikro client, so there is "
        "none to call through. Pass one explicitly (mikro=...)."
    )


__all__ = ["client_of"]
