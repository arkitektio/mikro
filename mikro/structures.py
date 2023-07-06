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
    from rekuest.structures.default import (
        get_default_structure_registry,
        Scope,
        id_shrink,
    )
    from rekuest.widgets import SearchWidget
    from mikro.api.schema import *

    structure_reg = get_default_structure_registry()
    structure_reg.register_as_structure(
        RepresentationFragment,
        identifier="@mikro/representation",
        aexpand=aexpand_representation,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_representationQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        MetricFragment,
        identifier="@mikro/metric",
        aexpand=aexpand_metric,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=None,
    )
    structure_reg.register_as_structure(
        ChannelFragment,
        identifier="@mikro/channel",
        aexpand=aget_channel,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=SearchChannelsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        DimensionMapFragment,
        identifier="@mikro/dimensionmap",
        aexpand=aget_dimension_map,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=None,
    )
    structure_reg.register_as_structure(
        SampleFragment,
        identifier="@mikro/sample",
        aexpand=aexpand_sample,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_sampleQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        GraphFragment,
        identifier="@mikro/graph",
        aexpand=aget_graph,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_graphsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        TableFragment,
        identifier="@mikro/table",
        aexpand=aexpand_table,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_tablesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ExperimentFragment,
        identifier="@mikro/experiment",
        aexpand=aexpand_experiment,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_experimentQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ThumbnailFragment,
        identifier="@mikro/thumbnail",
        aexpand=aexpand_thumbnail,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_thumbnailsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        OmeroFileFragment,
        identifier="@mikro/omerofile",
        aexpand=aexpand_omerofile,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_omerofileQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ROIFragment,
        identifier="@mikro/roi",
        aexpand=aexpand_roi,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(query=Search_roisQuery.Meta.document, ward="mikro"),
    )
    structure_reg.register_as_structure(
        FeatureFragment,
        identifier="@mikro/feature",
        aexpand=aexpand_feature,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_featuresQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        LabelFragment,
        identifier="@mikro/label",
        aexpand=aexpand_label,
        ashrink=id_shrink,
        scope=Scope.GLOBAL,
        default_widget=SearchWidget(
            query=Search_labelsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        VideoFragment,
        identifier="@mikro/video",
        scope=Scope.GLOBAL,
        aexpand=aget_video,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_videosQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        PositionFragment,
        identifier="@mikro/position",
        scope=Scope.GLOBAL,
        aexpand=aexpand_position,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_positionsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        StageFragment,
        identifier="@mikro/stage",
        scope=Scope.GLOBAL,
        aexpand=aexpand_stage,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_stagesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        EraFragment,
        identifier="@mikro/era",
        scope=Scope.GLOBAL,
        aexpand=aget_era,
        ashrink=id_shrink,
        default_widget=SearchWidget(query=SearchErasQuery.Meta.document, ward="mikro"),
    )
    structure_reg.register_as_structure(
        TimepointFragment,
        identifier="@mikro/timepoint",
        scope=Scope.GLOBAL,
        aexpand=aget_timepoint,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=SearchTimepointsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        DatasetFragment,
        identifier="@mikro/dataset",
        scope=Scope.GLOBAL,
        aexpand=aexpand_dataset,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_datasetsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ObjectiveFragment,
        identifier="@mikro/objective",
        scope=Scope.GLOBAL,
        aexpand=aexpand_objective,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_objectivesQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        CameraFragment,
        identifier="@mikro/camera",
        scope=Scope.GLOBAL,
        aexpand=aexpand_camera,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_camerasQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ModelFragment,
        identifier="@mikro/model",
        scope=Scope.GLOBAL,
        aexpand=aexpand_model,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_modelsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        ContextFragment,
        identifier="@mikro/context",
        scope=Scope.GLOBAL,
        aexpand=aexpand_context,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_contextsQuery.Meta.document, ward="mikro"
        ),
    )
    structure_reg.register_as_structure(
        LinkFragment,
        identifier="@mikro/link",
        scope=Scope.GLOBAL,
        aexpand=aexpand_link,
        ashrink=id_shrink,
        default_widget=SearchWidget(
            query=Search_linksQuery.Meta.document, ward="mikro"
        ),
    )
