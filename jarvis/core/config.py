import json
import logging
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    def __init__(self):
        self.config_path = Path(__file__).parent.parent / "config" / "settings.json"
        self._config = self._load_config()
        self._setup_logging()

    def _load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file {self.config_path}")

    def _setup_logging(self):
        logs_dir = Path(__file__).parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)

        log_file = logs_dir / f"jarvis_{self.jarvis_version}.log"

        # Use UTF-8 for the file handler so Unicode characters (arrows, etc.)
        # never cause UnicodeEncodeError on Windows cp1252 consoles.
        # The stream handler uses errors="replace" so the console never crashes.
        import sys

        file_handler   = logging.FileHandler(log_file, encoding="utf-8")
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.stream = open(
            sys.stdout.fileno(),
            mode="w",
            encoding="utf-8",
            errors="replace",
            closefd=False,
            buffering=1,
        )

        fmt = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(fmt)
        stream_handler.setFormatter(fmt)

        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, stream_handler],
            force=True,   # override any previously installed handlers
        )

    @property
    def mongodb_uri(self) -> str:
        return self._config.get("mongodb_uri", "mongodb://localhost:27017/")

    @property
    def database_name(self) -> str:
        return self._config.get("database_name", "jarvis")

    @property
    def jarvis_version(self) -> str:
        return self._config.get("jarvis_version", "0.1")


config = Config()
