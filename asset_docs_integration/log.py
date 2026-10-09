"""Logging configuration."""

import importlib.resources
import logging
import logging.config

logger = logging.getLogger("asset-docs-integration")


def setup_logging():
    """Initializes the project logging."""
    ref = importlib.resources.files("asset_docs_integration") / "logging.conf"
    with importlib.resources.as_file(ref) as path:
        logging.config.fileConfig(path)
