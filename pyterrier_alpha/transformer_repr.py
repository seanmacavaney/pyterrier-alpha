"""Module providing a function that calculates a string representation function for transformers."""

import inspect
from typing import Any


def transformer_repr(self: Any) -> str:
    """Return a string representation of a transformer instance.

    .. versionadded:: 0.3.0

    .. versionchanged:: 0.4.2
        Prioritize fields with ``_name`` above ``name``
    """
    cls = self.__class__
    init = self.__init__
    signature = inspect.signature(init)
    mode = 'pos'
    args = []
    for p in signature.parameters.values():
        if p.kind not in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
            mode = 'kwd'
        try:
            val = getattr(self, f'_{p.name}')
        except AttributeError:
            val = getattr(self, p.name)
        if val != p.default:
            args.append(f'{p.name}={val!r}' if mode == 'kwd' else repr(val))
        else:
            mode = 'kwd' # skip a paramter, force keyword mode
    return cls.__name__ + '(' + ', '.join(args) + ')'
