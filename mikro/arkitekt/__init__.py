"""mikro for an arkitekt app: its service, the types it sends by id, and the spec types.

- :mod:`mikro.arkitekt.service` declares the service and the structures. An app takes
  all of it in with ``App(services=[mikro_service])``.
- :mod:`mikro.arkitekt.specs` holds the types to put in an action's signature
  (``Volume``, ``SingleChannelImage``, ...).
"""

from mikro.arkitekt.service import mikro, registry

__all__ = ["mikro", "registry"]
