# storage/repository.py
"""
Generic JSON repository. Reads and writes objects (or lists/dicts) to JSON.
"""

import json
from pathlib import Path

from exceptions import CorruptedDataError


class JsonRepository:
    """A simple JSON file repository for save/load operations."""

    def __init__(self, file_path):
        self.file_path = Path(file_path)

    def exists(self):
        """True if the file exists on disk."""
        return self.file_path.exists()

    def load(self):
        """Read and return the parsed JSON content. Raises CorruptedDataError on failure."""
        if not self.exists():
            raise CorruptedDataError(f"File not found: {self.file_path}")
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise CorruptedDataError(f"Invalid JSON in {self.file_path}: {e}")

    def save(self, data):
        """Write data (dict or list) to disk as JSON, UTF-8, pretty-printed."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def delete(self):
        """Remove the file if it exists. Idempotent."""
        if self.exists():
            self.file_path.unlink()

    def __repr__(self):
        return f"JsonRepository(path='{self.file_path}', exists={self.exists()})"