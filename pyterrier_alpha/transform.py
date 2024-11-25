"""Decorators over transform functions."""

import functools
from typing import Callable, Optional

import pandas as pd
import pyterrier as pt

T_TRANSFORM_FN = Callable[[pd.DataFrame], pd.DataFrame]


def by_query(*,
    add_ranks: bool = True,
    batch_size: Optional[int] = None,
    verbose: bool = False,
) -> Callable[[T_TRANSFORM_FN], T_TRANSFORM_FN]:
    """Decorates a function to transform a DataFrame query-by-query.

    Example::

        class MyTransformer(pt.Transformer):
            @pta.transform.by_query()
            def transform(self, inp: pd.DataFrame) -> pd.DataFrame:
                # inp only contains a single query at a time.
    """
    def _wrapper(fn: T_TRANSFORM_FN) -> T_TRANSFORM_FN:
        @functools.wraps(fn)
        def _transform(self: pt.Transformer, inp: pd.DataFrame) -> pd.DataFrame:
            return pt.apply.by_query(
                functools.partial(fn, self),
                add_ranks=add_ranks,
                batch_size=batch_size,
                verbose=verbose,
            )(inp)
        return _transform
    return _wrapper
