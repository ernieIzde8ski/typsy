import subprocess
import sys
from collections.abc import Sequence
from enum import Enum
from typing import Annotated, LiteralString, NewType

import typer
from evilpath import Path
from loguru import logger
from typer import Typer
from watchfiles import watch as fswatch

from typsy.stdout import abort

from .config import get_config

__all__ = ["app"]

app = Typer()


def up_to_date(target: Path, *deps: Path):
    if not target.exists():
        logger.trace(f"target does not exist: {target}")
        return False

    t_mtime = target.mtime(form="datetime")
    logger.trace(f"\t({t_mtime}, {target})")
    for dep in deps:
        d_mtime = dep.mtime(form="datetime")
        logger.trace(f"\t({d_mtime}, {dep})")
        if d_mtime > t_mtime:
            return False

    return True


ExitCode = NewType("ExitCode", int)
NormalExit = ExitCode(0)


def build_multiple(files: Sequence[tuple[Path, Path]], *, root: Path | None) -> ExitCode:
    logger.info(f"Building {len(files)} files...")
    exit_code = NormalExit
    for source, target in files:
        logger.info(f"Building file: {target}")
        command = ["typst", "compile"]
        if root is not None:
            command += ["--root", root]
        command += [source, target]
        logger.debug(f"Executing command: {command}")
        proc = subprocess.run(command)
        exit_code = ExitCode(proc.returncode) or exit_code
    return exit_code


class Verbosity(str, Enum):
    quiet = "quiet"
    normal = "normal"
    debug = "debug"
    trace = "trace"

    def int_value(self) -> LiteralString:
        match self:
            case Verbosity.quiet:
                return "ERROR"
            case Verbosity.normal:
                return "INFO"
            case Verbosity.debug:
                return "DEBUG"
            case Verbosity.trace:
                return "TRACE"


@app.command()
def build(
    path: Annotated[Path | None, typer.Argument(parser=Path)] = None,
    watch: Annotated[bool, typer.Option("-w", "--watch")] = False,
    verbosity: Annotated[Verbosity, typer.Option("-v", "--verbosity")] = Verbosity.normal,
    poll: Annotated[
        bool | None,
        typer.Option(
            "-p",
            "--force-poll/--no-poll",
            help="""Forcefully enable polling. Implies `-w`.

            This is not recommended, but may be necessary if you experience issues with the typical API.""",
            show_default=False,
        ),
    ] = None,
):
    """Build a Typst project."""
    logger.remove()
    _ = logger.add(sys.stderr, level=verbosity.int_value())

    # TODO: implement watching on changes to config file
    (config, config_path) = get_config(path)
    typst_root = config_path.parent
    entries = dict(config.resolve_entries(typst_root))

    if watch:
        typer.clear()

    logger.debug("Collected entries:")
    for entry in entries.keys():
        logger.debug(f" - {entry}")

    out_of_date = tuple(
        (source, target)
        for (source, target) in entries.items()
        if not up_to_date(target, source)
    )

    if out_of_date:
        exit_code = build_multiple(out_of_date, root=typst_root)
    else:
        logger.info("All files up to date!")
        exit_code = ExitCode(0)

    if not watch and poll is None:
        raise typer.Exit(exit_code)

    logger.info(f"Watching for changes in {len(entries)} files.")

    if poll is not None:
        logger.debug(f"Forced polling is currently {'enabled' if poll else 'disabled'}.")

    for entry in entries:
        logger.trace(f"  - {entry}")

    for file_changes in fswatch(*entries, force_polling=poll):
        typer.clear()
        out_of_date = tuple(
            (Path(source), entries[Path(source)]) for (_, source) in file_changes
        )
        _ = build_multiple(out_of_date, root=typst_root)

    abort("`fswatch` unexpectedly stopped.")
