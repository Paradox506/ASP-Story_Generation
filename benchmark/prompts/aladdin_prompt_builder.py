from pathlib import Path
from typing import Optional

from benchmark.prompts.base_prompt_builder import BasePromptBuilder


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
