from typing import List
import os
from src.utils.helpers import PathHelper
from .interfaces import IFileRepository

class FileRepository(IFileRepository):
    def ensure_dir(self, path: str) -> None:
        PathHelper.ensure_dir_exists(path)

    def list_files(self, path: str, extensions: List[str]) -> List[str]:
        if not path or not os.path.exists(path):
            return []
        exts = [e.lower() for e in extensions]
        return [
            os.path.join(path, f)
            for f in os.listdir(path)
            if any(f.lower().endswith(ext) for ext in exts)
        ]

    def write_text(self, file_path: str, content: str) -> None:
        self.ensure_dir(os.path.dirname(file_path))
        with open(file_path, "w", encoding="utf-8") as fp:
            fp.write(content)

    def append_text(self, file_path: str, content: str) -> None:
        self.ensure_dir(os.path.dirname(file_path))
        with open(file_path, "a", encoding="utf-8") as fp:
            fp.write(content)
