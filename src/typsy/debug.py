from collections.abc import Callable
from functools import partial, wraps
from typing import Literal

from loguru import logger

__all__ = ["invocation"]


class _Invocation[**P, T]:
    type Fn = Callable[P, T]

    def __init__(
        self, func: Fn, i: int = 0, level: Literal["TRACE", "DEBUG"] = "TRACE"
    ) -> None:
        self.__func = func
        self.__i = i
        self.log: Callable[..., None] = partial(logger.log, level)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        prefix = f"{self.__func.__name__}[{self.__i}]"
        self.log(f"{prefix}: {args = }")
        self.log(f"{prefix}: {kwargs = }")

        self.__i += 1

        result = self.__func(*args, **kwargs)
        self.log(f"{prefix}: {result = }")
        return result


def invocation[**P, T](func: Callable[P, T]) -> Callable[P, T]:
    return wraps(func)(_Invocation(func))
