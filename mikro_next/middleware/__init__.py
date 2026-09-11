"""Middleware for mikro_next funcs API.

Middleware intercepts operations before they reach the rath link chain,
enabling pre-processing of arguments (e.g., uploading arrays and files
to the datalayer) at the funcs level rather than deep in the link chain.
"""

from .base import FuncsMiddleware
from .upload import UploadMiddleware

__all__ = [
    "FuncsMiddleware",
    "UploadMiddleware",
]
