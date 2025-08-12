"""Validation utilities for checking the input to transformers.

Part of pyterrier core since: TODO
"""
from pyterrier.validate import (
    InputValidationError,
    InputValidationWarning,
    any,
    any_iter,
    columns,
    columns_iter,
    document_frame,
    query_frame,
    result_frame,
)

__all__ = [
    'InputValidationError',
    'InputValidationWarning',
    'columns',
    'query_frame',
    'result_frame',
    'document_frame',
    'columns_iter',
    'any',
    'any_iter'
]
