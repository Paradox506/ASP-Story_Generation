from pathlib import Path
from typing import Optional


class BasePromptBuilder:
    """Simple prompt builder with domain-specific augmentation hooks."""

    def __init__(self, domain: str, asp_version: str = "original"):
        self.domain = domain
        self.asp_version = asp_version

    def build_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        prompt_path = base_dir / self.domain / self.asp_version / "prompt.txt"
        if prompt_path.exists():
            prompt_text = prompt_path.read_text()
        else:
            prompt_text = (base_dir / self.domain / "base" / "prompt.txt").read_text()
        if instance_dir:
            prompt_text = self.augment_prompt(prompt_text, base_dir, instance_dir)
        return prompt_text

    def augment_prompt(self, prompt_text: str, base_dir: Path, instance_dir: Path) -> str:
        return prompt_text
