# mikro

[![codecov](https://codecov.io/gh/arkitektio/mikro/graph/badge.svg?token=PRoouTwAGx)](https://codecov.io/gh/arkitektio/mikro)
[![PyPI version](https://badge.fury.io/py/mikro.svg)](https://pypi.org/project/mikro/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/mikro.svg)](https://pypi.python.org/pypi/mikro/)
[![PyPI download month](https://img.shields.io/pypi/dm/mikro.svg)](https://pypi.python.org/pypi/mikro/)

The Python client for mikro, the [Arkitekt](https://arkitekt.live) service for microscopy and
imaging data. mikro-server is a GraphQL server that keeps the metadata of your data (datasets,
folders, coordinate systems, scenes, and the relations between them), while the pixels live in
object storage as [Zarr](https://zarr.dev/) (and tables as Parquet). This client gives you both as
one: typed, validated Python objects built on [rath](https://github.com/jhnnsrs/rath) and pydantic,
whose `.data` is a lazy [xarray](https://docs.xarray.dev/) backed by dask. When you pass an array to a
mutation, mikro uploads it before the call runs, and when you read one back it downloads only the
chunks you touch.

## Installation

```bash
pip install mikro
```

mikro requires **Python 3.11+**. Extras bring in the heavier wire formats only when you need them:

| Extra | Brings in |
| --- | --- |
| `table` | pyarrow, pandas and duckdb, for querying Parquet-backed tables |
| `mesh` | `fabriks`, for uploading meshes |
| `network` | `konnektion`, for uploading graphs |
| `sparse` | `sporadik`, for sparse datasets |
| `complete` | all of the above |

Inside an arkitekt app, `pip install "arkitekt[rekuest,mikro]"` installs mikro along with arkitekt and the runtime `run(app)` needs.

## Usage

Every mikro operation is a method of the `Mikro` client. Each comes in a blocking and an
`a`-prefixed async flavour (`mikro.create_folder(...)`, `await mikro.acreate_folder(...)`). An object
that a call returns remembers the client that fetched it, so later calls on it, such as `.data`, go
through the same client.

### In an arkitekt app

Add `mikro_service` to your app and take the client by annotation. arkitekt injects it. Types from
`mikro.arkitekt.specs` such as `Volume` or `Image` are lenses over a mikro dataset. Each one declares
what an action needs, and the UI then offers only datasets that fit.

```python
from arkitekt import App, Task, run
from mikro import Mikro, mikro_service
from mikro.arkitekt.specs import Volume, ensure

app = App("clip-volume", "0.1.0", services=[mikro_service])


@app.action
def clip(volume: Volume, mikro: Mikro, task: Task) -> Volume:
    """Clip Volume

    Clips negative values and stores the result on the same grid.
    """
    source = volume.data  # a lazy xarray.DataArray
    task.progress(30, f"Processing {source.shape}")
    clipped = source.clip(min=0).compute()

    result = mikro.create_array_dataset(
        data=clipped,
        scales=[],
        name="clipped",
        axes=volume.carried_axes(clipped.dims),
        derived_from=[volume.derive_identity(value_relation="TRANSFORMED")],
    )
    return ensure(result.lens(), Volume)


if __name__ == "__main__":
    run(app)
```

Datasets, tables, meshes, annotations, lenses, coordinate systems, scenes, folders and files travel
between actions by id (`@mikro/arraydataset`, `@mikro/lens`, `@mikro/scene`, ...), so an action can
take them and return them directly.

### From a script

`easy` connects for you and returns the client:

```python
import numpy as np
import xarray as xr

from arkitekt import easy
from mikro import dataset_arrays, mikro_service

volume = xr.DataArray(np.random.random((2, 10, 256, 256)), dims=("c", "z", "y", "x"))

with easy("my-script", mikro_service) as mikro:
    folder = mikro.create_folder(name="examples")

    # `data` is level 0; `scales` holds only the coarser levels
    level_zero, scales = dataset_arrays(volume, levels=3)

    dataset = mikro.create_array_dataset(
        data=level_zero,
        scales=scales,
        name="random volume",
        axes=["c", "z", "y", "x"],
        folder=folder.id,
    )

    again = mikro.get_array_dataset(dataset.id)
    peak = again.data.max().compute()  # downloads only what it needs
```

Use `async with aeasy(...)` in async code, or `interactive("notebook", mikro_service)` in Jupyter.
Inside an async loop, remember that computing `.data` downloads the data in a blocking way on that
loop.

Declared axes are checked against the array **before** it is uploaded. For example, a rank mismatch
or a missing declaration raises `ArrayDeclarationError` (tables and sparse datasets have their own
errors) before any data is sent.

### A camera frame, and tiles that sit side by side

A frame straight off a camera is a bare array. Three things make it an image someone can look at:
labelled axes, contrast limits to draw it with, and a place in physical space.

```python
import numpy as np
import xarray as xr

from mikro import Unit, canonical, dataset_arrays, space_2d
from mikro.api.schema import CoordinateAnchorInput, ScenePolicyInput


def upload(mikro, frame: np.ndarray, name: str, space, x_um: float, y_um: float, pixel_um: float):
    # 1. Name the axes. `canonical` puts them in the order the server wants (c, y, x).
    image = canonical(xr.DataArray(frame, dims=("y", "x", "c")[: frame.ndim]))

    # 2. A pyramid, so a large frame opens at once, and one contrast anchor per channel.
    levels = max(1, min(4, int(np.log2(max(frame.shape[:2]) / 512)) + 1))
    level_zero, scales = dataset_arrays(image, levels=levels, method="mean")
    dataset = mikro.create_array_dataset(
        data=level_zero,
        scales=scales,
        name=name,
        axes=[str(d) for d in image.dims],
        anchors=CoordinateAnchorInput.histogram_anchors(image),
    )

    # 3. Where it is: pixel size as the scale, the stage position as the offset.
    space.register(dataset, scale={"y": pixel_um, "x": pixel_um}, x=x_um, y=y_um)
    return dataset


space = space_2d(mikro, "tile scan", unit=Unit("micrometer"))
for x_um, y_um, frame in tiles:
    upload(mikro, frame, f"tile {x_um:.0f} {y_um:.0f}", space, x_um, y_um, pixel_um=0.65)

# One scene over the space: every tile at its position.
space.stage(name="tile scan", policy=ScenePolicyInput(nchildren=len(tiles)))
```

Units and positions never go on the dataset: a physical space is a coordinate system of its own, and
`register` says where the data sits in it. Tiles registered into one space share one world, which is
what makes a viewer show them stitched by position. A single frame gets a space of its own the same
way.

`stage()` builds a scene from at most `nchildren` registered sources, **8 unless you say otherwise**.
A scan of more tiles than that needs the `policy` above, or the scene silently shows the first eight.

An action that returns the image returns a lens, not the dataset: `return dataset.lens()`.

### Working with data

```python
data = dataset.data               # level 0, a lazy dask-backed xarray.DataArray
coarse = dataset.level_data(2)    # a coarser pyramid level
levels = dataset.multi_scale_data()
window = dataset.lens(z=(0, 5))   # a Lens: an immutable selection over the dataset
window.data
```

[`examples/`](examples/README.md) holds ten self-contained scripts. Each one simulates an imaging
modality (SMLM, calcium imaging, high-content screening, CLEM, MRI, tractography, ...) and composes
it into a mikro scene, and together they use every layer kind the API offers.

### Standalone

Outside arkitekt, you build the client yourself from a `MikroRath` and a `DataLayer`, and you use it
as a context manager:

```python
from mikro import Mikro
from mikro.datalayer import DataLayer
from mikro.rath import MikroRath

mikro = Mikro(rath=MikroRath(link=...), datalayer=DataLayer(...))

with mikro:
    folder = mikro.create_folder(name="examples")
```

`tests/conftest.py` shows the complete wiring against a local deployment.

## Prerequisites

mikro needs a running mikro-server to connect to. The easiest option is an
[Arkitekt](https://arkitekt.live) deployment. For a local test server,
`tests/integration/docker-compose.yml` starts mikro together with a database and S3-compatible
object storage.

## Development

The generated API (`mikro/api/schema.py`) is produced by [turms](https://github.com/jhnnsrs/turms)
from the schema and the documents in `graphql/` (see `graphql.config.yaml`).

```bash
uv run pytest -m "not integration"   # no server needed
uv run pytest -m integration          # a real mikro deployment via dokker
```

See [RELEASING.md](RELEASING.md) for how versions are cut.

## License

MIT, see [LICENSE](LICENSE).
