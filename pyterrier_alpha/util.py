from typing import Callable
from functools import wraps


def once() -> Callable:
    def _once(fn: Callable) -> Callable:
        """
        Only allows the function to be run once. Subsequent calls will raise an error.
        """
        called = False

        @wraps(fn)
        def _wrapper(*args, **kwargs):
            nonlocal called
            if called:
                raise ValueError(f"{fn.__name__} has already been run")
            # how to handle errors?
            res = fn(*args, **kwargs)
            called = True
            return res
        _wrapper.called = lambda: called  # type: ignore
        return _wrapper
    return _once
