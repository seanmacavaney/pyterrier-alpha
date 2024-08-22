from typing import Iterator, Iterable, Union


_NO_BUFFER = object()

class PeekableIter:
    def __init__(self, base: Union[Iterator, Iterable]):
        self.base = iter(base)
        self._buffer = _NO_BUFFER

    def __getattr__(self, attr):
        return getattr(self.base, attr)

    def __next__(self):
        if self._buffer != _NO_BUFFER:
            n = self._buffer
            self._buffer = _NO_BUFFER
            return n
        return next(self.base)

    def __iter__(self):
        return self

    def peek(self):
        if self._buffer == _NO_BUFFER:
            self._buffer = next(self.base)
        return self._buffer


def peekable(it: Union[Iterator, Iterable]) -> PeekableIter:
    return PeekableIter(it)
