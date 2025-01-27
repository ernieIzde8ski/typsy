import subprocess
import sys
from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Annotated, LiteralString

import typer
from loguru import logger
from typer import Typer
from watchfiles import watch as fswatch

from .config import get_config

__all__ = ["app"]

app = Typer()


def up_to_date(target: Path, *deps: Path):
    if not target.exists():
        return False

    t_mtime = target.stat().st_mtime_ns
    for dep in deps:
        d_mtime = dep.stat().st_mtime_ns
        if d_mtime > t_mtime:
            return False

    return True


def build_multiple(files: Sequence[tuple[Path, Path]], *, root: Path | None = None):
    logger.info(f"Building {len(files)} files...")
    for source, target in files:
        logger.info(f"Building file: {target}")
        command = ["typst", "compile"]
        if root is not None:
            command += ["--root", root]
        command += [source, target]
        _ = subprocess.run(command)


class Verbosity(str, Enum):
    quiet = "quiet"
    normal = "normal"
    debug = "debug"

    def int_value(self) -> LiteralString:
        match self:
            case Verbosity.quiet:
                return "ERROR"
            case Verbosity.normal:
                return "INFO"
            case Verbosity.debug:
                return "DEBUG"


@app.command()
def build(
    path: Annotated[Path | None, typer.Argument()] = None,
    watch: Annotated[bool, typer.Option("-w", "--watch")] = False,
    verbosity: Annotated[Verbosity, typer.Option("-v", "--verbosity")] = Verbosity.normal,
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
        logger.debug(f":: {entry}")

    out_of_date = tuple(
        (source, target)
        for (source, target) in entries.items()
        if not up_to_date(target, source)
    )

    if out_of_date:
        build_multiple(out_of_date, root=typst_root)
    else:
        logger.info("All files up to date!")
        logger.info(f"Watching for changes in {len(entries)} files.")

    if not watch:
        return

    for file_changes in fswatch(*entries):
        typer.clear()
        out_of_date = tuple(
            (Path(source), entries[Path(source)]) for (_, source) in file_changes
        )
        build_multiple(out_of_date)
