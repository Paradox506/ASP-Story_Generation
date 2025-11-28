from pathlib import Path
from typing import Optional


class BasePromptGenerator:
    def __init__(self, domain: str, asp_version: str = "original"):
        self.domain = domain
        self.asp_version = asp_version

    def load_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
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


class AladdinPromptGenerator(BasePromptGenerator):
    def load_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        loyalty_text = ""
        if instance_dir:
            loyalty_path = instance_dir / "loyalty.txt"
            if loyalty_path.exists():
                loyalty_text = loyalty_path.read_text().strip()
        else:
            # allow loyalty at asp_version directory
            loyalty_path = base_dir / self.domain / self.asp_version / "loyalty.txt"
            if loyalty_path.exists():
                loyalty_text = loyalty_path.read_text().strip()

        prompt_text = super().load_prompt(base_dir, instance_dir)
        if loyalty_text:
            parts = prompt_text.split("\n\n")
            if len(parts) >= 1:
                prompt_text = "\n\n".join([parts[0], loyalty_text] + parts[1:])
            else:
                prompt_text = prompt_text + "\n\n" + loyalty_text
        return prompt_text


class WesternPromptGenerator(BasePromptGenerator):
    def augment_prompt(self, prompt_text: str, base_dir: Path, instance_dir: Path) -> str:
        intro = self.read_optional(instance_dir / "intro.txt")
        if intro:
            prompt_text += "\n\nInstance intro:\n" + intro
        return prompt_text

    def read_optional(self, path: Path) -> str:
        return path.read_text() if path.exists() else ""


class SecretAgentPromptGenerator(BasePromptGenerator):
    def augment_prompt(self, prompt_text: str, base_dir: Path, instance_dir: Path) -> str:
        intro = self.read_optional(instance_dir / "intro.txt")
        if prompt_text.strip() == "" and intro:
            prompt_text = intro
        elif intro:
            prompt_text += "\n\nMap description:\n" + intro
        return prompt_text

    def read_optional(self, path: Path) -> str:
        return path.read_text() if path.exists() else ""


def get_prompt_generator(domain: str, asp_version: str):
    if domain == "aladdin":
        return AladdinPromptGenerator(domain, asp_version)
    if domain == "western":
        return WesternPromptGenerator(domain, asp_version)
    if domain == "secret_agent":
        return SecretAgentPromptGenerator(domain, asp_version)
    return BasePromptGenerator(domain, asp_version)
