"""Default Widgets

This Module provides default widgets that can be used with the mikro app in an arkitekt
context.

Attributes:
    MY_TOP_REPRESENTATIONS (SearchWidget): The top representations for the currently active user
    MY_TOP_SAMPLES (SearchWidget): The top samples for the currently active user
"""


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

except:
    pass
