"""The sparse-dataset path through the inputs themselves -- traits, and the picker over them.

Where ``test_sparse.py`` calls the check functions, this file goes through
``CreateSparseDatasetInput``, ``SparseAxisInput`` and ``SparseColorByInput``, which is where a
caller meets them: a refusal arrives as pydantic's ``ValidationError`` wrapping ours, so the
assertions are on the wrapped message.

Two things are under test that the function-level file cannot reach.

The first is **ordering**. ``Mikro.execute`` validates the arguments (``_serialize``) and hands them
to the upload middleware next. A trait on the input therefore fires before a byte moves,
which is the whole argument for putting the checks there rather than only on the server -- and
the reason the tests construct the input directly rather than calling
``create_sparse_dataset``, which would fail on a missing client first, for the
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

from mikro.api.schema import (
    ColorMap,
    CreateSparseDatasetInput,
    DatasetIdentifiesInput,
    LabelRenderInput,
    SparseAxisInput,
    SparseColorByInput,
    SparseDatasetSpec,
    TableIdentifiesInput,
)
from mikro.inputs.picker import label_render, sparse_color_by
from mikro.traits import SparseDatasetTrait

pytest.importorskip("scipy", reason="the store cases need a real CSR matrix")
pytest.importorskip("sporadik", reason="the sparse wire format is an extra: pip install 'mikro[sparse]'")

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
            kind="SPARSE", lens="1", colormap=ColorMap.DISTINCT
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
                {"kind": "SPARSE", "lens": "1", "colormap": "DISTINCT"}
            ]
        )


def test_an_inverted_window_is_refused_but_a_degenerate_one_is_not():
    """Never stricter than the server: ``min == max`` is legal there, so it is legal here."""
    with pytest.raises(ValidationError, match="inverted"):
        SparseColorByInput(kind="SPARSE", lens="1", min=5.0, max=1.0)
    SparseColorByInput(kind="SPARSE", lens="1", min=1.0, max=1.0)


class _Window:
    def __init__(self, axis_name: str, low: float | None, high: float | None):
        self.axis, self.min, self.max = axis_name, low, high


class _Named:
    id = "42"
    name = "expression"


class _SparseLens:
    """The fields the `SparseLens` fragment selects. Nothing here needs a round trip."""

    id = "7"
    sparse_dataset = _Named()
    windows = (_Window("gene", 7.0, 7.0),)
    spec = (SparseDatasetSpec.VECTOR, SparseDatasetSpec.SLICE)


def test_a_slice_is_accepted_and_names_its_lens():
    assert sparse_color_by(_SparseLens()).lens == "7"


def test_a_lens_that_is_not_a_slice_is_refused():
    """The server answers "can a picker read this" as one member of the lens' spec.

    Reading that answer, rather than re-deriving it from the windows, is what keeps this from
    ever being stricter than the server: a range, a pin on the keyed axis and a pin no layout
    indexes all come back without SLICE, and the whole lens never has it.
    """

    class Range(_SparseLens):
        windows = (_Window("gene", 0.0, 9.0),)
        spec = (SparseDatasetSpec.MATRIX,)

    class Whole(_SparseLens):
        windows = ()
        spec = (SparseDatasetSpec.MATRIX,)

    with pytest.raises(ValueError, match=r"gene=0\.0\.\.9\.0\) is not a slice"):
        sparse_color_by(Range())
    with pytest.raises(ValueError, match="the whole lens"):
        sparse_color_by(Whole())


def test_an_id_or_a_lens_without_a_spec_defers_instead_of_refusing():
    """Guarded by field, not by type.

    A bare id, or a lens read through a selection that does not carry `spec`, cannot answer
    the question -- so it is passed through and the server asks instead.
    """

    class Bare:
        id = "7"

    assert sparse_color_by("7").lens == "7"
    assert sparse_color_by(Bare()).lens == "7"


def test_two_colourings_through_one_lens_are_one_entry():
    """A SPARSE entry's source is its lens, which is what the server keys its duplicate check on."""
    with pytest.raises(ValueError, match="renders identically"):
        label_render([sparse_color_by("1"), sparse_color_by("1", label="again")])

    # Genuinely different slices are still two entries.
    label_render([sparse_color_by("1"), sparse_color_by("2")])


class _Client:
    """Stands in for the client: records the one mutation `lens()` sends."""

    def __init__(self):
        self.sent = None

    def create_sparse_lens(self, **kwargs):
        self.sent = kwargs
        return _SparseLens()


class _SparseDataset(SparseDatasetTrait):
    """The fields the `SparseDataset` fragment already selects."""

    id = "42"
    name = "expression"
    axis_names = ("object", "gene")
    shape = (1000, 300)


def test_a_pinned_position_is_a_window_whose_min_is_its_max():
    """`createSparseLens(windows:)` has no "position" of its own: a pin is `min == max`."""
    client = _Client()
    _SparseDataset().lens(client, gene=7)
    assert client.sent["sparse_dataset"] == "42"
    (window,) = client.sent["windows"]
    assert (window.axis, window.min, window.max) == ("gene", 7.0, 7.0)


def test_no_windows_is_the_whole_lens():
    client = _Client()
    _SparseDataset().lens(client)
    assert client.sent["windows"] == []


def test_a_range_keeps_an_open_side_open():
    client = _Client()
    _SparseDataset().lens(client, gene=(10, None))
    (window,) = client.sent["windows"]
    assert (window.min, window.max) == (10.0, None)


def test_a_position_outside_the_matrix_is_refused():
    """A position is a row of the table that axis references, not an id of its own."""
    with pytest.raises(ValueError, match=r"outside 0\.\.299"):
        _SparseDataset().lens(_Client(), gene=5000)


def test_an_axis_the_matrix_does_not_have_is_refused():
    with pytest.raises(ValueError, match="Invalid axis 'nonexistent'"):
        _SparseDataset().lens(_Client(), nonexistent=1)
