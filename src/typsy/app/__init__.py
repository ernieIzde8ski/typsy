from typing import Annotated

import typer
from evilpath import Path
from loguru import logger
from typer import Typer
from watchfiles import watch as fswatch

from ..config import get_config
from ..stdout import abort
from .build import ExitCode, build_multiple, up_to_date
from .verbosity import Verbosity

__all__ = ["app"]

app = Typer()


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
    verbosity.configure_logger()

    if poll is not None:
        watch = True

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
