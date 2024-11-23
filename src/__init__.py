from .settings import get_settings
import logging.config
import os

logging.config.fileConfig(
    os.path.join(os.path.dirname(__file__), "..", "logging_config.ini")
)
