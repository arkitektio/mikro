"""The sparse-dataset path through the inputs themselves -- traits, and the picker over them.

Where ``test_sparse.py`` calls the check functions, this file goes through
``CreateSparseDatasetInput``, ``SparseAxisInput`` and ``SparseColorByInput``, which is where a
caller meets them: a refusal arrives as pydantic's ``ValidationError`` wrapping ours, so the
assertions are on the wrapped message.

Two things are under test that the function-level file cannot reach.

The first is **ordering**. ``funcs.execute`` validates the arguments at ``:94`` and hands them
to the upload middleware at ``:97``. A trait on the input therefore fires before a byte moves,
which is the whole argument for putting the checks there rather than only on the server -- and
the reason the tests construct the input directly rather than calling
``create_sparse_dataset``, which raises ``NoMikroFound`` at ``funcs.py:89`` first, for the
wrong reason.

The second is that ``SparseColorByInput`` is a member of a **discriminated union**
(``LabelColorByInput``, ``Field(discriminator='kind')``) and the first input in this package to
carry a trait while being one. If the discriminator path skipped model validators, the trait
would buy nothing over a guard in ``picker.sparse_color_by``, so
``test_the_colour_rule_survives_the_discriminated_union`` is what makes that argument true
rather than assumed.
"""

import pytest
from pydantic import ValidationError

from mikro_next.api.schema import (
    ColorMap,
    CreateSparseDatasetInput,
    DatasetIdentifiesInput,
    LabelRenderInput,
    SparseAxisInput,
    SparseColorByInput,
    TableIdentifiesInput,
)
from mikro_next.picker import label_render, sparse_color_by

pytest.importorskip("scipy", reason="the store cases need a real CSR matrix")
pytest.importorskip("sporadik", reason="the sparse wire format is an extra: pip install 'mikro-next[sparse]'")

import scipy.sparse as sp


def matrix(rows: int = 20, columns: int = 5):
    """A small CSR matrix -- the accept surface `SporadikLike` is built for."""
    return sp.random(rows, columns, density=0.3, format="csr")


def axis(name: str, *identifications) -> SparseAxisInput:
    """One declared axis."""
    return SparseAxisInput(name=name, identified_by=list(identifications))


def keyed(dataset: str = "1") -> DatasetIdentifiesInput:
    """An identification that authors a FIELD edge."""
    return DatasetIdentifiesInput(dataset=dataset)


def referenced(identifier: str = "2") -> TableIdentifiesInput:
    """An identification that authors none."""
    return TableIdentifiesInput(table=identifier)


def test_the_declaration_every_ingest_script_writes_is_accepted():
    """Objects keyed by a mask, features referenced by a table, two layouts on one store."""
    counts = matrix()
    declared = CreateSparseDatasetInput(
        name="expression",
        store=[counts, counts.tocsc()],
        axes=[axis("object", keyed()), axis("gene", referenced())],
    )
    assert [a.name for a in declared.axes] == ["object", "gene"]
    assert sorted(declared.store.layouts) == [0, 1]


def test_a_declaration_that_disagrees_with_the_matrix_is_refused_before_the_upload():
    """The refusal the server cannot make first, and the one that is otherwise silent.

    It fires at input construction -- before `UploadMiddleware` runs -- which on a matrix
    measured in gigabytes is the whole point.
    """
    with pytest.raises(ValidationError, match="but the matrix has shape"):
        CreateSparseDatasetInput(
            name="expression",
            store=[matrix()],
            axes=[axis("object", keyed()), axis("gene", referenced()), axis("extra", referenced("3"))],
        )


def test_a_matrix_nothing_keys_is_refused():
    """Legal to pydantic, useless in fact: no FIELD edge, so no layer can reach it."""
    with pytest.raises(ValidationError, match="nothing keys this matrix"):
        CreateSparseDatasetInput(
            name="expression",
            store=[matrix()],
            axes=[axis("object", referenced("1")), axis("gene", referenced("2"))],
        )


def test_a_bare_identification_says_to_write_a_list():
    """The error pydantic gives on its own names ``('kind', 'DATASET')`` and nothing useful.

    A `BaseModel` iterates as ``(field, value)`` pairs, so handing one to a `tuple[...]` field
    fails as a ``model_attributes_type`` mismatch on a tuple the caller never wrote. The trait
    catches it first and names the list.
    """
    with pytest.raises(ValidationError, match=r"`identified_by` is a list"):
        SparseAxisInput(name="object", identified_by=keyed())
    with pytest.raises(ValidationError, match=r"`identifiedBy` is a list"):
        SparseAxisInput(name="object", identifiedBy=keyed())


def test_an_axis_identifying_nothing_is_refused_at_the_axis():
    """One line earlier than the mutation, which is where the mistake is made."""
    with pytest.raises(ValidationError, match="is empty"):
        SparseAxisInput(name="object", identified_by=[])


def test_a_store_that_is_not_a_matrix_is_left_to_the_scalar():
    """The trait defers rather than inventing a second opinion about the store.

    `SporadikLike.validate` owns "is this a matrix at all", and says so in its own words --
    as a bare `TypeError`, not a `ValidationError`, because pydantic wraps only `ValueError`
    and `AssertionError`. Asserted as it actually behaves rather than as it reads.
    """
    with pytest.raises(TypeError, match="CSR or CSC"):
        CreateSparseDatasetInput(
            name="expression",
            store="not-a-matrix",
            axes=[axis("object", keyed()), axis("gene", referenced())],
        )


def test_a_qualitative_colormap_is_refused_on_a_sparse_colouring():
    """A slice is a value per object, and nothing stores categories sparsely."""
    with pytest.raises(ValidationError, match="qualitative"):
        SparseColorByInput(
            kind="SPARSE", dataset="1", at=[{"axis": "gene", "value": 4}], colormap=ColorMap.DISTINCT
        )


def test_the_colour_rule_survives_the_discriminated_union():
    """The trait must fire through ``LabelColorByInput``, not only on direct construction.

    ``SparseColorByInput`` is the first input here to carry a trait *and* be a member of a
    discriminated union. If pydantic's tag resolution bypassed the validator, putting the rule
    on the input would buy nothing over a guard in the picker -- so this is the assertion the
    design rests on, not a redundant one.
    """
    with pytest.raises(ValidationError, match="qualitative"):
        LabelRenderInput(
            colorBys=[
                {"kind": "SPARSE", "dataset": "1", "at": [{"axis": "gene", "value": 4}], "colormap": "DISTINCT"}
            ]
        )


def test_an_inverted_window_is_refused_but_a_degenerate_one_is_not():
    """Never stricter than the server: ``min == max`` is legal there, so it is legal here."""
    with pytest.raises(ValidationError, match="inverted"):
        SparseColorByInput(kind="SPARSE", dataset="1", at=[{"axis": "gene", "value": 4}], min=5.0, max=1.0)
    SparseColorByInput(kind="SPARSE", dataset="1", at=[{"axis": "gene", "value": 4}], min=1.0, max=1.0)


class _Reference:
    def __init__(self, axis_name: str):
        self.axis = axis_name


class _SparseDataset:
    """The fields the `SparseDataset` fragment already selects. Nothing here needs a round trip."""

    id = "42"
    name = "expression"
    axis_names = ("object", "gene")
    shape = (1000, 300)
    indexable_axes = ("gene",)
    axis_references = (_Reference("gene"),)


def test_a_colouring_may_only_name_the_axes_the_matrix_identifies():
    """Naming the keyed axis is the mistake, and the weaker "is this a known axis" misses it.

    The remaining axis is the one the layer supplies ids for, so a colouring names every
    *other* axis -- which is also what catches an unknown name and a duplicate entry.
    """
    sparse_color_by(_SparseDataset(), {"gene": 7})
    with pytest.raises(ValueError, match="selected along"):
        sparse_color_by(_SparseDataset(), {"object": 3})
    with pytest.raises(ValueError, match="selected along"):
        sparse_color_by(_SparseDataset(), {"nonexistent": 1})


def test_a_position_outside_the_matrix_is_refused():
    """A position is a row of the table that axis references, not an id of its own."""
    with pytest.raises(ValueError, match=r"runs 0\.\.299"):
        sparse_color_by(_SparseDataset(), {"gene": 5000})


def test_a_colouring_along_an_axis_no_layout_indexes_is_refused():
    """Reading one slice from the wrong layout is a scan of every byte: 1 777 ms against 2.2 ms."""

    class NoLayout(_SparseDataset):
        indexable_axes = ("object",)

    with pytest.raises(ValueError, match="No layout indexes"):
        sparse_color_by(NoLayout(), {"gene": 7})


def test_an_id_or_an_option_defers_instead_of_refusing():
    """Guarded by field, not by type.

    A `ColorByOption` names its dataset with an object carrying only `id` and `name`, and
    round-tripping one back is what `join_path_of` exists to support. Anything that cannot
    answer the questions is passed through and the server asks them instead.
    """

    class Option:
        id = "42"
        name = "expression"

    assert sparse_color_by("42", {"gene": 7}).dataset == "42"
    assert sparse_color_by(Option(), {"gene": 7}).dataset == "42"
    assert sparse_color_by(_SparseDataset(), {"gene": 7}).dataset == "42"


def test_two_slices_naming_the_same_position_are_one_entry():
    """The server sorts ``at`` before keying its duplicate check, so this side must too.

    Without it the pair passes here and is refused on the far side, which is the wrong way
    round -- and it is the same failure the picker's duplicate key had to be widened for once
    already.
    """
    first = sparse_color_by("1", {"gene": 1, "adduct": 0})
    reordered = sparse_color_by("1", {"adduct": 0, "gene": 1})
    with pytest.raises(ValueError, match="renders identically"):
        label_render([first, reordered])

    # Genuinely different slices are still two entries.
    label_render([sparse_color_by("1", {"gene": 1}), sparse_color_by("1", {"gene": 2})])
