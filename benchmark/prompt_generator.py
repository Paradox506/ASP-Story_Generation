import re
from pathlib import Path
from typing import Optional, Tuple, List


class PromptGenerator:
    """
    Prompt loader with light-weight templating for Aladdin instances.
    Other domains currently return the static prompt text.
    """

    def __init__(self, domain: str, asp_version: str = "original"):
        self.domain = domain
        self.asp_version = asp_version

    def load_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        """
        base_dir: repository root path.
        instance_dir: used for Aladdin to append instance-specific facts (roles, loyalty).
        """
        path = base_dir / self.domain / self.asp_version / "prompt.txt"
        use_base_template = False
        loyalty_text = ""

        if self.domain == "aladdin" and instance_dir is not None:
            loyalty_path = instance_dir / "loyalty.txt"
            if loyalty_path.exists():
                loyalty_text = loyalty_path.read_text().strip()
                use_base_template = True

        if use_base_template:
            prompt_text = (base_dir / self.domain / "base" / "prompt.txt").read_text()
            if loyalty_text:
                prompt_text = self._insert_loyalty(prompt_text, loyalty_text)
        else:
            if not path.exists():
                fallback = base_dir / self.domain / "base" / "prompt.txt"
                prompt_text = fallback.read_text()
            else:
                prompt_text = path.read_text()

        if self.domain == "aladdin" and instance_dir is not None:
            prompt_text = self._augment_aladdin(prompt_text, instance_dir)
        elif self.domain == "western" and instance_dir is not None:
            prompt_text = self._augment_western(prompt_text, instance_dir)
        elif self.domain == "secret_agent" and instance_dir is not None:
            prompt_text = self._augment_secret_agent(prompt_text, instance_dir)
        return prompt_text

    def _augment_aladdin(self, prompt_text: str, instance_dir: Path) -> str:
        roles, loyals = self._parse_aladdin_instance(instance_dir / "instance.lp")
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

    def _insert_loyalty(self, prompt_text: str, loyalty_text: str) -> str:
        """
        Insert loyalty description after the second paragraph (first blank line).
        """
        parts = prompt_text.split("\n\n")
        if len(parts) >= 2:
            return "\n\n".join([parts[0], parts[1], "Loyalty relations:\n" + loyalty_text] + parts[2:])
        return prompt_text + "\n\nLoyalty relations:\n" + loyalty_text

    def _augment_western(self, prompt_text: str, instance_dir: Path) -> str:
        intro = self._read_optional(instance_dir / "intro.txt")
        if intro:
            prompt_text += "\n\nInstance intro:\n" + intro
        return prompt_text

    def _augment_secret_agent(self, prompt_text: str, instance_dir: Path) -> str:
        intro = self._read_optional(instance_dir / "intro.txt")
        if prompt_text.strip() == "" and intro:
            prompt_text = intro
        elif intro:
            prompt_text += "\n\nMap description:\n" + intro
        return prompt_text

    def _parse_aladdin_instance(self, path: Path) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
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

    def _read_optional(self, path: Path) -> str:
        return path.read_text() if path.exists() else ""
