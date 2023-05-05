""" Strucutre Registration

This module is autoimported by arkitekt. It registers the default structure types with the arkitekt
structure-registry so that they can be used in the arkitekt app without having to import them.

You can of course overwrite this in your app if you need to expand to a more complex query.

"""
import logging

logger = logging.getLogger(__name__)


try:
    import rekuest
except ImportError:
    pass
    rekuest = None
    structure_reg = None

# Check if rekuest is installed
# If it is, register the structures with the default structure registry
if rekuest:
    from rekuest.structures.default import get_default_structure_registry, Scope
    from rekuest.widgets import SearchWidget
    from mikro.api.schema import *

    structure_reg = get_default_structure_registry()
    structure_reg.register_as_structure(
        RepresentationFragment,
        identifier="@mikro/representation",
        expand=aexpand_representation,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_representationQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        MetricFragment,
        identifier="@mikro/metric",
        expand=aexpand_metric,
        scope=Scope.GLOBAL,
        default_widget=None,
    )
    structure_reg.register_as_structure(
        ChannelFragment,
        identifier="@mikro/channel",
        expand=aget_channel,
        scope=Scope.GLOBAL,
        default_widget=None,
    )
    structure_reg.register_as_structure(
        DimensionMapFragment,
        identifier="@mikro/dimensionmap",
        expand=aget_dimension_map,
        scope=Scope.GLOBAL,
        default_widget=None,
    )
    structure_reg.register_as_structure(
        SampleFragment,
        identifier="@mikro/sample",
        expand=aexpand_sample,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_sampleQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        TableFragment,
        identifier="@mikro/table",
        expand=aexpand_table,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_tablesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ExperimentFragment,
        identifier="@mikro/experiment",
        expand=aexpand_experiment,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_experimentQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ThumbnailFragment,
        identifier="@mikro/thumbnail",
        expand=aexpand_thumbnail,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_thumbnailsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        OmeroFileFragment,
        identifier="@mikro/omerofile",
        expand=aexpand_omerofile,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_omerofileQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ROIFragment,
        identifier="@mikro/roi",
        expand=aexpand_roi,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(query=Search_roisQuery.Meta.document, ward="mikro"),
    )
    structure_reg.register_as_structure(
        FeatureFragment,
        identifier="@mikro/feature",
        expand=aexpand_feature,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_featuresQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        LabelFragment,
        identifier="@mikro/label",
        expand=aexpand_label,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_labelsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        VideoFragment,
        identifier="@mikro/video",
        scope=Scope.GLOBAL,
        expand=aget_video,
        default_widget=SearchWidget(
            query=Search_videosQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        PositionFragment,
        identifier="@mikro/position",
        scope=Scope.GLOBAL,
        expand=aexpand_position,
        default_widget=SearchWidget(
            query=Search_positionsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        StageFragment,
        identifier="@mikro/stage",
        scope=Scope.GLOBAL,
        expand=aexpand_stage,
        default_widget=SearchWidget(
            query=Search_stagesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        EraFragment,
        identifier="@mikro/era",
        scope=Scope.GLOBAL,
        expand=aget_era,
        default_widget=SearchWidget(query=SearchErasQuery.Meta.document, ward="mikro"),
    )
    structure_reg.register_as_structure(
        TimepointFragment,
        identifier="@mikro/timepoint",
        scope=Scope.GLOBAL,
        expand=aget_timepoint,
        default_widget=SearchWidget(
            query=SearchTimepointsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        DatasetFragment,
        identifier="@mikro/dataset",
        scope=Scope.GLOBAL,
        expand=aexpand_dataset,
        default_widget=SearchWidget(
            query=Search_datasetsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ObjectiveFragment,
        identifier="@mikro/objective",
        scope=Scope.GLOBAL,
        expand=aexpand_objective,
        default_widget=SearchWidget(
            query=Search_objectivesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ModelFragment,
        identifier="@mikro/model",
        scope=Scope.GLOBAL,
        expand=aexpand_model,
        default_widget=SearchWidget(
            query=Search_modelsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ContextFragment,
        identifier="@mikro/context",
        scope=Scope.GLOBAL,
        expand=aexpand_context,
        default_widget=SearchWidget(
            query=Search_contextsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        LinkFragment,
        identifier="@mikro/link",
        scope=Scope.GLOBAL,
        expand=aexpand_link,
        default_widget=SearchWidget(
            query=Search_linksQuery.Meta.document, ward="mikro"
        ),
    )
