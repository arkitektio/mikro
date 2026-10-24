"""Metrics, as a client records them: the object a metric is about is given as the object.

The first tests need no server: what reaches the wire is checked through the client's own
serializer, the step every call takes before its middlewares. The rest record metrics on
the test stack (a server image with metrics: ``MIKRO_SERVICE_TAG``) and read them back.
"""

import numpy as np
import pytest
import xarray as xr

from mikro.api.schema import (
    Annotation,
    AnnotationKind,
    ArrayDataset,
    ArrayLens,
    CreateMetricMutation,
    CreateMetricsMutation,
    MetricFilter,
    MetricInput,
    MetricTargetFilter,
    MetricTargetInput,
    SparseDataset,
    TableDataset,
)
from mikro.mikro import Mikro

# Most of these record against a real mikro in Docker.
pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("cls", "identifier", "id"),
    [
        (ArrayDataset, "@mikro/arraydataset", "3"),
        (TableDataset, "@mikro/tabledataset", "4"),
        (SparseDataset, "@mikro/sparsedataset", "5"),
        # An annotation's id is a uuid.
        (Annotation, "@mikro/annotation", "0192f3c4-7d1e-7b2a-9c4d-5e6f7a8b9c0d"),
    ],
)
def test_a_target_is_the_structure_an_object_travels_as_and_its_id(cls: type, identifier: str, id: str) -> None:
    target = MetricTargetInput.model_validate(cls.model_construct(id=id))
    assert (target.identifier, target.object) == (identifier, id)


def test_a_spelled_out_target_is_taken_as_it_is() -> None:
    spelled = {"identifier": "@mikro/arraydataset", "object": "3"}
    assert MetricTargetInput.model_validate(spelled) == MetricTargetInput.model_validate(ArrayDataset.model_construct(id="3"))
    given = MetricTargetInput(identifier="@mikro/annotation", object="7")
    assert MetricTargetInput.model_validate(given) is given


def test_a_nested_selection_is_a_target_as_its_type_is() -> None:
    """`lens.dataset` is a class of its own, not a subclass of the `ArrayDataset` fragment."""
    from mikro.api.schema import ArrayLensDataset

    assert not issubclass(ArrayLensDataset, ArrayDataset)
    target = MetricTargetInput.model_validate(ArrayLensDataset.model_construct(id="3"))
    assert (target.identifier, target.object) == ("@mikro/arraydataset", "3")


def test_an_object_no_structure_identifies_is_refused_by_name() -> None:
    from mikro.api.schema import Slice

    with pytest.raises(ValueError, match="not a str, which no structure identifies"):
        MetricTargetInput.model_validate("3")
    with pytest.raises(ValueError, match="not a Slice, which no structure identifies"):
        MetricTargetInput.model_validate(Slice.model_construct(axis="x"))


def test_an_object_of_another_structure_is_left_to_the_server_to_refuse() -> None:
    """Which structures a metric may be about is the server's to say, in prose."""
    target = MetricTargetInput.model_validate(ArrayLens.model_construct(id="9"))
    assert target.identifier == "@mikro/arraylens"


def test_a_quantity_reaches_the_wire_with_its_target_spelled_out() -> None:
    dataset = ArrayDataset.model_construct(id="3")
    wire = Mikro._serialize(
        CreateMetricMutation,
        {"input": {"target": dataset, "key": "my_app/mean_intensity", "magnitude": 3.2, "unit": "µm"}},
    )
    assert wire == {
        "input": {
            "target": {"identifier": "@mikro/arraydataset", "object": "3"},
            "key": "my_app/mean_intensity",
            "magnitude": 3.2,
            "unit": "µm",
        }
    }


def test_a_batch_coerces_every_target_and_a_correction_names_what_it_supersedes() -> None:
    old = "41"
    wire = Mikro._serialize(
        CreateMetricsMutation,
        {
            "input": {
                "metrics": [
                    MetricInput(target=ArrayDataset.model_construct(id="3"), key="my_app/area", magnitude=12.0, unit="µm²"),
                    MetricInput(target=Annotation.model_construct(id="0192f3c4-7d1e-7b2a-9c4d-5e6f7a8b9c0d"), key="segmenter_v2/class", code="segmenter_v2/class_3"),
                    MetricInput(target=ArrayDataset.model_construct(id="3"), key="my_app/area", magnitude=12.5, unit="µm²", supersedes=old),
                ]
            }
        },
    )
    metrics = wire["input"]["metrics"]
    assert [m["target"]["identifier"] for m in metrics] == ["@mikro/arraydataset", "@mikro/annotation", "@mikro/arraydataset"]
    assert metrics[1]["code"] == "segmenter_v2/class_3" and "magnitude" not in metrics[1]
    assert metrics[2]["supersedes"] == old


# --- On the stack -------------------------------------------------------------------


def _dataset(mikro: Mikro, name: str) -> ArrayDataset:
    data = np.random.default_rng(3).random((8, 8)).astype("float32")
    return mikro.create_array_dataset(data=xr.DataArray(data, dims=("y", "x")), scales=[], name=name, axes=["y", "x"])


def _annotation(mikro: Mikro, name: str) -> Annotation:
    collection = mikro.create_annotation_collection(name=name, axes=["y", "x"])
    return mikro.create_annotation(kind=AnnotationKind.POINT, vectors=[[1.0, 2.0]], collection=collection.id, name=name)


def test_a_quantity_is_recorded_about_a_dataset_and_read_back_by_its_target(mikro: Mikro) -> None:
    dataset = _dataset(mikro, "metrics_quantity")
    metric = mikro.create_metric(target=dataset, key="mikro_tests/mean_intensity", magnitude=0.5, unit="µm")

    assert (metric.target.identifier, metric.target.object) == ("@mikro/arraydataset", dataset.id)
    assert (metric.magnitude, metric.code, metric.supersedes) == (0.5, None, None)
    assert metric.unit  # normalized by the server, as pint reads it
    assert mikro.get_metric(metric.id).key == "mikro_tests/mean_intensity"

    about = MetricFilter(target=MetricTargetFilter(identifier="@mikro/arraydataset", object=dataset.id))
    assert [m.id for m in mikro.list_metrics(filters=about)] == [metric.id]


def test_a_code_is_recorded_about_an_annotation(mikro: Mikro) -> None:
    annotation = _annotation(mikro, "metrics_code")
    metric = mikro.create_metric(target=annotation, key="mikro_tests.segmenter/class", code="segmenter_v2/class_3")
    assert (metric.target.identifier, metric.target.object) == ("@mikro/annotation", annotation.id)
    assert (metric.code, metric.magnitude, metric.unit) == ("segmenter_v2/class_3", None, None)


def test_a_batch_is_recorded_about_several_objects_at_once(mikro: Mikro) -> None:
    dataset, annotation = _dataset(mikro, "metrics_batch"), _annotation(mikro, "metrics_batch")
    created = mikro.create_metrics(
        metrics=[
            MetricInput(target=dataset, key="mikro_tests/area", magnitude=float(i), unit="µm**2") for i in range(3)
        ]
        + [MetricInput(target=annotation, key="mikro_tests/class", code="a")],
    )
    assert [m.target.identifier for m in created] == ["@mikro/arraydataset"] * 3 + ["@mikro/annotation"]
    assert sorted(m.magnitude for m in created[:3]) == [0.0, 1.0, 2.0]


def test_a_corrected_metric_is_deleted_once_its_correction_is(mikro: Mikro) -> None:
    dataset = _dataset(mikro, "metrics_correction")
    wrong = mikro.create_metric(target=dataset, key="mikro_tests/area", magnitude=1.0, unit="µm**2")
    right = mikro.create_metric(target=dataset, key="mikro_tests/area", magnitude=2.0, unit="µm**2", supersedes=wrong)
    assert right.supersedes is not None and right.supersedes.id == wrong.id

    assert mikro.delete_metric(right.id) == right.id
    assert mikro.delete_metric(wrong.id) == wrong.id


@pytest.mark.xfail(
    strict=True,
    reason="mikro server: deleting a PROTECTed metric fails with Django's SynchronousOnlyOperation "
    "('You cannot call this from an async context') instead of saying why",
)
def test_a_corrected_metric_cannot_be_deleted_while_its_correction_stands(mikro: Mikro) -> None:
    dataset = _dataset(mikro, "metrics_protected")
    wrong = mikro.create_metric(target=dataset, key="mikro_tests/area", magnitude=1.0, unit="µm**2")
    mikro.create_metric(target=dataset, key="mikro_tests/area", magnitude=2.0, unit="µm**2", supersedes=wrong)
    with pytest.raises(Exception, match="(?i)supersed|correct|protect"):
        mikro.delete_metric(wrong.id)



def test_a_picker_searches_metrics_by_key_and_narrows_by_the_ports_constraints(mikro: Mikro) -> None:
    from mikro.api.schema import DescriptorConstraintInput, DescriptorOperator
    from mikro.arkitekt.specs import METRIC_KEY

    dataset = _dataset(mikro, "metrics_search")
    area = mikro.create_metric(target=dataset, key="mikro_tests.search/area", magnitude=1.0, unit="µm**2")
    count = mikro.create_metric(target=dataset, key="mikro_tests.search/count", magnitude=4.0, unit="dimensionless")

    # A frontend hands a null search when nothing is typed: the picker still offers everything.
    offered = {option.value for option in mikro.search_metrics(search=None, limit=1000)}
    assert {area.id, count.id} <= offered
    assert {option.value: option.label for option in mikro.search_metrics(search="mikro_tests.search/ar")} == {area.id: area.key}
    assert [option.value for option in mikro.search_metrics(values=[count.id])] == [count.id]

    of_a_key = [DescriptorConstraintInput(key=METRIC_KEY, operator=DescriptorOperator.EQUALS, value="mikro_tests.search/count")]
    assert {option.value for option in mikro.search_metrics(requires=of_a_key, limit=1000)} == {count.id}

@pytest.mark.parametrize(
    ("value", "refusal"),
    [
        ({"key": "mikro_tests/both", "magnitude": 1.0, "unit": "µm", "code": "x"}, "both"),
        ({"key": "mikro_tests/neither"}, "neither"),
        ({"key": "no_namespace", "code": "x"}, "namespace"),
    ],
)
def test_the_server_refuses_what_is_not_one_value_under_a_namespaced_key(mikro: Mikro, value: dict, refusal: str) -> None:
    dataset = _dataset(mikro, f"metrics_refused_{refusal}")
    with pytest.raises(Exception, match=refusal):
        mikro.create_metric(target=dataset, **value)
