"""Test cases for the FourByFourMatrix scalar."""

import numpy as np
import pytest

from mikro_next.scalars import FourByFourMatrix


def test_four_by_four_matrix() -> None:
    """Test the FourByFourMatrix scalar for valid and invalid inputs."""
    # Test valid 4x4 matrix
    valid_matrix = np.array([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]])
    assert isinstance(FourByFourMatrix.validate(valid_matrix), list)

    # Test invalid matrix (not 4x4)
    invalid_matrix = np.array([[1, 2], [3, 4]])
    with pytest.raises(ValueError):
        FourByFourMatrix.validate(invalid_matrix)


def test_four_by_four_matrix_edge_cases() -> None:
    """Test FourByFourMatrix with edge cases."""
    # Test with zeros
    zero_matrix = np.zeros((4, 4))
    assert isinstance(FourByFourMatrix.validate(zero_matrix), list)

    # Test with ones
    ones_matrix = np.ones((4, 4))
    assert isinstance(FourByFourMatrix.validate(ones_matrix), list)

    # Test with negative values
    negative_matrix = np.array(
        [[-1, -2, -3, -4], [-5, -6, -7, -8], [-9, -10, -11, -12], [-13, -14, -15, -16]]
    )
    assert isinstance(FourByFourMatrix.validate(negative_matrix), list)

    # Test with float values
    float_matrix = np.array(
        [
            [1.5, 2.5, 3.5, 4.5],
            [5.5, 6.5, 7.5, 8.5],
            [9.5, 10.5, 11.5, 12.5],
            [13.5, 14.5, 15.5, 16.5],
        ]
    )
    assert isinstance(FourByFourMatrix.validate(float_matrix), list)


def test_four_by_four_matrix_invalid_shapes() -> None:
    """Test FourByFourMatrix with various invalid shapes."""
    # Test 3x3 matrix
    with pytest.raises(ValueError):
        FourByFourMatrix.validate(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]))

    # Test 5x5 matrix
    with pytest.raises(ValueError):
        FourByFourMatrix.validate(np.ones((5, 5)))

    # Test 1D array
    with pytest.raises(ValueError):
        FourByFourMatrix.validate(np.array([1, 2, 3, 4]))

    # Test 3D array
    with pytest.raises(ValueError):
        FourByFourMatrix.validate(np.ones((4, 4, 4)))

