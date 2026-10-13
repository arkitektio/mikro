"""Widgets for an action's mikro arguments, beyond the plain search each structure ships with.

    from mikro.arkitekt.widgets import reachable_from

    @app.action
    def straighten_path(
        path: PathAnnotation,
        lens: Annotated[Volume, reachable_from("path")],
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
# annotation the lenses must be reachable from. Text rather than a document,
# because that variable is named after the app's own argument.
_REACHABLE_LENSES = """
query SearchReachableLenses(
  $search: String
  $values: [ID!]
  $requires: [DescriptorConstraintInput!]
  $%(argument)s: ID
  $limit: Int
  $offset: Int = 0
) {
  options: lenses(
    filters: { kind: %(kind)s, search: $search, ids: $values, requires: $requires, reachableFrom: $%(argument)s }
    pagination: { limit: $limit, offset: $offset }
  ) {
    value: id
    label
  }
}
"""


def reachable_lenses_query(argument: str, kind: LensKind = LensKind.ARRAY) -> str:
    """The query behind :func:`reachable_from`: the lenses of one kind an annotation reaches.

    Args:
        argument: The name of the variable that receives the annotation's id.
        kind: The kind of lens listed.

    Returns:
        The query, as text.
    """
    if not _NAME.match(argument) or argument in RESERVED_SEARCH_VARIABLES:
        raise ValueError(
            f"reachable_from({argument!r}): name the annotation argument of the action. It becomes a variable of the "
            f"search, so it must be a plain name and none of {sorted(RESERVED_SEARCH_VARIABLES)}."
        )
    return _REACHABLE_LENSES % {"argument": argument, "kind": getattr(kind, "value", kind)}


def reachable_from(argument: str, *, kind: LensKind = LensKind.ARRAY) -> AssignWidgetInput:
    """The widget of a lens argument that is picked after an annotation argument.

    Once that annotation is chosen, only the lenses it reaches through the
    transformation graph are offered: the lenses over the data it was drawn
    on, and over data registered into a space its collection reaches. What
    the argument's type requires (a ``Volume``) still applies. Until it is
    chosen every lens the type accepts is offered, and the user can lift the
    narrowing, which is the way to a tracing that was never registered.

    Args:
        argument: The name of the action's annotation argument.
        kind: The kind of lens the argument takes; an array lens by default.

    Returns:
        The widget, to put in the argument's ``Annotated``.
    """
    return StructurePicker(reachable_lenses_query(argument, kind), "mikro", [argument])
