---
sidebar_label: parquet
title: links.parquet
---

## DataLayerParquetUploadLink Objects

```python
class DataLayerParquetUploadLink(ParsingLink)
```

Data Layer Parquet Upload Link

This link is used to upload a DataFrame to a DataLayer.
It parses queries, mutatoin and subscription arguments and
uploads the items to the DataLayer, and substitures the
DataFrame with the S3 path.

**Arguments**:

- `ParsingLink` __type__ - _description_

#### store\_df

```python
def store_df(df: pd.DataFrame) -> None
```

Store a DataFrame in the DataLayer

#### aparse

```python
async def aparse(operation: Operation) -> Operation
```

Parse the operation (Async)

Extracts the DataFrame from the operation and uploads it to the DataLayer.

**Arguments**:

- `operation` _Operation_ - The operation to parse
  

**Returns**:

- `Operation` - _description_

#### \_\_aenter\_\_

```python
async def __aenter__() -> None
```

Enter the executor

