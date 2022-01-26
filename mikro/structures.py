from arkitekt.serialization.registry import get_current_structure_registry
from arkitekt.widgets import *
from mikro.api.schema import *


Representation = RepresentationFragment
Sample = SampleFragment
Experiment = ExperimentFragment
Thumbnail = ThumbnailFragment
OmeroFile = OmeroFileFragment


structure_reg = get_current_structure_registry()
structure_reg.register_as_structure(
    Representation,
    expand=aexpand_representation,
    default_widget=SearchWidget(query=Search_representationQuery.Meta.document),
)
structure_reg.register_as_structure(
    Sample,
    expand=aexpand_sample,
    default_widget=SearchWidget(query=Search_sampleQuery.Meta.document),
)
structure_reg.register_as_structure(
    Experiment,
    expand=aexpand_experiment,
    default_widget=SearchWidget(query=Search_experimentQuery.Meta.document),
)
structure_reg.register_as_structure(Thumbnail, expand=aexpand_thumbnail)
structure_reg.register_as_structure(OmeroFile, expand=aexpand_omerofile)
