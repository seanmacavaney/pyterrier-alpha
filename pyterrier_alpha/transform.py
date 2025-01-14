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
    verbose: Optional[bool] = None,
) -> Union[Callable[[T_TRANSFORM_FN], T_TRANSFORM_FN], Callable[[T_TRANSFORM_ITER_FN], T_TRANSFORM_ITER_FN]]:
    """Decorates a function to transform a DataFrame query-by-query. Arguments match those in pt.apply closely.

    Args:
        verbose(bool): Whether to print progress bar. Default is to inspect the passed transformer for
            a verbose member variable that is True.
        add_ranks(bool): Whether to add ranks
        batch_size(int): whether to apply fn on batches of rows or all that are received.

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
    .. versionchanged:: 0.12.4 inspect the passed transformer for a verbose variable
    """
    def _wrapper(fn: Union[T_TRANSFORM_FN]) -> Union[T_TRANSFORM_FN]:
        apply_iter_supports_verbose = Version(pt.__version__) >= Version('0.12.1')
        is_iter = fn.__name__ == 'transform_iter'
        if is_iter:
            assert not add_ranks, "add_ranks not supported for by_query with transform_iter; set add_ranks=False"
            @functools.wraps(fn)
            def _transform_iter(self: pt.Transformer, inp: Iterable[Dict]) -> Iterable[Dict]:
                kwargs = {}
                if verbose:
                    if apply_iter_supports_verbose:
                        kwargs['verbose'] = verbose
                    else:
                        warn(f'verbose ignored for pyterrier version {pt.__version__} (minimum 0.12.1 required)')
                elif (verbose is None and apply_iter_supports_verbose and
                      hasattr(self, 'verbose') and getattr(self, 'verbose')):
                    kwargs['verbose'] = True
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
                nonlocal verbose
                if verbose is None:
                    verbose = hasattr(self, 'verbose') and getattr(self, 'verbose')
                return pt.apply.by_query(
                    functools.partial(fn, self),
                    add_ranks=add_ranks,
                    batch_size=batch_size,
                    iter=False,
                    verbose=verbose,
                )(inp)
            return _transform
    return _wrapper
