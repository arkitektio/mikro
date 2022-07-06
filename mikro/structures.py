""" Strucutre Registration

This module is autoimported by arkitekt. It registers the default structure types with the arkitekt
structure-registry so that they can be used in the arkitekt app without having to import them.

You can of course overwrite this in your app if you need to expand to a more complex query.

"""


from arkitekt.widgets import ImageReturnWidget


try:
    from arkitekt.structures.default import get_default_structure_registry
    from arkitekt.widgets import SearchWidget
    from mikro.api.schema import *

    structure_reg = get_default_structure_registry()
    structure_reg.register_as_structure(
        RepresentationFragment,
        identifier="@mikro/representation",
        expand=aexpand_representation,
        default_widget=SearchWidget(query=Search_representationQuery.Meta.document),
    )
    structure_reg.register_as_structure(
        SampleFragment,
        identifier="@mikro/sample",
        expand=aexpand_sample,
        default_widget=SearchWidget(query=Search_sampleQuery.Meta.document),
    )
    structure_reg.register_as_structure(
        ExperimentFragment,
        identifier="@mikro/experiment",
        expand=aexpand_experiment,
        default_widget=SearchWidget(query=Search_experimentQuery.Meta.document),
    )
    structure_reg.register_as_structure(
        ThumbnailFragment,
        identifier="@mikro/thumbnail",
        expand=aexpand_thumbnail,
        default_widget=SearchWidget(query=Search_thumbnailsQuery.Meta.document),
        default_returnwidget=ImageReturnWidget(
            query=Image_for_thumbnailQuery.Meta.document
        ),
    )
    structure_reg.register_as_structure(
        OmeroFileFragment,
        identifier="@mikro/omerofile",
        expand=aexpand_omerofile,
        default_widget=SearchWidget(query=Search_omerofileQuery.Meta.document),
    )
except ImportError:
    structure_reg = None
