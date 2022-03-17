try:
    from arkitekt.structures.registry import get_current_structure_registry
    from arkitekt.widgets import SearchWidget
    from mikro.api.schema import *

    structure_reg = get_current_structure_registry()
    structure_reg.register_as_structure(
        RepresentationFragment,
        expand=aexpand_representation,
        default_widget=SearchWidget(query=Search_representationQuery.Meta.document),
    )
    structure_reg.register_as_structure(
        SampleFragment,
        expand=aexpand_sample,
        default_widget=SearchWidget(query=Search_sampleQuery.Meta.document),
    )
    structure_reg.register_as_structure(
        ExperimentFragment,
        expand=aexpand_experiment,
        default_widget=SearchWidget(query=Search_experimentQuery.Meta.document),
    )
    structure_reg.register_as_structure(ThumbnailFragment, expand=aexpand_thumbnail)
    structure_reg.register_as_structure(OmeroFileFragment, expand=aexpand_omerofile)
except ImportError:
    pass
