import subprocess
from collections.abc import Sequence
from typing import NewType

from evilpath import Path
from loguru import logger


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
        # TODO: better formatting for command debugging
        logger.debug(f"Executing command: {command}")
        proc = subprocess.run(command)
        exit_code = ExitCode(proc.returncode) or exit_code
    return exit_code
