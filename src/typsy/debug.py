from collections.abc import Callable
from functools import wraps

from loguru import logger


class _Invocation[**P, T]:
    type Fn = Callable[P, T]

    def __init__(self, func: Fn, i: int = 0) -> None:
        self.__func = func
        self.__i = i

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        prefix = f"{self.__func.__name__}[{self.__i}]"
        logger.debug(f"{prefix}: {args = }")
        logger.debug(f"{prefix}: {kwargs = }")

        self.__i += 1

        result = self.__func(*args, **kwargs)
        logger.debug(f"{prefix}: {result = }")
        return result


def invocation[**P, T](func: Callable[P, T]) -> Callable[P, T]:
    return wraps(func)(_Invocation(func))
