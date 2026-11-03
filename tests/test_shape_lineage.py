"""A shape made from a shape, through the client: the link, the preflight, the cascade."""

import pytest

from mikro.api.schema import AnnotationKind, AnnotationRelation, AnnotationSourceInput, AxisInput, AxisType
from mikro.mikro import Mikro

ROUGH = [[1.0, 1.0], [2.0, 3.0], [3.0, 2.0], [5.0, 5.0]]
SMOOTH = [[1.0, 1.0], [2.5, 2.5], [5.0, 5.0]]


@pytest.mark.integration
def test_a_refined_path_is_linked_and_goes_only_with_its_source(mikro: Mikro) -> None:
    """`derived_from` links it; a plain delete of the source is refused; `cascade` takes both."""
    collection = mikro.create_annotation_collection(
        name="shape lineage", axes=[AxisInput(name="y", type=AxisType.SPACE), AxisInput(name="x", type=AxisType.SPACE)]
    )
    rough = mikro.create_annotation(kind=AnnotationKind.PATH, vectors=ROUGH, collection=collection.id, name="rough")
    smooth = mikro.create_annotation(
        kind=AnnotationKind.PATH,
        vectors=SMOOTH,
        collection=collection.id,
        name="rough · smoothed",
        derived_from=[AnnotationSourceInput(annotation=rough.id, relation=AnnotationRelation.REFINED, reason="smoothed")],
    )
    assert smooth.source_ids == (rough.id,)

    lineage = mikro.get_annotation_lineage(id=rough.id)
    assert [shape.id for shape in lineage.derived_annotations] == [smooth.id]

    preflight = mikro.preflight_delete_annotation(id=rough.id)
    assert preflight.needs_cascade and preflight.deletable
    assert [casualty.key for casualty in preflight.casualties] == [f"annotation:{smooth.id}"]

    with pytest.raises(Exception, match="were made from it"):
        mikro.delete_annotation(id=rough.id)
    mikro.delete_annotation(id=rough.id, cascade=True)

    assert mikro.get_annotations(filters={"ids": [rough.id, smooth.id]}) == ()
