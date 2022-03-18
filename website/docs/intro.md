---
sidebar_position: 1
sidebar_label: "Introduction"
---

# Quick Start

Let's discover **mikro in less than 5 minutes**.

:::warning
This is a very developmental build, that is currently only used to test in the IINS, Bordeaux. If you are intersteted please contact
the authors directly!
please
:::

### Inspiration

Mikro is the client app for the mikro-server, a graphql compliant server for hosting your microscopy data. Mikro tries to
facilitate a transition to use modern technologies for the storage and retrieval of microscopy data. It emphasizes the importance
of relations within your data and tries to make them accessible through a GraphQL Interface.

### Installation

```bash
pip install mikro
```

### Design

Mikro is just a client and therefore only concerns itself with the querying (retrieval) and mutation (altering) of data on
the central server. Therefore its only composes two major components:

- Rath: A graphql client to query complex relationships in your data through simple queries.
- Datalayer: A way of accessing and retrieving binary data (image arrays, big tables,...) through known python apis like xarray and numpy

Under the hood Mikro is build on the growing ecosystem of graphql and pydantic as well as the amazing toolstack
of zarr, dask and xarray for scientific computation.

### Prerequisits

You need a fully configured mikro-server running in your lab, that mikro can connect to.

## Example Use case

The API of Mikro is best explained on this example:

```python
from mikro import MikroApp, get_representation
from fakts import Fakts


app = MikroApp()

with app:
    g = get_representation(107)

    maximum_intensity_l = g.data.max()
    maximum_intensity = maximum_intensity.compute()
```

1. **First we construct an App**:
   App is the entrypoint of every client accessing the mikro service,
   in a more complex example here you would define the configuration of
   the connection. If you don't specify anything here it will use `fakts` to
   autoconfigure (searching for the fakts.yaml file in the directory). Check
   fakts documentation for retrieving this.

2. **Entering the Context**:
   This is the most important concept to learn, every interaction you have with
   mikro needs to happen within a context. This is needed because mikro uses
   asyncrhonous programming to retrieve, and save data efficiently. The context
   ensures that every connection gets cleaned up effienctly and safely.

3. **Retrieving Model**:
   On calling `get_representation` we are calling the graphql server and retrieve
   the metadata of an image In this case the image with id `107`. This function just
   executes a default graphqlquery and constructs a typed python model out of it.

4. **Retrieving Data**:
   Here we are actually doing operations on the image data. Every Representation
   (Image) has a `data` attribute. This data attribute resolves to a lazily loaded
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
from mikro import MikroApp, get_representation
from fakts import Fakts


app = MikroApp()
app.connect()

g = get_representation(107)

maximum_intensity = g.data.max().compute()

#later
app.disconnect()


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
