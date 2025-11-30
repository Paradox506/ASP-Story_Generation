from pathlib import Path
from typing import Optional

from benchmark.prompts.base_prompt_builder import BasePromptBuilder
from benchmark.prompts.secret_agent.generate_secret_agent_prompt import (
    read_matrix,
    generate_prompt_from_grid,
)


class SecretAgentPromptBuilder(BasePromptBuilder):
    """
    Secret Agent prompt builder:
    - Expects an instance_dir with a matrix.txt describing the grid.
    - Uses the upstream generate_secret_agent_prompt helpers to render the full prompt.
    - If no instance is provided or matrix is missing, falls back to base prompt.txt.
    """

    def build_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        if instance_dir:
            matrix_path = instance_dir / "matrix.txt"
            if matrix_path.exists():
                grid = read_matrix(str(matrix_path))
                return generate_prompt_from_grid(grid)
        # fallback to legacy behavior
        return super().build_prompt(base_dir, instance_dir)
