class MikroError(Exception):
    """Base class for all Mikro errors."""


class NoMikroFound(MikroError):
    """Caused when no Mikro is found."""


class NoDataLayerFound(MikroError):
    """Caused when no DataLayer is found."""


class NotQueriedError(MikroError):
    """Caused when a field has not been queried."""
