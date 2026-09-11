"""Declaring a sparse dataset, and what the declaration is checked against.

The sparse counterpart of ``test_tables.py``, and it tests the same two things: the refusals,
and the shape of the API a caller writes. There is no helper and no wrapper type -- a caller
writes ``SparseAxisInput``s and hands them to ``create_sparse_dataset`` -- so the checks are
exercised through :mod:`mikro_next.sparse` here, and through the input itself in
``test_sparse_dataset.py``.

The reason this file exists at all is that the sparse path had no tests. ``SporadikLike`` was
the only client-side gate and it was untested by construction, because ``sporadik`` was not
installed in this package's own environment. Every case below runs without it: the checks in
:func:`~mikro_next.sparse.check_axes` are statements about axes, and
:func:`~mikro_next.sparse.check_against_store` reads exactly one attribute off a layout, so a
stub with a ``shape`` is a whole store as far as it is concerned. That split is deliberate --
it is what keeps the refusals reachable from a plain ``pytest`` run.

One rule under test is easy to state wrongly, and is the one place a client-side check could
end up stricter than the server: "nothing keys this matrix" is not "every axis has a table on
it". Fan-in is legal -- an axis may carry both a mask and the table its positions enumerate --
so ``test_an_axis_may_be_keyed_and_referenced_at_once`` is what pins the predicate.
"""

import pytest

from mikro_next.api.schema import (
    DatasetIdentifiesInput,
    SparseAxisInput,
    TableIdentifiesInput,
)
from mikro_next.sparse import MIN_RANK, SparseDeclarationError, check_against_store, check_axes


class Layout:
    """The one attribute :func:`check_against_store` reads off a layout.

    A stub rather than a real ``sporadik.Layout`` on purpose: the function takes a plain
    mapping precisely so the shape check can be tested with no wire format installed.
    """

    def __init__(self, shape):
        self.shape = shape


def mask(dataset: str = "1") -> DatasetIdentifiesInput:
    """An identification by a source whose own contents are the ids. Authors a FIELD edge."""
    return DatasetIdentifiesInput(dataset=dataset)


def table(identifier: str = "2") -> TableIdentifiesInput:
    """An identification by the table whose rows the positions are. Authors no edge."""
    return TableIdentifiesInput(table=identifier)


def axis(name: str, *identifications) -> SparseAxisInput:
    """One declared axis. Constructed through the input, so its own trait runs too."""
    return SparseAxisInput(name=name, identified_by=list(identifications))


def two_axes():
    """The ordinary rank-two declaration: objects keyed by a mask, features by a table."""
    return [axis("object", mask()), axis("gene", table())]


def test_the_ordinary_declaration_is_accepted():
    """The rank-two case every ingest script writes. If this refuses, nothing else matters."""
    check_axes(two_axes())
    check_against_store(two_axes(), {0: Layout((1000, 300))})


def test_a_rank_three_declaration_is_accepted():
    """Rank is not two by definition, only at minimum.

    A (cell, metabolite, adduct) tensor is an ordinary sparse dataset, and the rank-three case
    is where ``indexed_axis`` stops being derivable from the encoding -- so a check written
    against "csr means axis 0" would pass rank two and be wrong here.
    """
    axes = [axis("cell", mask()), axis("metabolite", table("2")), axis("adduct", table("3"))]
    check_axes(axes)
    check_against_store(axes, {0: Layout((5000, 400, 3))})


def test_an_axis_may_be_keyed_and_referenced_at_once():
    """Fan-in is legal, and this is what stops the "nothing keys it" rule being too strict.

    One axis may carry both a mask and the table its positions enumerate. Every axis then has
    a table on it, while something still keys the matrix -- so a check that refused on "every
    axis has a table" would refuse a declaration the server accepts, which is the one thing a
    client-side check must never do.
    """
    check_axes([axis("object", mask(), table("9")), axis("gene", table("2"))])


def test_two_masks_may_key_one_axis():
    """The reason ``identifiedBy`` is a list at all: a nucleus mask and a cell mask.

    Fan-in is refused only for tables, because each edge stands on its own.
    """
    check_axes([axis("object", mask("1"), mask("2")), axis("gene", table())])


def test_one_axis_is_not_a_sparse_matrix():
    """A single compressed axis needs at least one other to hold the positions."""
    with pytest.raises(SparseDeclarationError, match=f"at least {MIN_RANK} axes"):
        check_axes([axis("object", mask())])


def test_no_axes_at_all_is_refused_as_a_rank():
    """The empty case reaches the rank rule rather than being waved through as "nothing to check"."""
    with pytest.raises(SparseDeclarationError, match=f"at least {MIN_RANK} axes"):
        check_axes([])


def test_an_axis_declared_twice_is_refused():
    """An axis name is how a colouring names a position along it, so it has to pick one axis."""
    with pytest.raises(SparseDeclarationError, match="declared more than once"):
        check_axes([axis("gene", mask()), axis("gene", table())])


def test_an_axis_identifying_nothing_is_refused():
    """An axis nothing identifies is one no source could ever key.

    Refused by :func:`check_axes` as well as by the axis input's own trait, because a model
    built some other way still reaches the create input.
    """
    axes = [axis("object", mask()), SparseAxisInput.model_construct(name="gene", identified_by=())]
    with pytest.raises(SparseDeclarationError, match="empty `identifiedBy`"):
        check_axes(axes)


def test_a_matrix_nothing_keys_is_refused():
    """Every axis referenced by a table means no FIELD edge, so no layer can ever reach it."""
    with pytest.raises(SparseDeclarationError, match="nothing keys this matrix"):
        check_axes([axis("object", table("1")), axis("gene", table("2"))])


def test_two_tables_on_one_axis_are_refused():
    """An axis enumerates one thing; two tables are two answers to what a position is."""
    with pytest.raises(SparseDeclarationError, match="more than one table"):
        check_axes([axis("object", mask()), axis("gene", table("2"), table("3"))])


def test_more_axes_than_the_matrix_has_is_refused():
    """The refusal the server cannot make first, because it has no shape until the upload lands.

    Silent if it is not made: the axes are read in the order the shape is written, so a count
    that disagrees places every lookup one position out and raises nothing.
    """
    axes = [axis("object", mask()), axis("gene", table("2")), axis("extra", table("3"))]
    with pytest.raises(SparseDeclarationError, match=r"3 axes .* but the matrix has shape"):
        check_against_store(axes, {0: Layout((1000, 300))})


def test_fewer_axes_than_the_matrix_has_is_refused():
    """The same rule from the other side -- a rank-three matrix declared as if it were flat."""
    with pytest.raises(SparseDeclarationError, match="but the matrix has shape"):
        check_against_store(two_axes(), {0: Layout((5000, 400, 3))})


def test_the_shape_is_read_off_any_layout():
    """``layouts_of`` has already refused layouts that disagree, so any of them answers.

    Checked because reading only the first would be right by accident on a one-layout store
    and wrong on the two-layout stores every colouring path actually uses.
    """
    check_against_store(two_axes(), {0: Layout((1000, 300)), 1: Layout((1000, 300))})


def test_a_store_with_no_layouts_is_left_to_the_server():
    """Nothing is known, so nothing is claimed. The server checks what arrived."""
    check_against_store(two_axes(), {})
