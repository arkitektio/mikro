"""mikro's structures: what it can send across a node boundary, and how.

Nothing here needs a server. Each type is declared once, with the expander that
fetches it back, so there is no second list to drift from -- which is what the
old ``EXPANDERS``-versus-``STRUCTURES`` test existed to catch.
"""

import pytest

pytest.importorskip("rekuest")

from arkitekt_spec.declare.client import client_of  # noqa: E402
from arkitekt_spec.declare.structures.types import is_valid_identifier  # noqa: E402

from mikro import Mikro  # noqa: E402

DECLARED = client_of(Mikro)
assert DECLARED is not None
STRUCTURES = {s.identifier: s for s in DECLARED.structures}

#: The identifiers mikro puts on the wire. Changing one is a cross-service change,
#: so they are written out rather than derived from the thing under test.
IDENTIFIERS = {
    "@mikro/animation",
    "@mikro/annotation",
    "@mikro/annotationcollection",
    "@mikro/annotationlens",
    "@mikro/arraydataset",
    "@mikro/chart",
    "@mikro/coordinatesystem",
    "@mikro/folder",
    "@mikro/file",
    "@mikro/arraylens",
    "@mikro/meshcollection",
    "@mikro/meshlens",
    "@mikro/metric",
    "@mikro/networkcollection",
    "@mikro/networklens",
    "@mikro/scene",
    "@mikro/scenesnapshot",
    "@mikro/sparsedataset",
    "@mikro/sparselens",
    "@mikro/tabledataset",
    "@mikro/tablelens",
    "@mikro/transformation",
}


def test_it_declares_exactly_the_identifiers_it_always_has() -> None:
    """The wire contract, guarded literally."""
    assert set(STRUCTURES) == IDENTIFIERS


def test_every_identifier_is_one_the_server_accepts() -> None:
    assert [i for i in IDENTIFIERS if not is_valid_identifier(i)] == []


def test_every_structure_is_expanded_by_mikro() -> None:
    """An expander, owned by the client it asks for."""
    for structure in STRUCTURES.values():
        assert structure.aexpand is not None, structure.identifier
        assert structure.owner is DECLARED, structure.identifier


def test_importing_mikro_marks_its_structures() -> None:
    """A plain import of the schema marks the classes: nothing else has to be imported."""
    import subprocess
    import sys

    script = (
        "from arkitekt_spec.declare.structures.declare import structure_of\n"
        "from mikro.api.schema import ArrayDataset\n"
        "assert structure_of(ArrayDataset).owner.cls.__name__ == 'Mikro'\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_every_structure_mikro_describes_is_described_by_what_was_fetched() -> None:
    """What lets a run test an object against a port's Requires and Provides, with no round trip of its own."""
    from mikro.arkitekt.specs import descriptors_of

    described = {i for i, s in STRUCTURES.items() if s.describe}
    # Every structure whose type has `descriptors`; a coordinate system and a transformation have none.
    assert "@mikro/arraylens" in described and "@mikro/file" in described
    assert not described & {"@mikro/coordinatesystem", "@mikro/transformation"}
    assert all(STRUCTURES[i].describe is descriptors_of for i in described)


def test_a_metric_is_picked_by_its_key_narrowed_by_the_ports_constraints() -> None:
    from arkitekt_spec.scalars import get_search_query_variables

    widget = STRUCTURES["@mikro/metric"].default_widget
    assert widget is not None and widget.kind == "SEARCH" and widget.ward == "mikro"
    assert get_search_query_variables(widget.query)[:3] == [
        "search",
        "values",
        "requires",
    ]


def test_every_structure_class_the_server_identifies_says_so_itself() -> None:
    """`__identifier__` (turms over `@identified`) agrees with the identifier each class is registered under."""
    stamped = {
        identifier: getattr(structure.cls, "__identifier__", None)
        for identifier, structure in STRUCTURES.items()
    }
    assert {i: s for i, s in stamped.items() if s is not None} == {
        i: i for i, s in stamped.items() if s is not None
    }
    assert any(s is not None for s in stamped.values())


def test_a_lens_structure_is_the_array_lens_and_every_kind_has_its_own() -> None:
    """`@mikro/arraylens` is pixels: a port typed on it is never handed a table lens."""
    from mikro.api import schema

    kinds = {
        "@mikro/arraylens": schema.ArrayLens,
        "@mikro/tablelens": schema.TableLens,
        "@mikro/sparselens": schema.SparseLens,
        "@mikro/meshlens": schema.MeshLens,
        "@mikro/networklens": schema.NetworkLens,
        "@mikro/annotationlens": schema.AnnotationLens,
    }
    assert {i: STRUCTURES[i].cls for i in kinds} == kinds
    assert {f.Meta.type for f in kinds.values()} == {
        "ArrayLens",
        "TableLens",
        "SparseLens",
        "MeshLens",
        "NetworkLens",
        "AnnotationLens",
    }


def test_every_lens_kind_and_an_annotation_are_picked_by_a_search_that_takes_the_ports_constraints() -> (
    None
):
    """A port typed on a lens or an annotation gets a picker, and the picker's query has
    a `$requires` for the frontend to fill from the port: one widget per structure
    then offers each port only what that port accepts."""
    from arkitekt_spec.scalars import get_search_query_variables

    kinds = {
        "array": "ARRAY",
        "table": "TABLE",
        "sparse": "SPARSE",
        "mesh": "MESH",
        "network": "NETWORK",
        "annotation": "ANNOTATION",
    }
    for name, kind in kinds.items():
        widget = STRUCTURES[f"@mikro/{name}lens"].default_widget
        assert (
            widget is not None and widget.kind == "SEARCH" and widget.ward == "mikro"
        ), name
        assert get_search_query_variables(widget.query)[:3] == [
            "search",
            "values",
            "requires",
        ], name
        # Each kind's query offers its own kind only: a table lens is never offered to a port typed on pixels.
        assert f"kind: {kind}," in widget.query, name

    annotation = STRUCTURES["@mikro/annotation"].default_widget
    assert annotation is not None and annotation.kind == "SEARCH"
    assert "requires" in get_search_query_variables(annotation.query)


def test_a_path_is_an_annotation_that_must_be_drawn_as_one() -> None:
    """`PathAnnotation` is the constraint a picker hands the server, spelled as the server declares the key."""
    from typing import get_args

    from arkitekt_spec.declare.annotations import Provides, Requires

    from mikro.api.schema import Annotation
    from mikro.arkitekt.specs import PathAnnotation

    cls, *markers = get_args(PathAnnotation)
    assert cls is Annotation
    stated = {
        type(marker): (
            marker.key,
            str(getattr(marker.operator, "value", marker.operator)),
            marker.value,
        )
        for marker in markers
    }
    assert stated == {
        Requires: ("@mikro/annotation_kind", "EQUALS", "PATH"),
        Provides: ("@mikro/annotation_kind", "EQUALS", "PATH"),
    }


def test_a_lens_picked_after_an_annotation_is_narrowed_to_what_that_annotation_reaches() -> (
    None
):
    """`reachable_from("path")`: the catalog picker, its query naming the argument, the plain search over it as fallback."""
    from graphql import build_schema, parse, validate
    from mikro.api.schema import LensKind
    from mikro.arkitekt.widgets import reachable_from, reachable_lenses_query

    widget = reachable_from("path")
    assert widget.kind == "CUSTOM" and widget.component == "StructurePicker"
    assert widget.dependencies == ("path",)
    props = {prop.key: prop.static_value for prop in widget.props}
    assert props["ward"] == "mikro" and props["bind"] == "value"
    assert "reachableFrom: $path" in props["query"] and "kind: ARRAY" in props["query"]
    assert widget.fallback.kind == "SEARCH" and widget.fallback.dependencies == (
        "path",
    )

    # The query is text, written here and not generated: held to the schema the client was generated from.
    # `assume_valid_sdl`: the dump carries federation directives (`@key`, `@link`) it does not define.
    schema = build_schema(DECLARED.get_graphql_schema(), assume_valid_sdl=True)
    for kind in LensKind:
        assert validate(schema, parse(reachable_lenses_query("shape", kind))) == [], (
            kind
        )
        assert f"kind: {kind.value}," in reachable_lenses_query("shape", kind)

    for bad in ("search", "values", "requires", "my path", "1st", "a/b"):
        with pytest.raises(ValueError, match="reachable_from"):
            reachable_from(bad)


def test_a_lens_picked_after_an_annotation_can_be_narrowed_to_lenses_holding_data_where_it_is() -> (
    None
):
    """`overlapping("path")`: the same picker, filtered by `overlapsAnnotation` instead of `reachableFrom`."""
    from graphql import build_schema, parse, validate
    from mikro.api.schema import LensKind
    from mikro.arkitekt.widgets import overlapping, overlapping_lenses_query

    widget = overlapping("path")
    assert (
        widget.kind == "CUSTOM"
        and widget.component == "StructurePicker"
        and widget.dependencies == ("path",)
    )
    query = {prop.key: prop.static_value for prop in widget.props}["query"]
    assert "overlapsAnnotation: $path" in query and "reachableFrom" not in query

    schema = build_schema(DECLARED.get_graphql_schema(), assume_valid_sdl=True)
    for kind in LensKind:
        assert validate(schema, parse(overlapping_lenses_query("shape", kind))) == [], (
            kind
        )

    with pytest.raises(ValueError, match="overlapping"):
        overlapping("requires")
