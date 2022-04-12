---
sidebar_label: traits
title: traits
---

Traits for Mikro.

Traits are mixins that are added to every graphql type that exists on the mikro schema.
We use them to add functionality to the graphql types that extend from the base type.

Every GraphQL Model on Mikro gets a identifier and shrinking methods to ensure the compatibliity
with arkitekt. This is done by adding the identifier and the shrinking methods to the graphql type.
If you want to add your own traits to the graphql type, you can do so by adding them in the graphql
.config.yaml file.

## Representation Objects

```python
class Representation(BaseModel, ShrinkByID)
```

Representation Trait

Implements both identifier and shrinking methods.
Also Implements the data attribute

**Attributes**:

- `data` _xarray.Dataset_ - The data of the representation.

#### data

```python
@property
def data() -> xr.DataArray
```

The Data of the Representation as an xr.DataArray

**Returns**:

- `xr.DataArray` - The associated object.
  

**Raises**:

- `AssertionError` - If the representation has no store attribute quries

## ROI Objects

```python
class ROI(BaseModel, ShrinkByID)
```

Additional Methods for ROI

#### get\_identifier

```python
@classmethod
def get_identifier(cls)
```

THis classes identifier on the platform

#### ashrink

```python
async def ashrink()
```

Shrinks this to a unique identifier on
the mikro server

**Returns**:

- `str` - The unique identifier

#### vector\_data

```python
@property
def vector_data() -> np.ndarray
```

A numpy array of the vectors of the ROI

**Returns**:

- `np.ndarray` - _description_

## Table Objects

```python
class Table(BaseModel, ShrinkByID)
```

Table Trait

Implements both identifier and shrinking methods.
Also Implements the data attribute

**Attributes**:

- `data` _pd.DataFrame_ - The data of the table.

#### data

```python
@property
def data() -> pd.DataFrame
```

The data of this table as a pandas dataframe

**Returns**:

- `pd.DataFrame` - The Dataframe

## Vectorizable Objects

```python
class Vectorizable()
```

#### list\_from\_numpyarray

```python
@classmethod
def list_from_numpyarray(cls: T, x: np.ndarray) -> List[T]
```

Creates a list of InputVector from a numpya array

**Arguments**:

- `vector_list` _List[List[float]]_ - A list of lists of floats
  

**Returns**:

- `List[Vectorizable]` - A list of InputVector

