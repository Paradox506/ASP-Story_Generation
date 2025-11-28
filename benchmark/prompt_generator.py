from pathlib import Path
from typing import Optional


class PromptGenerator:
    """
    Minimal prompt loader. For now, it simply returns the original prompt
    text shipped with the dataset (no templating).
    """

    def __init__(self, domain: str, asp_version: str = "original"):
        self.domain = domain
        self.asp_version = asp_version

    def load_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        """
        base_dir: repository root path.
        instance_dir: unused for now (reserved for future templating).
        """
        path = base_dir / self.domain / self.asp_version / "prompt.txt"
        return path.read_text()
