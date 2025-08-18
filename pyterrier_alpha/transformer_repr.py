"""Module providing a function that calculates a string representation function for transformers."""

import inspect
from typing import Any

import pyterrier as pt


def transformer_repr(transformer: Any) -> str:
    """Return a string representation of a transformer instance.

    .. versionadded:: 0.3.0

    .. versionchanged:: 0.4.2
        Prioritize fields with ``_name`` above ``name``

    .. versionchanged:: 0.12.1
        Ignore verbose

    .. versionchanged:: TODO
        Use :meth:`pt.inspect.transformer_attributes`
    """
    cls = transformer.__class__
    mode = 'pos'
    args = []
    for attr in pt.inspect.transformer_attributes(transformer):
        if attr.init_parameter_kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            mode = 'kwd'
        if attr.value != attr.init_default_value and attr.name != 'verbose':
            args.append(f'{attr.name}={attr.value!r}' if mode == 'kwd' else repr(attr.value))
        else:
            mode = 'kwd' # skip a parameter, force keyword mode
    return cls.__name__ + '(' + ', '.join(args) + ')'
