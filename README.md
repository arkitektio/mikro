# mikro

[![codecov](https://codecov.io/gh/arkitektio/mikro-next/graph/badge.svg?token=PRoouTwAGx)](https://codecov.io/gh/arkitektio/mikro-next)
[![PyPI version](https://badge.fury.io/py/mikro-next.svg)](https://pypi.org/project/mikro-next/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://pypi.org/project/mikro-next/)
![Maintainer](https://img.shields.io/badge/maintainer-jhnnsrs-blue)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/mikro-next.svg)](https://pypi.python.org/pypi/mikro-next/)
[![PyPI status](https://img.shields.io/pypi/status/mikro-next.svg)](https://pypi.python.org/pypi/mikro-next/)
[![PyPI download month](https://img.shields.io/pypi/dm/mikro-next.svg)](https://pypi.python.org/pypi/mikro-next/)

mikro-next is the python client for the next version of the mikro-server environment.


# Quick Start

Let's discover **mikro in less than 5 minutes**.


### Inspiration

Mikro is the client app for the mikro-server, a graphql compliant server for hosting your microscopy data. Mikro tries to
facilitate a transition to use modern technologies for the storage and retrieval of microscopy data. It emphasizes the importance
of relations within your data and tries to make them accessible through a GraphQL Interface.

### Installation

```bash
pip install mikro-next
```

### Design

Mikro is just a client and therefore only concerns itself with the querying (retrieval) and mutation (altering) of data on
the central server. Therefore its only composes two major components:

- Rath: A graphql client to query complex relationships in your data through simple queries.
- Datalayer: A way of accessing and retrieving binary data (image arrays, big tables,...) through known python apis like xarray and numpy

Under the hood Mikro is build on the growing ecosystem of graphql and pydantic as well as the amazing toolstack
of zarr, dask and xarray for scientific computation.

### Features

- Easy to extend with custom graphql logic (together with turms can generate APIs for very complex relationship)
- Interoperable and standardization (has bindings for Dataframes and Numpy arrays)
- Fully Typed and Validated(uses pydantic for validation)

### Prerequisits

You need a fully configured mikro-server running in your lab, that mikro can connect to. The easiest way to do this is to
use the [arkitekt.live](https://arkitekt.live) platform, which provides a fully managed mikro-server for your lab. Just
follow the instructions on the website to get started. If you just want a local test service, check out the 
tests/integration/docker-compose.yml file, which contains a docker-compose file to start a mikro-server
locally with a postgres database and a minio object storage.

## Example Use case

The API of Mikro is best explained on this example:

```python
from arkitekt_next import easy
from mikro_next.api.schema import get_random_image


with easy("my-app") as app:
    g = get_random_image()

    maximum_intensity_l = g.data.max()
    maximum_intensity = maximum_intensity.compute()
```

1. **First we construct an App**:
   App is the entrypoint of every client accessing the mikro service,
   in a more complex example here you would define the configuration of
   the connection. In this example we use the `easy` function to
   construct an arkitekt-app with a default configuration. 

2. **Entering the Context**:
   This is the most important concept to learn, every interaction you have with
   mikro needs to happen within a context. This is needed because mikro uses
   asyncrhonous programming to retrieve, and save data efficiently. The context
   ensures that every connection gets cleaned up effienctly and safely.

3. **Retrieving Model**:
   On calling `get_random_image` we are calling the graphql server and retrieve
   the metadata of a reandom image. This function just
   executes a default graphqlquery and constructs a typed python model out of it.

4. **Retrieving Data**:
   Here we are actually doing operations on the image data. Every Image
   has a `data` attribute. This data attribute resolves to a lazily loaded
   xarray that connects to a zarr store on the s3 datalayer. What that means for you
   is that you can use this as a normal xarray with dask array.

5. **Computing Data**
   Only on Computing Data is the data actually downloaded from the datalayer. If you
   only act on partial data, only partial data is downloaded. This is the magic of
   zarr and xarray.

## Other usage options

If you dont want to use a context manager you can also choose to
use the connect/disconnect methods:

```python
from arkitekt_next import easy 
from mikro_next.api.schema import get_image


app = easy()
app.enter()

g = get_image(107)

maximum_intensity = g.data.max().compute()

#later
app.exit()


```
:::warning
If you choose this approach, make sure that you call disconnect in your code at some
stage. Especially when using asynchronous links/transports (supporting subscriptions) in a sync
environment,as only on disconnect we will close the threaded loop that these transports required
to operate. Otherwise this connection will stay open.
:::

# Async Usage:

If you love asyncio, the way we do, you can also take full control over what happens in your app
within an asynchrouns loop. Actually this is the API we would recommend.

```python
from mikro import MikroApp, aget_representation
from fakts import Fakts


app = MikroApp()

async with app:
    g = await aget_representation(107)

    maximum_intensity = g.data.max() # DO NOT DO THIS IN YOUR ASYNC LOOP

```

:::warning

In this scenario we are using the asyncio event loop and do not spawn a seperate thread, so calling
g.data.max() actually calculates the array (e.g downloads everything blockingly in this loop)

:::

If you want to know more about why we use apps, composition and how we handle threads, check out koil
(mikros async-sync-helper library)
