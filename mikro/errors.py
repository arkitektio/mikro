class MikroError(Exception):
    """Base class for all Mikro errors."""


class NoMikroFound(MikroError):
    """Caused when no Mikro is found."""


