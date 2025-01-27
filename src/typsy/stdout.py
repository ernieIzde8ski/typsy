from collections.abc import Callable
from functools import partial
from typing import IO, Any

import typer
from typer import echo, style

__all__ = ["print", "eprint", "println", "eprintln", "abort"]


def print(
    *values: object,
    sep: str = " ",
    end: str = "",
    to_str: Callable[[object], str] = str,
    fg: str | None = None,
    stderr: "IO[Any] | bool" = False,  # pyright: ignore[reportExplicitAny]
) -> None:
    res = sep.join(to_str(values) for values in values) + end
    if fg is not None:
        res = style(res, fg=fg)
    if isinstance(stderr, bool):
        return echo(res, nl=False, err=stderr)
    else:
        return echo(res, nl=False, file=stderr)


println = partial(print, end="\n")
eprint = partial(print, stderr=True)
eprintln = partial(print, stderr=True, end="\n")


def abort(*values: object, code: int = 1):
    eprint(*values, end=" Aborted.")
    raise typer.Exit(code=code)
