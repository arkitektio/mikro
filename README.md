# mikro

mikro is the python client for the mikro-server environment.

### Installation

```bash
pip install mikro
```

### Usage

```python
from mikro import from_xarray

data = xr.DataArray(np.zeros((1000,1000,10), dims=["x","y","z"])

image = from_xarray(data, name="Zerod Image")

```

### Codegen

mikros api is heavily autogenerated from graphql operations and can therefore be easily extended through
custom graphql queries or mutations. just check out turms for that!
