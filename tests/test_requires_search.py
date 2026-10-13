"""The search a port's picker runs: the port's ``requires`` narrows what the server offers.

End to end, against the real service: the aliases in ``mikro.arkitekt.specs`` are turned
into the constraints a frontend hands on, and the lens and annotation searches answer with
exactly the objects a port typed on that alias accepts.
"""

from typing import get_args

import numpy as np
import pytest
import xarray as xr
from arkitekt_spec.declare.annotations import Requires

from mikro.api.schema import AnnotationKind, DescriptorConstraintInput, DescriptorOperator
from mikro.arkitekt.specs import Image, PathAnnotation, SingleChannelVolume, Volume
from mikro.mikro import Mikro

#: A substring every dataset of this module shares, so the search isolates them.
PREFIX = "requires_search_qzvkx"


def _requires(spec: object) -> list[DescriptorConstraintInput]:
    """A spec alias' `Requires`, in the input the search takes: what a frontend does with a port's constraints."""
    return [
        DescriptorConstraintInput(key=marker.key, operator=DescriptorOperator(str(getattr(marker.operator, "value", marker.operator))), value=marker.value)
        for marker in get_args(spec)[1:]
        if isinstance(marker, Requires)
    ]


@pytest.mark.integration
def test_a_lens_search_offers_what_the_port_requires(mikro: Mikro) -> None:
    volume = mikro.create_array_dataset(data=xr.DataArray(np.zeros((2, 4, 16, 16), dtype="uint8"), dims=["c", "z", "y", "x"]), scales=[], name=f"{PREFIX}_volume", axes=["c", "z", "y", "x"])
    image = mikro.create_array_dataset(data=xr.DataArray(np.zeros((16, 16), dtype="uint8"), dims=["y", "x"]), scales=[], name=f"{PREFIX}_image", axes=["y", "x"])
    whole, plane, channel = volume.lens(), volume.lens(z=1), volume.lens(c=0)
    flat = image.lens()

    def offered(spec: object) -> set[str]:
        return {option.value for option in mikro.search_array_lenses(search=PREFIX, requires=_requires(spec))}

    everything = {option.value for option in mikro.search_array_lenses(search=PREFIX)}
    assert {whole.id, plane.id, channel.id, flat.id} <= everything
    # A crop narrows an axis and never drops one: a plane of the stack still has three space axes.
    assert offered(Volume) == {whole.id, plane.id, channel.id}
    assert offered(SingleChannelVolume) == {channel.id}
    assert offered(Image) == {flat.id}

    options = mikro.search_array_lenses(values=[channel.id], requires=_requires(Volume))
    assert [option.value for option in options] == [channel.id]
    assert options[0].label, "a lens nobody named still has a label to show"


@pytest.mark.integration
def test_an_annotation_search_offers_the_paths_to_a_port_typed_on_paths(mikro: Mikro) -> None:
    image = mikro.create_array_dataset(data=xr.DataArray(np.zeros((16, 16), dtype="uint8"), dims=["y", "x"]), scales=[], name=f"{PREFIX}_canvas", axes=["y", "x"])
    scene = mikro.auto_visualize(lens=image.lens().id, name=f"{PREFIX}_scene")
    path = mikro.create_annotation(kind=AnnotationKind.PATH, vectors=[[0.0, 1.0, 1.0], [0.0, 4.0, 4.0], [0.0, 6.0, 2.0]], scene=scene.id, name=f"{PREFIX}_path")
    box = mikro.create_annotation(kind=AnnotationKind.RECTANGLE, vectors=[[0.0, 1.0, 1.0], [0.0, 4.0, 4.0]], scene=scene.id, name=f"{PREFIX}_box")

    assert {option.value for option in mikro.search_annotations(search=PREFIX)} == {path.id, box.id}
    assert {option.value for option in mikro.search_annotations(search=PREFIX, requires=_requires(PathAnnotation))} == {path.id}


@pytest.mark.integration
def test_the_reachable_lens_search_offers_the_lenses_of_the_image_a_path_was_drawn_on(mikro: Mikro) -> None:
    """The query `reachable_from("path")` ships, run as a frontend runs it: by text, with the path's id."""
    from mikro.arkitekt.widgets import reachable_lenses_query

    drawn_on = mikro.create_array_dataset(data=xr.DataArray(np.zeros((16, 16), dtype="uint8"), dims=["y", "x"]), scales=[], name=f"{PREFIX}_drawn_on", axes=["y", "x"])
    elsewhere = mikro.create_array_dataset(data=xr.DataArray(np.zeros((16, 16), dtype="uint8"), dims=["y", "x"]), scales=[], name=f"{PREFIX}_elsewhere", axes=["y", "x"])
    whole, crop, stranger = drawn_on.lens(), drawn_on.lens(y=slice(0, 4)), elsewhere.lens()
    scene = mikro.auto_visualize(lens=whole.id, name=f"{PREFIX}_reach_scene")
    path = mikro.create_annotation(kind=AnnotationKind.PATH, vectors=[[0.0, 8.0, 8.0], [0.0, 12.0, 12.0]], scene=scene.id, name=f"{PREFIX}_reach_path")

    query = reachable_lenses_query("path")

    def offered(**variables: object) -> set[str]:
        return {option["value"] for option in mikro.rath.query(query, {"search": PREFIX, **variables}).data["options"]}

    reached = offered(path=path.id)
    assert {whole.id, crop.id} <= reached, "a crop the path lies outside of is still data it can be read against"
    assert stranger.id not in reached
    # No annotation yet, or the narrowing lifted: the variable is null and narrows nothing.
    assert {whole.id, crop.id, stranger.id} <= offered(path=None)
    assert offered(path=path.id, requires=[{"key": "@mikro/n_space_axes", "operator": "EQUALS", "value": 3}]) == set()
