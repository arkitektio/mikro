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
class Representation()
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

## Table Objects

```python
class Table()
```

Table Trait

Implements both identifier and shrinking methods.
Also Implements the data attribute

**Attributes**:

- `data` _pd.DataFrame_ - The data of the table.

