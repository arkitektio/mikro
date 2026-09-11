"""Default Widgets

This Module provides default widgets that can be used with the mikro app in an arkitekt
context.

Attributes:
    MY_TOP_REPRESENTATIONS (SearchWidget): The top representations for the currently active user
    MY_TOP_SAMPLES (SearchWidget): The top samples for the currently active user
"""

from rekuest_next.widgets import DescriptorInput, withDescriptor


def withMaxXSize(max_x_size: int) -> DescriptorInput:
    """A decorator to add a max size descriptor to a class.

    Args:
        max_x_size (int): The maximum x size

    Returns:
        Callable[[Type], Type]: The decorated class
    """

    return withDescriptor("@mikro/max_x_size", max_x_size)


def withMaxYSize(max_x_size: int) -> DescriptorInput:
    """A decorator to add a max size descriptor to a class.

    Args:
        max_x_size (int): The maximum x size

    Returns:
        Callable[[Type], Type]: The decorated class
    """

    return withDescriptor("@mikro/max_x_size", max_x_size)


def withMaxZSize(max_x_size: int) -> DescriptorInput:
    """A decorator to add a max size descriptor to a class.

    Args:
        max_x_size (int): The maximum x size

    Returns:
        Callable[[Type], Type]: The decorated class
    """

    return withDescriptor("@mikro/max_z_size", max_x_size)


def withMaxTSize(max_x_size: int) -> DescriptorInput:
    """A decorator to add a max size descriptor to a class.

    Args:
        max_x_size (int): The maximum x size

    Returns:
        Callable[[Type], Type]: The decorated class
    """

    return withDescriptor("@mikro/max_t_size", max_x_size)


def withMaxCSize(max_x_size: int) -> DescriptorInput:
    """A decorator to add a max size descriptor to a class.

    Args:
        max_x_size (int): The maximum x size

    Returns:
        Callable[[Type], Type]: The decorated class
    """

    return withDescriptor("@mikro/max_c_size", max_x_size)
