from pathlib import Path
import re
from typing import Optional, List, Tuple


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
        use_base_template = False
        if instance_dir:
            loyalty_path = instance_dir / "loyalty.txt"
            if loyalty_path.exists():
                loyalty_text = loyalty_path.read_text().strip()
                use_base_template = True

        if use_base_template:
            prompt_text = (base_dir / self.domain / "base" / "prompt.txt").read_text()
            if loyalty_text:
                prompt_text = self.insert_loyalty(prompt_text, loyalty_text)
        else:
            prompt_text = super().load_prompt(base_dir, instance_dir)

        if instance_dir:
            prompt_text = self.augment_prompt(prompt_text, base_dir, instance_dir)
        return prompt_text

    def augment_prompt(self, prompt_text: str, base_dir: Path, instance_dir: Path) -> str:
        roles, loyals = self.parse_instance(instance_dir / "instance.lp")
        if roles or loyals:
            prompt_text += "\n\n"
        if roles:
            prompt_text += "Roles for this instance:\n"
            for name, desc in roles:
                prompt_text += f"- {name}: {desc}\n"
        if loyals:
            prompt_text += "Loyalty relations:\n"
            for a, b in loyals:
                prompt_text += f"- {a} is loyal to {b}\n"
        return prompt_text

    def parse_instance(self, path: Path) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        roles: List[Tuple[str, str]] = []
        loyals: List[Tuple[str, str]] = []
        if not path.exists():
            return roles, loyals
        role_re = re.compile(r'role\(([^,]+),\s*"([^"]*)"\s*\)\.')
        loyal_re = re.compile(r'attr\(is_loyal_to\(([^,]+),\s*([^)]+)\)\)\.')
        for line in path.read_text().splitlines():
            line = line.strip()
            m = role_re.match(line)
            if m:
                roles.append((m.group(1), m.group(2)))
                continue
            m = loyal_re.match(line)
            if m:
                loyals.append((m.group(1), m.group(2)))
        return roles, loyals

    def insert_loyalty(self, prompt_text: str, loyalty_text: str) -> str:
        parts = prompt_text.split("\n\n")
        if len(parts) >= 2:
            return "\n\n".join([parts[0], parts[1], "Loyalty relations:\n" + loyalty_text] + parts[2:])
        return prompt_text + "\n\nLoyalty relations:\n" + loyalty_text


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
