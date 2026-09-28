"""mikro: the image and dataset client for arkitekt."""

import logging

from kanne.scalars import Unit

from .checks import ArrayDeclarationError, SparseDeclarationError, TableDeclarationError
from .inputs.spaces import create_space, space_2d, space_3d, timelapse_3d
from .io.chunking import rechunk
from .mikro import Mikro
from .pyramid import axes_for, build_pyramid, canonical, dataset_arrays, scales_from
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
    "Mikro",
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
    # The declaration a caller writes against is the generated input; what lives
    # here is the refusal each create path can raise before its bytes move.
    "ArrayDeclarationError",
    "SparseDeclarationError",
    "TableDeclarationError",
    # The vocabularies a caller writes against. `ChannelSpec` is deliberately not
    # here: `inputs.render` imports the generated schema at module level, and
    # pulling that into every `import mikro` is what `pyramid` and `spaces` avoid
    # with function-local imports. Reach for `from mikro.inputs.render import ...`.
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

# The service is declared with arkitekt-spec, a core dependency: it is always there.
from .arkitekt import mikro as mikro_service  # noqa: E402

__all__ += ["mikro_service"]


