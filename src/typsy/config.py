from collections.abc import Generator
from itertools import chain

import typer
import yaml
from evilpath import Path
from pydantic import BaseModel, TypeAdapter

from .stdout import abort


class Config(BaseModel):
    entries: list[str]
    """Files to compile."""

    def resolve_entries(self, home: Path) -> Generator[tuple[Path, Path]]:
        for file_pattern in self.entries:
            for file in home.glob(file_pattern):
                yield (file, file.with_suffix(".pdf"))


class Project(BaseModel):
    typsy: Config | None = None


_ConfigValidator = TypeAdapter[Config | Project](Config | Project)


def load_config_path(path: Path):
    data: object = yaml.safe_load(path.read_bytes())
    match _ConfigValidator.validate_python(data):
        case Config() as conf:
            return conf
        case Project() as proj:
            return proj.typsy


def get_config(cwd: Path | None) -> tuple[Config, Path]:
    if cwd is None:
        cwd = Path.cwd()
    elif not cwd.exists():
        typer.echo(f"path does not exist: {cwd}")
        raise typer.Abort()
    elif not cwd.is_dir():
        typer.echo(f"path is not a directory: {cwd}")
        raise typer.Abort()

    for folder in chain((cwd,), cwd.parents):
        for filename in (
            "project.yml",
            "project.yaml",
            "typsy.yml",
            "typsy.yaml",
            ".typsy.yml",
            ".typsy.yaml",
        ):
            conf_path = folder / filename
            if not conf_path.exists():
                continue
            conf = load_config_path(conf_path)
            if conf is not None:
                return (conf, conf_path)

    abort("Could not find a suitable config file!")
    raise typer.Abort()
