"""A fixture from a `.glb` on disk to a layer in a scene, against a real mikro.

The seam that is mikro's: `GltfLike` takes a path, the upload middleware puts the file in the
media store, and the server reads its header and boxes it. Everything below -- reading glTF,
placing by units -- is the server's and tested there.
"""

from pathlib import Path

import pytest
import trimesh

from mikro.api.schema import AxisType, LayerKind, PhysicalAxisInput, WindowInput

from .conftest import DeployedMikro

MM_AXES = [PhysicalAxisInput(name=axis, type=AxisType.SPACE, unit="millimeter") for axis in ("x", "y", "z")]


@pytest.fixture
def coverslip(tmp_path: Path) -> Path:
    """A 24 x 24 x 0.17 mm coverslip, as one binary glTF."""
    path = tmp_path / "coverslip.glb"
    path.write_bytes(trimesh.creation.box(extents=[24.0, 24.0, 0.17]).export(file_type="glb"))
    return path


@pytest.mark.integration
def test_a_glb_path_becomes_a_fixture_in_millimetres(deployed_app: DeployedMikro, coverslip: Path) -> None:
    """The path is uploaded, read, and boxed in the model's own units."""
    fixture = deployed_app.mikro.create_fixture(store=coverslip, axes=MM_AXES)

    assert fixture.label == "coverslip.glb", "an unnamed fixture is labelled by its file"
    assert [(axis.name, str(axis.unit)) for axis in fixture.coordinate_system.axes] == [("x", "millimeter"), ("y", "millimeter"), ("z", "millimeter")]
    assert fixture.full_lens is not None and fixture.full_lens.windows == ()
    assert fixture.bounds, "the server read the box off the file's accessors"


@pytest.mark.integration
def test_a_fixture_is_drawn_in_a_scene_over_its_space(deployed_app: DeployedMikro, coverslip: Path) -> None:
    """A layer draws through the whole lens; the colour override can be set and cleared."""
    mikro = deployed_app.mikro
    fixture = mikro.create_fixture(store=coverslip, axes=MM_AXES, name="Coverslip")
    assert fixture.full_lens is not None
    scene = mikro.create_scene(name="bench", coordinate_system=fixture.coordinate_system.id)

    layer = mikro.create_fixture_layer(scene=scene.id, lens=fixture.full_lens.id, material_color=[200, 220, 255, 255])
    assert layer.kind == LayerKind.FIXTURE
    assert layer.fixture is not None and layer.fixture.id == fixture.id
    assert layer.material_color == (200, 220, 255, 255)

    cleared = mikro.update_fixture_layer(id=layer.id, material_color=None, wireframe=True)
    assert cleared.material_color is None, "null returns to the model's own materials"
    assert cleared.wireframe is True


@pytest.mark.integration
def test_a_clip_box_is_one_lens_however_often_it_is_asked_for(deployed_app: DeployedMikro, coverslip: Path) -> None:
    """A lens is get-or-create, in the model's own axes."""
    mikro = deployed_app.mikro
    fixture = mikro.create_fixture(store=coverslip, axes=MM_AXES)
    windows = [WindowInput(axis="z", min=0.0, max=0.1)]

    first = mikro.create_fixture_lens(fixture=fixture.id, windows=windows)
    again = mikro.create_fixture_lens(fixture=fixture.id, windows=windows)

    assert again.id == first.id
    assert first.fixture.id == fixture.id
    assert [(window.axis, window.min, window.max) for window in first.windows] == [("z", 0.0, 0.1)]
    assert fixture.id in {option.value for option in mikro.search_fixtures(search="coverslip")}

    assert mikro.delete_fixture(id=fixture.id) == fixture.id
