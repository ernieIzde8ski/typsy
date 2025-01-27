"""A Typst project manager."""

from .info import (
    __author__,
    __copyright__,
    __credits__,
    __license__,
    __maintainer__,
    __version__,
)

__all__ = [
    "__author__",
    "__copyright__",
    "__credits__",
    "__license__",
    "__version__",
    "__maintainer__",
    "add",
]


def add(left: int, right: int) -> int:
    """Returns the sum of two numbers."""
    return left + right
