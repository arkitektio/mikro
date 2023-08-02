"""Default Widgets

This Module provides default widgets that can be used with the mikro app in an arkitekt
context.

Attributes:
    MY_TOP_REPRESENTATIONS (SearchWidget): The top representations for the currently active user
    MY_TOP_SAMPLES (SearchWidget): The top samples for the currently active user
"""


def build_column_query(for_input: str):
    """Builds a query for a column widget. (Which is a search widget with a specific column query that
    adsjust to the input variable name)"""
    return """
    query ColumnSearch($search: String, $values: [ID], $%s: ID!)  {
        options: columnsof(search: $search, values: $values, table: $%s) {
            value: name
            label: fieldName
            description: pandasType
        }
    }
    """ % (
        for_input,
        for_input,
    )


def build_roi_query(for_input: str):
    """Builds a query for a column widget. (Which is a search widget with a specific column query that
    adsjust to the input variable name)"""
    return """
    query Representation($search: String, $values: [ID], $%s: ID!)  {
        options: rois(search: $search, values: $values, representation: $%s) {
            value: id
            label: label
            description: id
        }
    }
    """ % (
        for_input,
        for_input,
    )


try:
    from mikro.api.schema import (
        Search_representationQuery,
        Search_sampleQuery,
        Search_tagsQuery,
    )
    from rekuest.widgets import SearchWidget

    MY_TOP_REPRESENTATIONS = SearchWidget(
        query=Search_representationQuery.Meta.document, ward="mikro"
    )

    MY_TOP_SAMPLES = SearchWidget(query=Search_sampleQuery.Meta.document, ward="mikro")

    TAGS_WIDGET = SearchWidget(query=Search_tagsQuery.Meta.document, ward="mikro")

    def ColumnWidget(for_input: str, **kwargs):
        return SearchWidget(query=build_column_query(for_input), ward="mikro", **kwargs)

    def RoiWidget(for_input: str, **kwargs):
        return SearchWidget(query=build_roi_query(for_input), ward="mikro", **kwargs)

except ImportError:
    pass
