import sys
from enum import Enum
from typing import Annotated, LiteralString

from loguru import logger
from typer import Option


class Verbosity(str, Enum):
    quiet = "quiet"
    normal = "normal"
    debug = "debug"
    trace = "trace"

    def as_level(self) -> LiteralString:
        match self:
            case Verbosity.quiet:
                return "ERROR"
            case Verbosity.normal:
                return "INFO"
            case Verbosity.debug:
                return "DEBUG"
            case Verbosity.trace:
                return "TRACE"

    def configure_logger(self):
        logger.remove()
        _ = logger.add(sys.stderr, level=self.as_level())


type VerbosityOption = Annotated[
    Verbosity, Option(Verbosity.normal, "-V", "--verbosity", help="Set output verbosity.")
]
