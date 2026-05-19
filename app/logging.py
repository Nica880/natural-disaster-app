"""Module-level logger setup. Call configure_logging() once at app startup."""
from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        return  # already configured (e.g. by uvicorn)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-7s %(name)s :: %(message)s", datefmt="%H:%M:%S")
    )
    root.addHandler(handler)
    root.setLevel(level.upper())
