""" Strucutre Registration

This module is autoimported by arkitekt. It registers the default structure types with the arkitekt
structure-registry so that they can be used in the arkitekt app without having to import them.

You can of course overwrite this in your app if you need to expand to a more complex query.

"""


try:
    from rekuest.structures.default import get_default_structure_registry
    from rekuest.widgets import SearchWidget, ImageReturnWidget
    from rekuest.widgets import CustomReturnWidget
    from mikro.api.schema import *

    structure_reg = get_default_structure_registry()
    structure_reg.register_as_structure(
        RepresentationFragment,
        identifier="@mikro/representation",
        expand=aexpand_representation,
        default_widget=SearchWidget(
            query=Search_representationQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        MetricFragment,
        identifier="@mikro/metric",
        expand=aexpand_metric,
        default_widget=None,
        default_returnwidget=CustomReturnWidget(hook="metric", ward="mikro"),
    )
    structure_reg.register_as_structure(
        SampleFragment,
        identifier="@mikro/sample",
        expand=aexpand_sample,
        default_widget=SearchWidget(
            query=Search_sampleQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        TableFragment,
        identifier="@mikro/table",
        expand=aexpand_table,
        default_widget=SearchWidget(
            query=Search_tablesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ExperimentFragment,
        identifier="@mikro/experiment",
        expand=aexpand_experiment,
        default_widget=SearchWidget(
            query=Search_experimentQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ThumbnailFragment,
        identifier="@mikro/thumbnail",
        expand=aexpand_thumbnail,
        default_widget=SearchWidget(
            query=Search_thumbnailsQuery.Meta.document, ward="mikro"
        ),
        default_returnwidget=ImageReturnWidget(
            query=Image_for_thumbnailQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        OmeroFileFragment,
        identifier="@mikro/omerofile",
        expand=aexpand_omerofile,
        default_widget=SearchWidget(
            query=Search_omerofileQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ROIFragment,
        identifier="@mikro/roi",
        expand=aexpand_roi,
        default_widget=SearchWidget(query=Search_roisQuery.Meta.document, ward="mikro"),
    )
    structure_reg.register_as_structure(
        FeatureFragment,
        identifier="@mikro/feature",
        expand=aexpand_feature,
        default_widget=SearchWidget(
            query=Search_featuresQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        LabelFragment,
        identifier="@mikro/label",
        expand=aexpand_label,
        default_widget=SearchWidget(
            query=Search_labelsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        PositionFragment,
        identifier="@mikro/position",
        expand=aexpand_position,
        default_widget=SearchWidget(
            query=Search_positionsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        StageFragment,
        identifier="@mikro/stage",
        expand=aexpand_stage,
        default_widget=SearchWidget(
            query=Search_stagesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        DatasetFragment,
        identifier="@mikro/dataset",
        expand=aexpand_dataset,
        default_widget=SearchWidget(
            query=Search_datasetsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ObjectiveFragment,
        identifier="@mikro/objective",
        expand=aexpand_objective,
        default_widget=SearchWidget(
            query=Search_objectivesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ModelFragment,
        identifier="@mikro/model",
        expand=aexpand_model,
        default_widget=SearchWidget(
            query=Search_modelsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ContextFragment,
        identifier="@mikro/context",
        expand=aexpand_context,
        default_widget=SearchWidget(
            query=Search_contextsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        LinkFragment,
        identifier="@mikro/link",
        expand=aexpand_link,
        default_widget=SearchWidget(
            query=Search_linksQuery.Meta.document, ward="mikro"
        ),
    )


except ImportError:
    structure_reg = None
