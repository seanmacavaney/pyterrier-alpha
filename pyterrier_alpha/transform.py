"""Decorators over transform functions."""

import functools
from typing import Callable, Dict, Iterable, Optional, Union
from warnings import warn

import pandas as pd
import pyterrier as pt
from packaging.version import Version

T_TRANSFORM_FN = Callable[[pd.DataFrame], pd.DataFrame]
T_TRANSFORM_ITER_FN = Callable[[Iterable[Dict]], Iterable[Dict]]


def by_query(*,
    add_ranks: bool = True,
    batch_size: Optional[int] = None,
    verbose: bool = False,
) -> Union[Callable[[T_TRANSFORM_FN], T_TRANSFORM_FN], Callable[[T_TRANSFORM_ITER_FN], T_TRANSFORM_ITER_FN]]:
    """Decorates a function to transform a DataFrame query-by-query.

    Example::

        class MyTransformer(pt.Transformer):
            @pta.transform.by_query()
            def transform(self, inp: pd.DataFrame) -> pd.DataFrame:
                # inp only contains a single query at a time.

    It can also decorate ``transform_iter``, which is identifed by the function name

    Example::

        class MyIterTransformer(pt.Transformer):
            @pta.transform.by_query(add_ranks=False)
            def transform_iter(self, inp: Iterable[Dict]) -> Iterable[Dict]:
                # inp only contains a single query at a time.

    .. versionchanged:: 0.12.0 added support for ``transform_iter``
    .. versionchanged:: 0.12.3 supports verbose kwarg
    """
    def _wrapper(fn: Union[T_TRANSFORM_FN]) -> Union[T_TRANSFORM_FN]:
        is_iter = fn.__name__ == 'transform_iter'
        if is_iter:
            assert not add_ranks, "add_ranks not supported for by_query with transform_iter; set add_ranks=False"
            @functools.wraps(fn)
            def _transform_iter(self: pt.Transformer, inp: Iterable[Dict]) -> Iterable[Dict]:
                kwargs = {}
                if Version(pt.__version__) >= Version('0.12.1'):
                    kwargs['verbose'] = verbose
                elif verbose:
                    warn(f'verbose ignored for pyterrier version {pt.__version__} (minimum 0.12.1 required)')
                return pt.apply.by_query(
                    functools.partial(fn, self),
                    batch_size=batch_size,
                    iter=True,
                    **kwargs,
                )(inp)
            return _transform_iter
        else:
            @functools.wraps(fn)
            def _transform(self: pt.Transformer, inp: pd.DataFrame) -> pd.DataFrame:
                return pt.apply.by_query(
                    functools.partial(fn, self),
                    add_ranks=add_ranks,
                    batch_size=batch_size,
                    iter=False,
                    verbose=verbose,
                )(inp)
            return _transform
    return _wrapper
