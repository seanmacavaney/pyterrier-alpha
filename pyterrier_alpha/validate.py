"""Validation utilities for checking the input to transformers."""

from types import TracebackType
from typing import List, Optional, Type

import pandas as pd

from pyterrier_alpha.utils import PeekableIter


class _TransformerMode:
    def __init__(self, missing_columns: List[str], extra_columns: List[str], mode_name: Optional[str] = None):
        self.missing_columns = missing_columns
        self.extra_columns = extra_columns
        self.mode_name = mode_name

    def __str__(self):
        return f'{self.mode_name} (missing: {self.missing_columns}, extra: {self.extra_columns})'

    def __repr__(self):
        return f'TransformerMode(missing_columns={self.missing_columns!r}, ' \
               f'extra_columns={self.extra_columns!r}, ' \
               f'mode_name={self.mode_name!r})'


class InputValidationError(KeyError):
    """Exception raised when input validation fails."""
    def __init__(self, message: str, modes: List[_TransformerMode]):
        """Create an InputValidationError."""
        assert len(modes) > 0
        super().__init__(message)
        self.modes = modes

    def __str__(self):
        return self.args[0] + ' ' + str(self.modes)

    def __repr__(self):
        return f'InputValidationError({self.args[0]!r}, {self.modes!r})'


def columns(inp: pd.DataFrame,
            *,
            includes: Optional[List[str]] = None,
            excludes: Optional[List[str]] = None) -> None:
    """Check that the input frame has the expected columns.

    Raises:
        InputValidationError: If is missing any of the `includes` columns, or has any of the `excludes` columns.
    """
    with any(inp) as v:
        v.columns(includes=includes, excludes=excludes)


def query_frame(inp: pd.DataFrame, extra_columns: Optional[List[str]] = None) -> None:
    """Check that the input frame is a valid query frame.

    Raises:
        InputValidationError: If the input frame is not a valid query frame.
    """
    with any(inp) as v:
        v.query_frame(extra_columns)



def result_frame(inp: pd.DataFrame, extra_columns: Optional[List[str]] = None) -> None:
    """Check that the input frame is a valid result frame.

    Raises:
        InputValidationError: If the input frame is not a valid result frame.
    """
    with any(inp) as v:
        v.result_frame(extra_columns)


def document_frame(inp: pd.DataFrame, extra_columns: Optional[List[str]] = None) -> None:
    """Check that the input frame is a valid document frame.

    Raises:
        InputValidationError: If the input frame is not a valid document frame.
    """
    with any(inp) as v:
        v.document_frame(extra_columns)


def columns_iter(inp: pd.DataFrame,
            *,
            includes: Optional[List[str]] = None,
            excludes: Optional[List[str]] = None) -> None:
    """Check that the input frame has the expected columns.

    Raises:
        InputValidationError: If is missing any of the `includes` columns, or has any of the `excludes` columns.
    """
    with any_iter(inp) as v:
        v.columns(includes=includes, excludes=excludes)


def any(inp: pd.DataFrame) -> '_ValidationContextManager':
    """Create a validation context manager for a DataFrame."""
    return _ValidationContextManager(inp)


def any_iter(inp: PeekableIter) -> '_IterValidationContextManager':
    """Create a validation context manager for an iterator."""
    if not isinstance(inp, PeekableIter):
        raise AttributeError('inp is not peekable. Run the following before calling this function.\n'
                             'inp = pta.utils.peekable(inp) # !! IMPORTANT: you must re-assign the input to peekable '
                             '(not just pass it in), otherwise you will skip the first record !!')
    return _IterValidationContextManager(inp)


class _ValidationContextManager:
    """Context manager for validating the input to transformers."""
    def __init__(self, inp: pd.DataFrame):
        """Create a ValidationContextManager for the given DataFrame."""
        self.inp = inp
        self.mode = None
        self.attempts = 0
        self.errors = []

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> Optional[bool]:

        if exc_type is not None:
            return False # the captured exception takes priority

        if self.attempts > 0 and self.attempts == len(self.errors):
            raise InputValidationError("DataFrame does not match required columns for this transformer.", self.errors)

    def columns(self,
                *,
                includes: Optional[List[str]] = None,
                excludes: Optional[List[str]] = None,
                mode: str = None) -> bool:
        """Check that the input frame has the ``includes`` columns and doesn't have the ``excludes`` columns."""
        includes = includes if includes is not None else []
        excludes = excludes if excludes is not None else []
        missing_columns = set(includes) - set(self.inp.columns)
        extra_columns = set(excludes) & set(self.inp.columns)
        self.attempts += 1

        if missing_columns or extra_columns:
            self.errors.append(_TransformerMode(
                missing_columns=[c for c in includes if c in missing_columns],
                extra_columns=[c for c in excludes if c in extra_columns],
                mode_name=mode,
            ))
            return False

        if self.mode is None and mode is not None:
            self.mode = mode

        return True

    def query_frame(self, extra_columns: Optional[List[str]] = None, mode: str = None) -> bool:
        """Check that the input frame is a valid query frame, with optional extra columns."""
        extra_columns = list(extra_columns) if extra_columns is not None else []
        return self.columns(includes=['qid'] + extra_columns, excludes=['docno'], mode=mode)

    def result_frame(self, extra_columns: Optional[List[str]] = None, mode: str = None) -> bool:
        """Check that the input frame is a valid result frame, with optional extra columns."""
        extra_columns = list(extra_columns) if extra_columns is not None else []
        return self.columns(includes=['qid', 'docno'] + extra_columns, mode=mode)

    def document_frame(self, extra_columns: Optional[List[str]] = None, mode: str = None) -> bool:
        """Check that the input frame is a valid document frame, with optional extra columns."""
        extra_columns = list(extra_columns) if extra_columns is not None else []
        return self.columns(includes=['docno'] + extra_columns, excludes=['qid'], mode=mode)


_EMPTY_ITER = object()

class _IterValidationContextManager:
    def __init__(self, inp: PeekableIter):
        try:
            self.sample_cols = set(inp.peek().keys())
        except StopIteration:
            self.sample_cols = _EMPTY_ITER
        self.mode = None
        self.attempts = 0
        self.errors = []

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType]
    ) -> Optional[bool]:

        if exc_type is not None:
            return False # the captured exception takes priority

        if self.attempts > 0 and self.attempts == len(self.errors):
            raise InputValidationError("Input does not match required columns for this transformer.", self.errors)

    def columns(self,
                *,
                includes: Optional[List[str]] = None,
                excludes: Optional[List[str]] = None,
                mode: str = None) -> bool:
        self.attempts += 1
        includes = includes if includes is not None else []
        excludes = excludes if excludes is not None else []
        if self.sample_cols == _EMPTY_ITER:
            self.errors.append(_TransformerMode(
                missing_columns=list(includes),
                extra_columns=[],
                mode_name=mode,
            ))
            return False
        missing_columns = set(includes) - self.sample_cols
        extra_columns = set(excludes) & self.sample_cols

        if missing_columns or extra_columns:
            self.errors.append(_TransformerMode(
                missing_columns=[c for c in includes if c in missing_columns],
                extra_columns=[c for c in excludes if c in extra_columns],
                mode_name=mode,
            ))
            return False

        if self.mode is None and mode is not None:
            self.mode = mode

        return True

    def empty(self, *, mode: str = 'empty'):
        self.attempts += 1
        if self.sample_cols != _EMPTY_ITER:
            self.errors.append(_TransformerMode(
                missing_columns=[],
                extra_columns=[],
                mode_name=mode,
            ))
            return False

        if self.mode is None and mode is not None:
            self.mode = mode
        return True
