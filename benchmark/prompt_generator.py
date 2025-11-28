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
        prompt_text = path.read_text()

        if self.domain == "aladdin" and instance_dir is not None:
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
        elif self.domain == "western" and instance_dir is not None:
            intro = self._read_optional(instance_dir / "intro.txt")
            if intro:
                prompt_text += "\n\nInstance intro:\n" + intro
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
