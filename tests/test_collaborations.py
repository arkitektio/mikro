"""Collaborations are lok's, named by one key across services: mikro keeps its row of one."""

import uuid

import pytest

from mikro.api.schema import CollaborationObjectRef

from .conftest import DeployedMikro


@pytest.mark.integration
def test_add_many_makes_the_collaboration_under_its_key(
    deployed_app: DeployedMikro,
) -> None:
    """The first objects put in make mikro's row of the collaboration, by lok's key."""
    mikro = deployed_app.mikro
    first = mikro.create_folder(name="collaboration_folder_one")
    second = mikro.create_folder(name="collaboration_folder_two")
    key = str(uuid.uuid4())

    collaboration = mikro.add_many_to_collaboration(
        collaboration=key,
        objects=[
            CollaborationObjectRef(identifier="@mikro/folder", object=first.id),
            CollaborationObjectRef(identifier="@mikro/folder", object=second.id),
        ],
        name="shared folders",
    )

    assert collaboration.key == key
    assert collaboration.name == "shared folders"
    assert collaboration.item_count == 2
    assert mikro.get_collaboration(key=key).id == collaboration.id
    assert any(c.key == key for c in mikro.list_collaborations())


@pytest.mark.integration
def test_remove_takes_an_object_out(deployed_app: DeployedMikro) -> None:
    """One object goes in by hand and comes out again."""
    mikro = deployed_app.mikro
    folder = mikro.create_folder(name="collaboration_filtered_folder")
    key = str(uuid.uuid4())

    added = mikro.add_to_collaboration(
        collaboration=key, identifier="@mikro/folder", object=folder.id
    )
    assert added.item_count == 1

    removed = mikro.remove_from_collaboration(
        collaboration=key, identifier="@mikro/folder", object=folder.id
    )
    assert removed.item_count == 0


@pytest.mark.integration
def test_a_dry_run_share_of_an_unknown_workflow_adds_nothing(
    deployed_app: DeployedMikro,
) -> None:
    """A workflow mikro saw nothing of puts nothing in, and a dry run writes nothing."""
    key = str(uuid.uuid4())

    share = deployed_app.mikro.share_workflow(
        collaboration=key, root_task=str(uuid.uuid4()), dry_run=True
    )

    assert share.dry_run
    assert share.collaboration == key
    assert share.added == ()
    assert share.skipped == ()
