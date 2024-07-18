import warnings
from functools import wraps
from importlib.util import find_spec
from typing import Callable

import pyterrier as pt
from pyterrier_alpha import util, io


def autoclass(*args, **kwargs):
    raise RuntimeError('pta.java.autoclass not available until pta.java.init() is called.')


def _legacy_init(jnius_config):
    if not pt.started():
        pt.init()


@util.once()
def init() -> None:
    global autoclass

    if find_spec('jnius_config') is None:
        warnings.warn('pyterrier-alpha[java] not installed; no need to run pta.java.init()')
        return

    import jnius_config
    for entry_point in io.entry_points('pyterrier.java.init'):
        _init = entry_point.load()
        _init(jnius_config)

    import jnius

    autoclass = jnius.autoclass


def started() -> bool:
    return init.called()


def required() -> Callable:
    def _required(fn: Callable) -> Callable:
        @wraps(fn)
        def _wrapper(*args, **kwargs):
            if not started():
                init()
            return fn(*args, **kwargs)
        return _wrapper
    return _required
