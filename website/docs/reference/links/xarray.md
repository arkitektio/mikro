---
sidebar_label: xarray
title: links.xarray
---

## DataLayerXArrayUploadLink Objects

```python
class DataLayerXArrayUploadLink(ParsingLink)
```

Data Layer Xarray Upload Link

This link is used to upload a Xarray to a DataLayer.
It parses queries, mutatoin and subscription arguments and
uploads the items to the DataLayer, and substitures the
XArray with the S3 path.

**Arguments**:

- `ParsingLink` __type__ - _description_
  

**Attributes**:

- `FileVersion` _str_ - The version of the file format.

#### \_\_aenter\_\_

```python
async def __aenter__() -> None
```

Enter the executor

