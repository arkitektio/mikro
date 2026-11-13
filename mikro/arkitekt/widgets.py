"""Widgets for an action's mikro arguments, beyond the plain search each structure ships with.

    from mikro.arkitekt.widgets import overlapping

    @app.action
    def straighten_path(
        path: PathAnnotation,
        lens: Annotated[Volume, overlapping("path")],
    ): ...

``mikro.arkitekt`` imports ``arkitekt_spec`` at module level, like the rest of
this subpackage, so it is not exported from ``mikro/__init__.py``.
"""

import re

from arkitekt_spec.actions import AssignWidgetInput
from arkitekt_spec.declare.widgets import StructurePicker
from arkitekt_spec.scalars import RESERVED_SEARCH_VARIABLES

from mikro.api.schema import LensKind

_NAME = re.compile(r"^[_A-Za-z][_0-9A-Za-z]*$")

# The lens search of `graphql/queries/lens.graphql`, with one more variable: the
# annotation the lenses are narrowed by, under one of the `LensFilter` keys that take
# an annotation. Text rather than a document, because that variable is named after
# the app's own argument.
_LENSES_BY_ANNOTATION = """
query %(operation)s(
  $search: String
  $values: [ID!]
  $requires: [DescriptorConstraintInput!]
  $%(argument)s: ID
  $limit: Int
  $offset: Int = 0
) {
  options: lenses(
    filters: { kind: %(kind)s, search: $search, ids: $values, requires: $requires, %(filter)s: $%(argument)s }
    pagination: { limit: $limit, offset: $offset }
  ) {
    value: id
    label: title
    description: detail
    group: origin
  }
}
"""


def _lenses_by_annotation(widget: str, operation: str, filter_key: str, argument: str, kind: LensKind) -> str:
    if not _NAME.match(argument) or argument in RESERVED_SEARCH_VARIABLES:
        raise ValueError(
            f"{widget}({argument!r}): name the annotation argument of the action. It becomes a variable of the "
            f"search, so it must be a plain name and none of {sorted(RESERVED_SEARCH_VARIABLES)}."
        )
    return _LENSES_BY_ANNOTATION % {
        "operation": operation,
        "filter": filter_key,
        "argument": argument,
        "kind": getattr(kind, "value", kind),
    }


def reachable_lenses_query(argument: str, kind: LensKind = LensKind.ARRAY) -> str:
    """The query behind :func:`reachable_from`: the lenses of one kind an annotation reaches.

    Args:
        argument: The name of the variable that receives the annotation's id.
        kind: The kind of lens listed.

    Returns:
        The query, as text.
    """
    return _lenses_by_annotation("reachable_from", "SearchReachableLenses", "reachableFrom", argument, kind)


def overlapping_lenses_query(argument: str, kind: LensKind = LensKind.ARRAY) -> str:
    """The query behind :func:`overlapping`: the lenses of one kind that hold data where an annotation is.

    Args:
        argument: The name of the variable that receives the annotation's id.
        kind: The kind of lens listed.

    Returns:
        The query, as text.
    """
    return _lenses_by_annotation("overlapping", "SearchOverlappingLenses", "overlapsAnnotation", argument, kind)


def reachable_from(argument: str, *, kind: LensKind = LensKind.ARRAY) -> AssignWidgetInput:
    """The widget of a lens argument that is picked after an annotation argument, loosely.

    Once that annotation is chosen, only the lenses it reaches through the
    transformation graph are offered: the lenses over the data it was drawn
    on, and over data registered into a space its collection reaches -- also a
    crop or a channel the shape lies outside of. To offer only lenses that hold
    data where the shape is, use :func:`overlapping`. What the argument's type
    requires (a ``Volume``) still applies. Until it is chosen every lens the
    type accepts is offered, and the user can lift the narrowing, which is the
    way to a tracing that was never registered.

    Args:
        argument: The name of the action's annotation argument.
        kind: The kind of lens the argument takes; an array lens by default.

    Returns:
        The widget, to put in the argument's ``Annotated``.
    """
    return StructurePicker(reachable_lenses_query(argument, kind), "mikro", [argument])


def overlapping(argument: str, *, kind: LensKind = LensKind.ARRAY) -> AssignWidgetInput:
    """The widget of a lens argument that must hold data where an annotation argument is.

    Once that annotation is chosen, only the lenses whose extent overlaps the
    shape are offered: of the lenses :func:`reachable_from` offers, those with
    any part of the shape's box inside them, compared in the nearest space both
    are registered into. A crop or a channel window the shape lies outside of is
    not offered, and neither is a lens the server cannot bound there (placed
    only per index, or across a warp). What the argument's type requires (a
    ``Volume``) still applies. Until the annotation is chosen every lens the
    type accepts is offered, and the user can lift the narrowing.

    Args:
        argument: The name of the action's annotation argument.
        kind: The kind of lens the argument takes; an array lens by default.

    Returns:
        The widget, to put in the argument's ``Annotated``.
    """
    return StructurePicker(overlapping_lenses_query(argument, kind), "mikro", [argument])
