"""mikro's structures: what it can send across a node boundary, and how.

Nothing here needs a server. Each type is declared once, with the expander that
fetches it back, so there is no second list to drift from -- which is what the
old ``EXPANDERS``-versus-``STRUCTURES`` test existed to catch.
"""

import pytest

pytest.importorskip("rekuest")

from arkitekt_spec.declare.app import AppRegistry  # noqa: E402
from arkitekt_spec.declare.structures.types import is_valid_identifier  # noqa: E402

from mikro import arkitekt as declared  # noqa: E402

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
    registered = set(declared.registry.structure_registry.identifier_structure_map)
    assert registered == IDENTIFIERS


def test_every_identifier_is_one_the_server_accepts() -> None:
    assert [i for i in IDENTIFIERS if not is_valid_identifier(i)] == []


def test_every_structure_knows_how_to_expand_itself() -> None:
    """An expander, and the client it needs named in its own signature."""
    for structure in declared.registry.structure_registry.structures():
        assert structure.aexpand is not None, structure.identifier
        assert structure.injects, f"{structure.identifier} asks for no client"


def test_merging_stamps_the_service_that_owns_them() -> None:
    """The identifier only hints at the service; the merge states it."""
    app = AppRegistry()
    app.merge(declared.registry, service="mikro")

    services = {s.service for s in app.structure_registry.structures()}
    assert services == {"mikro"}


def test_a_lens_and_a_dataset_say_how_they_are_described() -> None:
    """What lets a run test a lens against a port's Requires and Provides."""
    from mikro.arkitekt.specs import lens_descriptors

    structures = declared.registry.structure_registry
    assert structures.get_fullfilled_structure("@mikro/arraylens").describe is lens_descriptors
    assert structures.get_fullfilled_structure("@mikro/arraydataset").describe is lens_descriptors
    # Nothing else carries descriptors a port could constrain on.
    described = {i for i, s in structures.identifier_structure_map.items() if s.describe}
    assert described == {"@mikro/arraylens", "@mikro/arraydataset", "@mikro/annotation", "@mikro/metric"}


def test_an_annotation_is_described_by_its_shape_and_the_axes_it_is_drawn_in() -> None:
    """The keys the server declares for `@mikro/annotation`, in the schema's spelling."""
    from types import SimpleNamespace

    from mikro.api.schema import AnnotationKind, AxisType
    from mikro.arkitekt.specs import annotation_descriptors

    structures = declared.registry.structure_registry
    assert structures.get_fullfilled_structure("@mikro/annotation").describe is annotation_descriptors

    plane = SimpleNamespace(axes=[SimpleNamespace(type=AxisType.SPACE), SimpleNamespace(type=AxisType.SPACE)])
    box = SimpleNamespace(kind=AnnotationKind.RECTANGLE, coordinate_system=plane)
    assert annotation_descriptors(box) == {
        "@mikro/annotation_kind": "RECTANGLE",
        "@mikro/n_space_axes": 2,
        "@mikro/n_time_axes": 0,
    }



def test_a_metric_is_described_by_its_key_its_value_and_what_it_is_about() -> None:
    """The keys the server declares for `@mikro/metric`: a quantity says magnitude and unit, a code its code."""
    from types import SimpleNamespace

    from mikro.arkitekt.specs import metric_descriptors

    structures = declared.registry.structure_registry
    assert structures.get_fullfilled_structure("@mikro/metric").describe is metric_descriptors

    target = SimpleNamespace(identifier="@mikro/arraydataset", object="3")
    quantity = SimpleNamespace(key="my_app/area", magnitude=12.0, unit="micrometer ** 2", code=None, target=target)
    assert metric_descriptors(quantity) == {
        "@mikro/metric_key": "my_app/area",
        "@mikro/magnitude": 12.0,
        "@mikro/unit": "micrometer ** 2",
        "@mikro/target_identifier": "@mikro/arraydataset",
        "@mikro/target_object": "3",
    }
    code = SimpleNamespace(key="segmenter_v2/class", magnitude=None, unit=None, code="segmenter_v2/class_3", target=target)
    assert metric_descriptors(code) == {
        "@mikro/metric_key": "segmenter_v2/class",
        "@mikro/metric_code": "segmenter_v2/class_3",
        "@mikro/target_identifier": "@mikro/arraydataset",
        "@mikro/target_object": "3",
    }


def test_a_metric_is_picked_by_its_key_narrowed_by_the_ports_constraints() -> None:
    from arkitekt_spec.scalars import get_search_query_variables

    widget = declared.registry.structure_registry.get_fullfilled_structure("@mikro/metric").default_widget
    assert widget is not None and widget.kind == "SEARCH" and widget.ward == "mikro"
    assert get_search_query_variables(widget.query)[:3] == ["search", "values", "requires"]

def test_every_structure_class_the_server_identifies_says_so_itself() -> None:
    """`__identifier__` (turms over `@identified`) agrees with the identifier each class is registered under."""
    stamped = {
        identifier: getattr(structure.cls, "__identifier__", None)
        for identifier, structure in declared.registry.structure_registry.identifier_structure_map.items()
    }
    assert {i: s for i, s in stamped.items() if s is not None} == {i: i for i, s in stamped.items() if s is not None}
    assert any(s is not None for s in stamped.values())

def test_a_lens_structure_is_the_array_lens_and_every_kind_has_its_own() -> None:
    """`@mikro/arraylens` is pixels: a port typed on it is never handed a table lens."""
    from mikro.api import schema

    structures = declared.registry.structure_registry.identifier_structure_map
    kinds = {
        "@mikro/arraylens": schema.ArrayLens,
        "@mikro/tablelens": schema.TableLens,
        "@mikro/sparselens": schema.SparseLens,
        "@mikro/meshlens": schema.MeshLens,
        "@mikro/networklens": schema.NetworkLens,
        "@mikro/annotationlens": schema.AnnotationLens,
    }
    assert {i: structures[i].cls for i in kinds} == kinds
    assert {f.Meta.type for f in kinds.values()} == {
        "ArrayLens", "TableLens", "SparseLens", "MeshLens", "NetworkLens", "AnnotationLens",
    }


def test_every_lens_kind_and_an_annotation_are_picked_by_a_search_that_takes_the_ports_constraints() -> None:
    """A port typed on a lens or an annotation gets a picker, and the picker's query has
    a `$requires` for the frontend to fill from the port: one widget per structure
    then offers each port only what that port accepts."""
    from arkitekt_spec.scalars import get_search_query_variables

    structures = declared.registry.structure_registry
    kinds = {"array": "ARRAY", "table": "TABLE", "sparse": "SPARSE", "mesh": "MESH", "network": "NETWORK", "annotation": "ANNOTATION"}
    for name, kind in kinds.items():
        widget = structures.get_fullfilled_structure(f"@mikro/{name}lens").default_widget
        assert widget is not None and widget.kind == "SEARCH" and widget.ward == "mikro", name
        assert get_search_query_variables(widget.query)[:3] == ["search", "values", "requires"], name
        # Each kind's query offers its own kind only: a table lens is never offered to a port typed on pixels.
        assert f"kind: {kind}," in widget.query, name

    annotation = structures.get_fullfilled_structure("@mikro/annotation").default_widget
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
    stated = {type(marker): (marker.key, str(getattr(marker.operator, "value", marker.operator)), marker.value) for marker in markers}
    assert stated == {Requires: ("@mikro/annotation_kind", "EQUALS", "PATH"), Provides: ("@mikro/annotation_kind", "EQUALS", "PATH")}


def test_a_lens_picked_after_an_annotation_is_narrowed_to_what_that_annotation_reaches() -> None:
    """`reachable_from("path")`: the catalog picker, its query naming the argument, the plain search over it as fallback."""
    from pathlib import Path

    from graphql import build_schema, parse, validate

    from mikro.api.schema import LensKind
    from mikro.arkitekt.widgets import reachable_from, reachable_lenses_query

    widget = reachable_from("path")
    assert widget.kind == "CUSTOM" and widget.component == "StructurePicker"
    assert widget.dependencies == ("path",)
    props = {prop.key: prop.static_value for prop in widget.props}
    assert props["ward"] == "mikro" and props["bind"] == "value"
    assert "reachableFrom: $path" in props["query"] and "kind: ARRAY" in props["query"]
    assert widget.fallback.kind == "SEARCH" and widget.fallback.dependencies == ("path",)

    # The query is text, written here and not generated: held to the schema the client was generated from.
    # `assume_valid_sdl`: the dump carries federation directives (`@key`, `@link`) it does not define.
    schema = build_schema((Path(declared.__file__).parents[1] / "api" / "schema.graphql").read_text(), assume_valid_sdl=True)
    for kind in LensKind:
        assert validate(schema, parse(reachable_lenses_query("shape", kind))) == [], kind
        assert f"kind: {kind.value}," in reachable_lenses_query("shape", kind)

    for bad in ("search", "values", "requires", "my path", "1st", "a/b"):
        with pytest.raises(ValueError, match="reachable_from"):
            reachable_from(bad)
