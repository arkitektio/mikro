"""The refusals a declaration can raise before its bytes move.

Each module checks one create path's declaration against the data it describes -- an array's
dims against its axes, a frame against its columns, a matrix against its axes -- and each is
called lazily from the trait on the generated input, so a refusal fires in ``Mikro.execute``
before the upload middleware runs. The server makes most of the same checks after the bytes
have landed; on a multi-gigabyte upload, before is the whole difference.
"""

from .arrays import ArrayDeclarationError
from .sparse import SparseDeclarationError
from .tables import TableDeclarationError

__all__ = ["ArrayDeclarationError", "SparseDeclarationError", "TableDeclarationError"]
