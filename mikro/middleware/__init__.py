"""Middleware for mikro's operations.

Middleware intercepts operations before they reach the rath link chain,
enabling pre-processing of arguments (e.g., uploading arrays and files
to the datalayer) at the operation level rather than deep in the link chain.
"""

from .base import OperationMiddleware
from .upload import UploadMiddleware

__all__ = [
    "OperationMiddleware",
    "UploadMiddleware",
]
