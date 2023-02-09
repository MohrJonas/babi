from __future__ import annotations

import re
from pathlib import Path


class Grep:
    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def search_string(self, query: str) -> list[tuple[Path, list[re.match]]]:
        results = []
        pattern = re.compile(query)
        for file in self.directory.iterdir():
            with open(file) as f:
                try:
                    content = f.read()
                    m = list(re.finditer(pattern, content))
                    if len(m) == 0:
                        continue
                    results.append((file, m))
                except UnicodeDecodeError:
                    continue
        return results
