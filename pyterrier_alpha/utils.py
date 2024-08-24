"""Module that provides utility functions."""

from typing import Any, Iterable, Iterator, Union

_NO_BUFFER = object()

class PeekableIter:
    """An iterator that allows peeking at the next element."""
    def __init__(self, base: Union[Iterator, Iterable]):
        """Create a PeekableIter from an iterator or iterable."""
        self.base = iter(base)
        self._buffer = _NO_BUFFER

    def __getattr__(self, attr: str):
        return getattr(self.base, attr)

    def __next__(self):
        if self._buffer != _NO_BUFFER:
            n = self._buffer
            self._buffer = _NO_BUFFER
            return n
        return next(self.base)

    def __iter__(self):
        return self

    def peek(self) -> Any:
        """Return the next element without consuming it."""
        if self._buffer == _NO_BUFFER:
            self._buffer = next(self.base)
        return self._buffer


def peekable(it: Union[Iterator, Iterable]) -> PeekableIter:
    """Create a PeekableIter from an iterator or iterable."""
    return PeekableIter(it)
