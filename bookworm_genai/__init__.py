import logging
import os
import importlib.metadata

from rich.logging import RichHandler

LOGGING_LEVEL = os.environ.get("LOGGING_LEVEL", logging.INFO)
LOGGING_FORMAT = os.environ.get("LOGGING_FORMAT", "%(message)s")

__version__ = importlib.metadata.version(__name__)
_is_debug = logging.getLevelName(LOGGING_LEVEL) == logging.DEBUG

logging.basicConfig(
    level=LOGGING_LEVEL,
    format=LOGGING_FORMAT,
    handlers=[RichHandler(markup=True, show_path=_is_debug, show_time=_is_debug, show_level=_is_debug)],
)

logging.getLogger("httpx").setLevel(logging.WARNING)
