from pathlib import Path

from benchmark.prompts.base_prompt_builder import BasePromptBuilder


class SecretAgentPromptBuilder(BasePromptBuilder):
    def augment_prompt(self, prompt_text: str, base_dir: Path, instance_dir: Path) -> str:
        intro_path = instance_dir / "intro.txt"
        intro = intro_path.read_text() if intro_path.exists() else ""
        if prompt_text.strip() == "" and intro:
            prompt_text = intro
        elif intro:
            prompt_text += "\n\nMap description:\n" + intro
        return prompt_text
