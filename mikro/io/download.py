from mikro.api.schema import (
    RequestQueryRequest as Credentials,
    XArrayInput,
    BigFile,
    ParquetInput,
)
import uuid
import s3fs
import ntpath
from typing import Protocol, Any, runtime_checkable
from aiobotocore.session import get_session
import botocore
from pyarrow import Table
import pyarrow.parquet as pq
