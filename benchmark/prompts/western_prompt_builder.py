from pathlib import Path
from typing import Optional, List

from benchmark.prompts.base_prompt_builder import BasePromptBuilder


class WesternPromptBuilder(BasePromptBuilder):
    def build_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        """
        Western prompt assembly (domains-based):
        1) instance intro.txt (if present)
        2) prompts in domains/western/<asp_version>/prompts/, in order if present:
           intro.txt, 2map.txt, 3term_definitions.txt, 4instructions.txt, prompt.txt
        """
        parts: List[str] = []
        if instance_dir:
            intro_path = instance_dir / "intro.txt"
            if intro_path.exists():
                parts.append(intro_path.read_text().strip())
        prompt_dir = base_dir / "western" / self.asp_version / "prompts"
        for name in ["intro.txt", "2map.txt", "3term_definitions.txt", "4instructions.txt", "prompt.txt"]:
            p = prompt_dir / name
            if p.exists():
                parts.append(p.read_text().strip())
        return "\n\n".join(parts)
