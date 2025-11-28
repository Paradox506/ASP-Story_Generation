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


class AladdinPromptBuilder(BasePromptBuilder):
    def build_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        loyalty_text = ""
        if instance_dir:
            loyalty_path = instance_dir / "loyalty.txt"
            if loyalty_path.exists():
                loyalty_text = loyalty_path.read_text().strip()
        else:
            loyalty_path = base_dir / self.domain / self.asp_version / "loyalty.txt"
            if loyalty_path.exists():
                loyalty_text = loyalty_path.read_text().strip()

        prompt_text = super().build_prompt(base_dir, instance_dir)
        if loyalty_text:
            parts = prompt_text.split("\n\n")
            if len(parts) >= 1:
                prompt_text = "\n\n".join([parts[0], loyalty_text] + parts[1:])
            else:
                prompt_text = prompt_text + "\n\n" + loyalty_text
        return prompt_text


class WesternPromptBuilder(BasePromptBuilder):
    def augment_prompt(self, prompt_text: str, base_dir: Path, instance_dir: Path) -> str:
        intro_path = instance_dir / "intro.txt"
        if intro_path.exists():
            prompt_text += "\n\nInstance intro:\n" + intro_path.read_text()
        return prompt_text


class SecretAgentPromptBuilder(BasePromptBuilder):
    def augment_prompt(self, prompt_text: str, base_dir: Path, instance_dir: Path) -> str:
        intro_path = instance_dir / "intro.txt"
        intro = intro_path.read_text() if intro_path.exists() else ""
        if prompt_text.strip() == "" and intro:
            prompt_text = intro
        elif intro:
            prompt_text += "\n\nMap description:\n" + intro
        return prompt_text


def get_prompt_builder(domain: str, asp_version: str):
    if domain == "aladdin":
        return AladdinPromptBuilder(domain, asp_version)
    if domain == "western":
        return WesternPromptBuilder(domain, asp_version)
    if domain == "secret_agent":
        return SecretAgentPromptBuilder(domain, asp_version)
    return BasePromptBuilder(domain, asp_version)
