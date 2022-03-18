---
sidebar_label: schema
title: api.schema
---

## OmeroFileType Objects

```python
class OmeroFileType(str, Enum)
```

An enumeration.

#### TIFF

Tiff

#### JPEG

Jpeg

#### MSR

MSR File

#### CZI

Zeiss Microscopy File

#### UNKNOWN

Unwknon File Format

## RepresentationVariety Objects

```python
class RepresentationVariety(str, Enum)
```

An enumeration.

#### MASK

Mask (Value represent Labels)

#### VOXEL

Voxel (Value represent Intensity)

#### RGB

RGB (First three channel represent RGB)

#### UNKNOWN

Unknown

## RepresentationVarietyInput Objects

```python
class RepresentationVarietyInput(str, Enum)
```

Variety expresses the Type of Representation we are dealing with

#### MASK

Mask (Value represent Labels)

#### VOXEL

Voxel (Value represent Intensity)

#### RGB

RGB (First three channel represent RGB)

#### UNKNOWN

Unknown

## ROIType Objects

```python
class ROIType(str, Enum)
```

An enumeration.

#### ELLIPSE

Ellipse

#### POLYGON

POLYGON

#### LINE

Line

#### RECTANGLE

Rectangle

#### PATH

Path

#### UNKNOWN

Unknown

## RoiTypeInput Objects

```python
class RoiTypeInput(str, Enum)
```

An enumeration.

#### ELLIPSIS

Ellipse

#### POLYGON

POLYGON

#### LINE

Line

#### RECTANGLE

Rectangle

#### PATH

Path

#### UNKNOWN

Unknown

## InputVector Objects

```python
class InputVector(BaseModel)
```

#### x

X-coordinate

#### y

Y-coordinate

#### z

Z-coordinate

## RepresentationFragmentSample Objects

```python
class RepresentationFragmentSample(Sample, BaseModel)
```

Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample

## RepresentationFragment Objects

```python
class RepresentationFragment(Representation, BaseModel)
```

#### sample

The Sample this representation belongs to

#### type

The Representation can have varying types, consult your API

#### variety

The Representation can have varying types, consult your API

#### name

Cleartext name

## ROIFragmentVectors Objects

```python
class ROIFragmentVectors(BaseModel)
```

#### x

X-coordinate

#### y

Y-coordinate

#### z

Z-coordinate

## ROIFragmentRepresentation Objects

```python
class ROIFragmentRepresentation(Representation, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants


@elements/rep:latest

## ROIFragment Objects

```python
class ROIFragment(BaseModel)
```

#### type

The Representation can have varying types, consult your API

## TableFragmentCreator Objects

```python
class TableFragmentCreator(BaseModel)
```

A reflection on the real User

## TableFragmentSample Objects

```python
class TableFragmentSample(Sample, BaseModel)
```

Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample

## TableFragmentRepresentation Objects

```python
class TableFragmentRepresentation(Representation, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants


@elements/rep:latest

## TableFragmentExperiment Objects

```python
class TableFragmentExperiment(Experiment, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment

## TableFragment Objects

```python
class TableFragment(Table, BaseModel)
```

#### tags

A comma-separated list of tags.

#### store

The location of the Parquet on the Storage System (S3 or Media-URL)

## SampleFragmentRepresentations Objects

```python
class SampleFragmentRepresentations(Representation, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants


@elements/rep:latest

## SampleFragmentExperiments Objects

```python
class SampleFragmentExperiments(Experiment, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment

## ExperimentFragmentCreator Objects

```python
class ExperimentFragmentCreator(BaseModel)
```

A reflection on the real User

## Get\_omero\_fileQuery Objects

```python
class Get_omero_fileQuery(BaseModel)
```

#### omerofile

Get a single representation by ID

## Expand\_omerofileQuery Objects

```python
class Expand_omerofileQuery(BaseModel)
```

#### omerofile

Get a single representation by ID

## Search\_omerofileQuery Objects

```python
class Search_omerofileQuery(BaseModel)
```

#### omerofiles

My samples return all of the users samples attached to the current user

## Expand\_representationQuery Objects

```python
class Expand_representationQuery(BaseModel)
```

#### representation

Get a single representation by ID

## Get\_representationQuery Objects

```python
class Get_representationQuery(BaseModel)
```

#### representation

Get a single representation by ID

## Search\_representationQueryRepresentations Objects

```python
class Search_representationQueryRepresentations(Representation, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants


@elements/rep:latest

#### label

Cleartext name

## Search\_representationQuery Objects

```python
class Search_representationQuery(BaseModel)
```

#### representations

All represetations

## Get\_random\_repQuery Objects

```python
class Get_random_repQuery(BaseModel)
```

#### random\_representation

Get a single representation by ID

## ThumbnailQuery Objects

```python
class ThumbnailQuery(BaseModel)
```

#### thumbnail

Get a single representation by ID

## Expand\_thumbnailQuery Objects

```python
class Expand_thumbnailQuery(BaseModel)
```

#### thumbnail

Get a single representation by ID

## Get\_roisQuery Objects

```python
class Get_roisQuery(BaseModel)
```

#### rois

All represetations

## TableQuery Objects

```python
class TableQuery(BaseModel)
```

#### table

Get a single representation by ID

## Expand\_tableQuery Objects

```python
class Expand_tableQuery(BaseModel)
```

#### table

Get a single representation by ID

## Search\_tablesQuery Objects

```python
class Search_tablesQuery(BaseModel)
```

#### tables

My samples return all of the users samples attached to the current user

## Get\_sampleQuery Objects

```python
class Get_sampleQuery(BaseModel)
```

#### sample

Get a single representation by ID

## Search\_sampleQuerySamples Objects

```python
class Search_sampleQuerySamples(Sample, BaseModel)
```

Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample

## Search\_sampleQuery Objects

```python
class Search_sampleQuery(BaseModel)
```

#### samples

All Samples

## Expand\_sampleQuery Objects

```python
class Expand_sampleQuery(BaseModel)
```

#### sample

Get a single representation by ID

## Get\_experimentQuery Objects

```python
class Get_experimentQuery(BaseModel)
```

#### experiment

Get a single representation by ID

## Expand\_experimentQuery Objects

```python
class Expand_experimentQuery(BaseModel)
```

#### experiment

Get a single representation by ID

## Search\_experimentQueryExperiments Objects

```python
class Search_experimentQueryExperiments(Experiment, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment

## Search\_experimentQuery Objects

```python
class Search_experimentQuery(BaseModel)
```

#### experiments

All Samples

## Watch\_samplesSubscriptionMysamplesUpdateExperiments Objects

```python
class Watch_samplesSubscriptionMysamplesUpdateExperiments(Experiment, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment

## Watch\_samplesSubscriptionMysamplesUpdate Objects

```python
class Watch_samplesSubscriptionMysamplesUpdate(Sample, BaseModel)
```

Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample

## Watch\_samplesSubscriptionMysamplesCreateExperiments Objects

```python
class Watch_samplesSubscriptionMysamplesCreateExperiments(Experiment, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants @elements/experiment

## Watch\_samplesSubscriptionMysamplesCreate Objects

```python
class Watch_samplesSubscriptionMysamplesCreate(Sample, BaseModel)
```

Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample

## From\_xarrayMutation Objects

```python
class From_xarrayMutation(BaseModel)
```

#### from\_x\_array

Creates a Representation

## Double\_uploadMutationX Objects

```python
class Double_uploadMutationX(Representation, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants


@elements/rep:latest

## Double\_uploadMutationY Objects

```python
class Double_uploadMutationY(Representation, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants


@elements/rep:latest

## Double\_uploadMutation Objects

```python
class Double_uploadMutation(BaseModel)
```

#### x

Creates a Representation

#### y

Creates a Representation

## Create\_metricMutationCreatemetricRep Objects

```python
class Create_metricMutationCreatemetricRep(Representation, BaseModel)
```

A Representation is a multi-dimensional Array that can do what ever it wants


@elements/rep:latest

## Create\_metricMutationCreatemetricCreator Objects

```python
class Create_metricMutationCreatemetricCreator(BaseModel)
```

A reflection on the real User

## Create\_metricMutationCreatemetric Objects

```python
class Create_metricMutationCreatemetric(BaseModel)
```

#### rep

The Representatoin this Metric belongs to

#### key

The Key

## Create\_metricMutation Objects

```python
class Create_metricMutation(BaseModel)
```

#### create\_metric

Creates a Representation

## Create\_roiMutation Objects

```python
class Create_roiMutation(BaseModel)
```

#### create\_roi

Creates a Sample

## From\_dfMutation Objects

```python
class From_dfMutation(BaseModel)
```

#### from\_df

Creates a Representation

## Create\_sampleMutationCreatesampleCreator Objects

```python
class Create_sampleMutationCreatesampleCreator(BaseModel)
```

A reflection on the real User

## Create\_sampleMutationCreatesample Objects

```python
class Create_sampleMutationCreatesample(Sample, BaseModel)
```

Samples are storage containers for representations. A Sample is to be understood analogous to a Biological Sample. It existed in Time (the time of acquisiton and experimental procedure),
was measured in space (x,y,z) and in different modalities (c). Sample therefore provide a datacontainer where each Representation of
the data shares the same dimensions. Every transaction to our image data is still part of the original acuqistion, so also filtered images are refering back to the sample

## Create\_sampleMutation Objects

```python
class Create_sampleMutation(BaseModel)
```

#### create\_sample

Creates a Sample\n

## Create\_experimentMutation Objects

```python
class Create_experimentMutation(BaseModel)
```

#### create\_experiment

Create an experiment (only signed in users)

#### aget\_omero\_file

```python
async def aget_omero_file(id: Optional[str], mikrorath: MikroRath = None) -> Optional[OmeroFileFragment]
```

get_omero_file

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  OmeroFileFragment

#### get\_omero\_file

```python
def get_omero_file(id: Optional[str], mikrorath: MikroRath = None) -> Optional[OmeroFileFragment]
```

get_omero_file

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  OmeroFileFragment

#### aexpand\_omerofile

```python
async def aexpand_omerofile(id: Optional[str], mikrorath: MikroRath = None) -> Optional[OmeroFileFragment]
```

expand_omerofile

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  OmeroFileFragment

#### expand\_omerofile

```python
def expand_omerofile(id: Optional[str], mikrorath: MikroRath = None) -> Optional[OmeroFileFragment]
```

expand_omerofile

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  OmeroFileFragment

#### asearch\_omerofile

```python
async def asearch_omerofile(search: Optional[str], mikrorath: MikroRath = None) -> Optional[List[Search_omerofileQueryOmerofiles]]
```

search_omerofile

My samples return all of the users samples attached to the current user

**Arguments**:

- `search` _str_ - search
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_omerofileQueryOmerofiles

#### search\_omerofile

```python
def search_omerofile(search: Optional[str], mikrorath: MikroRath = None) -> Optional[List[Search_omerofileQueryOmerofiles]]
```

search_omerofile

My samples return all of the users samples attached to the current user

**Arguments**:

- `search` _str_ - search
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_omerofileQueryOmerofiles

#### aexpand\_representation

```python
async def aexpand_representation(id: Optional[str], mikrorath: MikroRath = None) -> Optional[RepresentationFragment]
```

expand_representation

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  RepresentationFragment

#### expand\_representation

```python
def expand_representation(id: Optional[str], mikrorath: MikroRath = None) -> Optional[RepresentationFragment]
```

expand_representation

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  RepresentationFragment

#### aget\_representation

```python
async def aget_representation(id: Optional[str], mikrorath: MikroRath = None) -> Optional[RepresentationFragment]
```

get_representation

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  RepresentationFragment

#### get\_representation

```python
def get_representation(id: Optional[str], mikrorath: MikroRath = None) -> Optional[RepresentationFragment]
```

get_representation

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  RepresentationFragment

#### asearch\_representation

```python
async def asearch_representation(search: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[List[Search_representationQueryRepresentations]]
```

search_representation

All represetations

**Arguments**:

- `search` _Optional[str], optional_ - search.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_representationQueryRepresentations

#### search\_representation

```python
def search_representation(search: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[List[Search_representationQueryRepresentations]]
```

search_representation

All represetations

**Arguments**:

- `search` _Optional[str], optional_ - search.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_representationQueryRepresentations

#### aget\_random\_rep

```python
async def aget_random_rep(mikrorath: MikroRath = None) -> Optional[RepresentationFragment]
```

get_random_rep

Get a single representation by ID

**Arguments**:

- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  RepresentationFragment

#### get\_random\_rep

```python
def get_random_rep(mikrorath: MikroRath = None) -> Optional[RepresentationFragment]
```

get_random_rep

Get a single representation by ID

**Arguments**:

- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  RepresentationFragment

#### athumbnail

```python
async def athumbnail(id: Optional[str], mikrorath: MikroRath = None) -> Optional[ThumbnailFragment]
```

Thumbnail

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ThumbnailFragment

#### thumbnail

```python
def thumbnail(id: Optional[str], mikrorath: MikroRath = None) -> Optional[ThumbnailFragment]
```

Thumbnail

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ThumbnailFragment

#### aexpand\_thumbnail

```python
async def aexpand_thumbnail(id: Optional[str], mikrorath: MikroRath = None) -> Optional[ThumbnailFragment]
```

expand_thumbnail

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ThumbnailFragment

#### expand\_thumbnail

```python
def expand_thumbnail(id: Optional[str], mikrorath: MikroRath = None) -> Optional[ThumbnailFragment]
```

expand_thumbnail

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ThumbnailFragment

#### aget\_rois

```python
async def aget_rois(representation: Optional[str], type: Optional[List[Optional[RoiTypeInput]]] = None, mikrorath: MikroRath = None) -> Optional[List[ROIFragment]]
```

get_rois

All represetations

**Arguments**:

- `representation` _str_ - representation
- `type` _Optional[List[Optional[RoiTypeInput]]], optional_ - type.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ROIFragment

#### get\_rois

```python
def get_rois(representation: Optional[str], type: Optional[List[Optional[RoiTypeInput]]] = None, mikrorath: MikroRath = None) -> Optional[List[ROIFragment]]
```

get_rois

All represetations

**Arguments**:

- `representation` _str_ - representation
- `type` _Optional[List[Optional[RoiTypeInput]]], optional_ - type.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ROIFragment

#### atable

```python
async def atable(id: Optional[str], mikrorath: MikroRath = None) -> Optional[TableFragment]
```

Table

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  TableFragment

#### table

```python
def table(id: Optional[str], mikrorath: MikroRath = None) -> Optional[TableFragment]
```

Table

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  TableFragment

#### aexpand\_table

```python
async def aexpand_table(id: Optional[str], mikrorath: MikroRath = None) -> Optional[TableFragment]
```

expand_table

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  TableFragment

#### expand\_table

```python
def expand_table(id: Optional[str], mikrorath: MikroRath = None) -> Optional[TableFragment]
```

expand_table

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  TableFragment

#### asearch\_tables

```python
async def asearch_tables(mikrorath: MikroRath = None) -> Optional[List[Search_tablesQueryTables]]
```

search_tables

My samples return all of the users samples attached to the current user

**Arguments**:

- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_tablesQueryTables

#### search\_tables

```python
def search_tables(mikrorath: MikroRath = None) -> Optional[List[Search_tablesQueryTables]]
```

search_tables

My samples return all of the users samples attached to the current user

**Arguments**:

- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_tablesQueryTables

#### aget\_sample

```python
async def aget_sample(id: Optional[str], mikrorath: MikroRath = None) -> Optional[SampleFragment]
```

get_sample

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  SampleFragment

#### get\_sample

```python
def get_sample(id: Optional[str], mikrorath: MikroRath = None) -> Optional[SampleFragment]
```

get_sample

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  SampleFragment

#### asearch\_sample

```python
async def asearch_sample(search: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[List[Search_sampleQuerySamples]]
```

search_sample

All Samples

**Arguments**:

- `search` _Optional[str], optional_ - search.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_sampleQuerySamples

#### search\_sample

```python
def search_sample(search: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[List[Search_sampleQuerySamples]]
```

search_sample

All Samples

**Arguments**:

- `search` _Optional[str], optional_ - search.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_sampleQuerySamples

#### aexpand\_sample

```python
async def aexpand_sample(id: Optional[str], mikrorath: MikroRath = None) -> Optional[SampleFragment]
```

expand_sample

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  SampleFragment

#### expand\_sample

```python
def expand_sample(id: Optional[str], mikrorath: MikroRath = None) -> Optional[SampleFragment]
```

expand_sample

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  SampleFragment

#### aget\_experiment

```python
async def aget_experiment(id: Optional[str], mikrorath: MikroRath = None) -> Optional[ExperimentFragment]
```

get_experiment

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ExperimentFragment

#### get\_experiment

```python
def get_experiment(id: Optional[str], mikrorath: MikroRath = None) -> Optional[ExperimentFragment]
```

get_experiment

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ExperimentFragment

#### aexpand\_experiment

```python
async def aexpand_experiment(id: Optional[str], mikrorath: MikroRath = None) -> Optional[ExperimentFragment]
```

expand_experiment

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ExperimentFragment

#### expand\_experiment

```python
def expand_experiment(id: Optional[str], mikrorath: MikroRath = None) -> Optional[ExperimentFragment]
```

expand_experiment

Get a single representation by ID

**Arguments**:

- `id` _str_ - id
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ExperimentFragment

#### asearch\_experiment

```python
async def asearch_experiment(search: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[List[Search_experimentQueryExperiments]]
```

search_experiment

All Samples

**Arguments**:

- `search` _Optional[str], optional_ - search.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_experimentQueryExperiments

#### search\_experiment

```python
def search_experiment(search: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[List[Search_experimentQueryExperiments]]
```

search_experiment

All Samples

**Arguments**:

- `search` _Optional[str], optional_ - search.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Search_experimentQueryExperiments

#### awatch\_rois

```python
async def awatch_rois(representation: Optional[str], mikrorath: MikroRath = None) -> AsyncIterator[Optional[Watch_roisSubscriptionRois]]
```

watch_rois



**Arguments**:

- `representation` _str_ - representation
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Watch_roisSubscriptionRois

#### watch\_rois

```python
def watch_rois(representation: Optional[str], mikrorath: MikroRath = None) -> Iterator[Optional[Watch_roisSubscriptionRois]]
```

watch_rois



**Arguments**:

- `representation` _str_ - representation
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Watch_roisSubscriptionRois

#### awatch\_samples

```python
async def awatch_samples(mikrorath: MikroRath = None) -> AsyncIterator[Optional[Watch_samplesSubscriptionMysamples]]
```

watch_samples



**Arguments**:

- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Watch_samplesSubscriptionMysamples

#### watch\_samples

```python
def watch_samples(mikrorath: MikroRath = None) -> Iterator[Optional[Watch_samplesSubscriptionMysamples]]
```

watch_samples



**Arguments**:

- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Watch_samplesSubscriptionMysamples

#### anegotiate

```python
async def anegotiate(mikrorath: MikroRath = None) -> Optional[Dict]
```

negotiate



**Arguments**:

- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Dict

#### negotiate

```python
def negotiate(mikrorath: MikroRath = None) -> Optional[Dict]
```

negotiate



**Arguments**:

- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Dict

#### aupload\_bioimage

```python
async def aupload_bioimage(file: Optional[Upload], mikrorath: MikroRath = None) -> Optional[Upload_bioimageMutationUploadomerofile]
```

upload_bioimage



**Arguments**:

- `file` _Upload_ - file
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Upload_bioimageMutationUploadomerofile

#### upload\_bioimage

```python
def upload_bioimage(file: Optional[Upload], mikrorath: MikroRath = None) -> Optional[Upload_bioimageMutationUploadomerofile]
```

upload_bioimage



**Arguments**:

- `file` _Upload_ - file
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Upload_bioimageMutationUploadomerofile

#### afrom\_xarray

```python
async def afrom_xarray(xarray: Optional[XArray], name: Optional[str] = None, variety: Optional[RepresentationVarietyInput] = None, origins: Optional[List[Optional[str]]] = None, tags: Optional[List[Optional[str]]] = None, sample: Optional[str] = None, omero: Optional[OmeroRepresentationInput] = None, mikrorath: MikroRath = None) -> Optional[RepresentationFragment]
```

from_xarray

Creates a Representation

**Arguments**:

- `xarray` _XArray_ - xarray
- `name` _Optional[str], optional_ - name.
- `variety` _Optional[RepresentationVarietyInput], optional_ - variety.
- `origins` _Optional[List[Optional[str]]], optional_ - origins.
- `tags` _Optional[List[Optional[str]]], optional_ - tags.
- `sample` _Optional[str], optional_ - sample.
- `omero` _Optional[OmeroRepresentationInput], optional_ - omero.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  RepresentationFragment

#### from\_xarray

```python
def from_xarray(xarray: Optional[XArray], name: Optional[str] = None, variety: Optional[RepresentationVarietyInput] = None, origins: Optional[List[Optional[str]]] = None, tags: Optional[List[Optional[str]]] = None, sample: Optional[str] = None, omero: Optional[OmeroRepresentationInput] = None, mikrorath: MikroRath = None) -> Optional[RepresentationFragment]
```

from_xarray

Creates a Representation

**Arguments**:

- `xarray` _XArray_ - xarray
- `name` _Optional[str], optional_ - name.
- `variety` _Optional[RepresentationVarietyInput], optional_ - variety.
- `origins` _Optional[List[Optional[str]]], optional_ - origins.
- `tags` _Optional[List[Optional[str]]], optional_ - tags.
- `sample` _Optional[str], optional_ - sample.
- `omero` _Optional[OmeroRepresentationInput], optional_ - omero.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  RepresentationFragment

#### adouble\_upload

```python
async def adouble_upload(xarray: Optional[XArray], name: Optional[str] = None, origins: Optional[List[Optional[str]]] = None, tags: Optional[List[Optional[str]]] = None, sample: Optional[str] = None, omero: Optional[OmeroRepresentationInput] = None, mikrorath: MikroRath = None) -> Double_uploadMutation
```

double_upload


x: Creates a Representation
y: Creates a Representation

**Arguments**:

- `xarray` _XArray_ - xarray
- `name` _Optional[str], optional_ - name.
- `origins` _Optional[List[Optional[str]]], optional_ - origins.
- `tags` _Optional[List[Optional[str]]], optional_ - tags.
- `sample` _Optional[str], optional_ - sample.
- `omero` _Optional[OmeroRepresentationInput], optional_ - omero.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Double_uploadMutation

#### double\_upload

```python
def double_upload(xarray: Optional[XArray], name: Optional[str] = None, origins: Optional[List[Optional[str]]] = None, tags: Optional[List[Optional[str]]] = None, sample: Optional[str] = None, omero: Optional[OmeroRepresentationInput] = None, mikrorath: MikroRath = None) -> Double_uploadMutation
```

double_upload


x: Creates a Representation
y: Creates a Representation

**Arguments**:

- `xarray` _XArray_ - xarray
- `name` _Optional[str], optional_ - name.
- `origins` _Optional[List[Optional[str]]], optional_ - origins.
- `tags` _Optional[List[Optional[str]]], optional_ - tags.
- `sample` _Optional[str], optional_ - sample.
- `omero` _Optional[OmeroRepresentationInput], optional_ - omero.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Double_uploadMutation

#### acreate\_thumbnail

```python
async def acreate_thumbnail(rep: Optional[str], file: Optional[File], mikrorath: MikroRath = None) -> Optional[ThumbnailFragment]
```

create_thumbnail



**Arguments**:

- `rep` _str_ - rep
- `file` _File_ - file
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ThumbnailFragment

#### create\_thumbnail

```python
def create_thumbnail(rep: Optional[str], file: Optional[File], mikrorath: MikroRath = None) -> Optional[ThumbnailFragment]
```

create_thumbnail



**Arguments**:

- `rep` _str_ - rep
- `file` _File_ - file
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ThumbnailFragment

#### acreate\_metric

```python
async def acreate_metric(key: Optional[str], value: Optional[Dict], rep: Optional[str] = None, sample: Optional[str] = None, experiment: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[Create_metricMutationCreatemetric]
```

create_metric

Creates a Representation

**Arguments**:

- `key` _str_ - key
- `value` _Dict_ - value
- `rep` _Optional[str], optional_ - rep.
- `sample` _Optional[str], optional_ - sample.
- `experiment` _Optional[str], optional_ - experiment.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Create_metricMutationCreatemetric

#### create\_metric

```python
def create_metric(key: Optional[str], value: Optional[Dict], rep: Optional[str] = None, sample: Optional[str] = None, experiment: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[Create_metricMutationCreatemetric]
```

create_metric

Creates a Representation

**Arguments**:

- `key` _str_ - key
- `value` _Dict_ - value
- `rep` _Optional[str], optional_ - rep.
- `sample` _Optional[str], optional_ - sample.
- `experiment` _Optional[str], optional_ - experiment.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Create_metricMutationCreatemetric

#### acreate\_roi

```python
async def acreate_roi(representation: Optional[str], vectors: Optional[List[Optional[InputVector]]], creator: Optional[str] = None, type: Optional[RoiTypeInput] = None, mikrorath: MikroRath = None) -> Optional[ROIFragment]
```

create_roi

Creates a Sample

**Arguments**:

- `representation` _str_ - representation
- `vectors` _List[Optional[InputVector]]_ - vectors
- `creator` _Optional[str], optional_ - creator.
- `type` _Optional[RoiTypeInput], optional_ - type.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ROIFragment

#### create\_roi

```python
def create_roi(representation: Optional[str], vectors: Optional[List[Optional[InputVector]]], creator: Optional[str] = None, type: Optional[RoiTypeInput] = None, mikrorath: MikroRath = None) -> Optional[ROIFragment]
```

create_roi

Creates a Sample

**Arguments**:

- `representation` _str_ - representation
- `vectors` _List[Optional[InputVector]]_ - vectors
- `creator` _Optional[str], optional_ - creator.
- `type` _Optional[RoiTypeInput], optional_ - type.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ROIFragment

#### afrom\_df

```python
async def afrom_df(df: Optional[DataFrame], mikrorath: MikroRath = None) -> Optional[TableFragment]
```

from_df

Creates a Representation

**Arguments**:

- `df` _DataFrame_ - df
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  TableFragment

#### from\_df

```python
def from_df(df: Optional[DataFrame], mikrorath: MikroRath = None) -> Optional[TableFragment]
```

from_df

Creates a Representation

**Arguments**:

- `df` _DataFrame_ - df
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  TableFragment

#### acreate\_sample

```python
async def acreate_sample(name: Optional[str] = None, creator: Optional[str] = None, meta: Optional[Dict] = None, experiments: Optional[List[Optional[str]]] = None, mikrorath: MikroRath = None) -> Optional[Create_sampleMutationCreatesample]
```

create_sample

Creates a Sample


**Arguments**:

- `name` _Optional[str], optional_ - name.
- `creator` _Optional[str], optional_ - creator.
- `meta` _Optional[Dict], optional_ - meta.
- `experiments` _Optional[List[Optional[str]]], optional_ - experiments.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Create_sampleMutationCreatesample

#### create\_sample

```python
def create_sample(name: Optional[str] = None, creator: Optional[str] = None, meta: Optional[Dict] = None, experiments: Optional[List[Optional[str]]] = None, mikrorath: MikroRath = None) -> Optional[Create_sampleMutationCreatesample]
```

create_sample

Creates a Sample


**Arguments**:

- `name` _Optional[str], optional_ - name.
- `creator` _Optional[str], optional_ - creator.
- `meta` _Optional[Dict], optional_ - meta.
- `experiments` _Optional[List[Optional[str]]], optional_ - experiments.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  Create_sampleMutationCreatesample

#### acreate\_experiment

```python
async def acreate_experiment(name: Optional[str], creator: Optional[str] = None, meta: Optional[Dict] = None, description: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[ExperimentFragment]
```

create_experiment

Create an experiment (only signed in users)

**Arguments**:

- `name` _str_ - name
- `creator` _Optional[str], optional_ - creator.
- `meta` _Optional[Dict], optional_ - meta.
- `description` _Optional[str], optional_ - description.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ExperimentFragment

#### create\_experiment

```python
def create_experiment(name: Optional[str], creator: Optional[str] = None, meta: Optional[Dict] = None, description: Optional[str] = None, mikrorath: MikroRath = None) -> Optional[ExperimentFragment]
```

create_experiment

Create an experiment (only signed in users)

**Arguments**:

- `name` _str_ - name
- `creator` _Optional[str], optional_ - creator.
- `meta` _Optional[Dict], optional_ - meta.
- `description` _Optional[str], optional_ - description.
- `mikrorath` _mikro.mikro.MikroRath, optional_ - The mikro rath client
  

**Returns**:

  ExperimentFragment

