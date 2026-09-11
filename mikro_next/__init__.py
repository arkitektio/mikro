"""mikro-next: the image and dataset client for arkitekt."""

import logging

from kanne.scalars import Unit

from .compression import DEFAULT_COMPRESSION, MESH_CODECS, TABLE_CODECS, UnreadableCodecError
from .mikro_next import MikroNext
from .pyramid import axes_for, build_pyramid, canonical, dataset_arrays, scales_from
from .spaces import create_space, space_2d, space_3d, timelapse_3d
from .sparse import SparseDeclarationError
from .tables import TableDeclarationError
from .utils import rechunk
from .vocabulary import (
    AxisSelection,
    AxisTypeName,
    Calibration,
    ColumnRoleName,
    Reduction,
    TransformKind,
    default_axis_type,
    duckdb_type,
)

logger = logging.getLogger(__name__)

__all__ = [
    "MikroNext",
    "axes_for",
    "build_pyramid",
    "canonical",
    "dataset_arrays",
    "scales_from",
    "create_space",
    "space_2d",
    "space_3d",
    "timelapse_3d",
    "rechunk",
    # The declaration a caller writes against is the generated `ColumnInput`;
    # what lives here is the refusal it can raise and the codec vocabulary,
    # which is this client's own and stated nowhere else.
    "SparseDeclarationError",
    "TableDeclarationError",
    "UnreadableCodecError",
    "DEFAULT_COMPRESSION",
    "TABLE_CODECS",
    "MESH_CODECS",
    # The vocabularies a caller writes against. `ChannelSpec` is deliberately not
    # here: `render` imports the generated schema at module level, and pulling
    # that into every `import mikro_next` is what `pyramid` and `spaces` avoid
    # with function-local imports. Reach for `from mikro_next.render import ...`.
    "AxisSelection",
    "AxisTypeName",
    "Calibration",
    "ColumnRoleName",
    "Reduction",
    "Unit",
    "TransformKind",
    "default_axis_type",
    "duckdb_type",
]

# Both of these are optional: `arkitekt-next` and `rekuest-next` are dev
# dependencies, not install requirements. A name that did not import must stay
# out of `__all__` as well, or `from mikro_next import *` raises on a perfectly
# valid install. (`mikro_next.specs` is unexported for the same reason — it
# imports `rekuest_next.annotations` at module level.)
try:
    from .arkitekt import MikroService as MikroService
except ImportError as e:
    try:
        import arkitekt_next  # noqa: F401 — presence is the question

        raise ImportError(
            "Arkitekt is installed, but the MikroService could not be imported. This may indicate a version mismatch or missing dependencies."
        ) from e
    except ImportError:
        pass
else:
    __all__.append("MikroService")


try:
    from .rekuest import structure_reg as structure_reg

except ImportError as e:
    try:
        import rekuest_next  # noqa: F401 — presence is the question

        raise ImportError(
            "Rekuest is installed, but the structure_reg could not be imported. This may indicate a version mismatch or missing dependencies."
        ) from e
    except ImportError:
        pass
else:
    __all__.append("structure_reg")
