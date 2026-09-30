"""The generated Layer fragment classes: no arm's nested class may shadow another's.

turms names a nested selection's class after its field, so two arms of the Layer interface
fragment that select the same field spelled the same way get one module-level name, and the
LAST definition wins every reference. Identical copies are harmless; differing ones meant a
mesh layer's `collection` and pickers were validated against the network/point layer's
classes and refused on their __typename.
"""

import ast
from pathlib import Path

import mikro.api.schema as schema


def test_every_repeated_generated_class_is_identical() -> None:
    tree = ast.parse(Path(schema.__file__).read_text())
    bodies: dict[str, list[list[str]]] = {}
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            body = [ast.unparse(s) for s in node.body if not isinstance(s, ast.Expr)]
            bodies.setdefault(node.name, []).append(body)

    differing = [name for name, defs in bodies.items() if any(d != defs[0] for d in defs)]

    assert differing == [], (
        f"{differing} are generated more than once with different fields; alias the field "
        "in graphql/fragments/layer.graphql so each arm gets its own class"
    )


def test_a_mesh_layer_with_a_collection_and_pickers_parses() -> None:
    fields = {
        "__typename": "MeshColorBy",
        "kind": "COLUMN",
        "table": "1",
        "column": "area",
        "dataset": None,
        "at": [],
        "joinPath": [],
        "colormap": None,
        "min": None,
        "max": None,
        "label": None,
    }
    collection = schema.LayerCollection.model_validate(
        {"__typename": "MeshCollection", "id": "7", "version": "3"}
    )
    color_by_field = schema.LayerMeshLayer.model_fields["color_bys"].annotation.__args__[0]
    color_by = color_by_field.model_validate(fields)

    assert collection.version == "3"
    assert color_by.typename == "MeshColorBy"
