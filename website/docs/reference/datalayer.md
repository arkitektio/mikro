---
sidebar_label: datalayer
title: datalayer
---

This modules provides the datalayer.

**Example**:

  
  A simple datalayer that connects to an s3 instance via access_key and secret_key.
  You can define all of the logic within the context manager
  
  ```python
  from mikro.datalayer import Datalayer
  
  dl = Datalayer(access_key=&quot;XXXX&quot;, secret_key=&quot;XXXX&quot;, endpoint_url=&quot;s3.amazonaws.com&quot;)
  
  with dl:
  print(df.fs.ls())
  
  ```
  
  Async Usage:
  
  ```python
  from mikro.datalayer import Datalayer
  
  dl = Datalayer(access_key=&quot;XXXX&quot;, secret_key=&quot;XXXX&quot;, endpoint_url=&quot;s3.amazonaws.com&quot;)
  
  async with dl:
  print(df.fs.ls())
  
  ```

## DataLayer Objects

```python
@koilable(add_connectors=True)
class DataLayer()
```

Implements a S3 DataLayer

This will be used to upload and download files from S3.
Make sure to set the access_key and secret_key and enter the context
manager to connect to S3 (if authentication is required for the S3 instance
and to ensure that the context is exited when the context manager is exited
(for future cleanup purposes on other datalayers).

**Attributes**:

- `fs` _s3fs.S3FileSystem_ - The filesystem object

