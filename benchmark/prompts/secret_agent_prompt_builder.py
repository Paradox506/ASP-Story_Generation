from pathlib import Path
from typing import Optional, List, Tuple, Dict

from benchmark.prompts.base_prompt_builder import BasePromptBuilder


class SecretAgentPromptBuilder(BasePromptBuilder):
    """
    Secret Agent prompt builder:
    - Expects an instance_dir with a matrix.txt describing the grid.
    - No fallback: missing matrix.txt will raise an error.
    """

    def build_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        if not instance_dir:
            raise ValueError("SecretAgentPromptBuilder requires an instance_dir with matrix.txt")
        matrix_path = instance_dir / "matrix.txt"
        if not matrix_path.exists():
            raise FileNotFoundError(f"Missing matrix.txt in {instance_dir}")
        grid = self.read_matrix(matrix_path)
        return self.generate_prompt_from_grid(grid)

    # --- Inline helpers adapted from generate_secret_agent_prompt.py ---
    def read_matrix(self, file_path: Path) -> List[List[int]]:
        lines = file_path.read_text().splitlines()
        matrix: List[List[int]] = []
        for line in lines:
            line = line.strip()
            if line:
                row = [int(ch) for ch in line if ch.isdigit()]
                if row:
                    matrix.append(row)
        if not matrix:
            raise ValueError(f"Empty matrix in {file_path}")
        return matrix

    def location_name(self, pos: Tuple[int, int]) -> str:
        return f"l{pos[0]}_{pos[1]}"

    def parse_grid(self, grid: List[List[int]]) -> Dict:
        n = len(grid)
        walkable = []
        walls = []
        dox = []
        gun = None
        for i in range(n):
            for j in range(len(grid[i])):
                val = grid[i][j]
                if val == 1:
                    walls.append((i, j))
                elif val == 0:
                    walkable.append((i, j))
                elif val == 2:
                    dox.append((i, j))
                    walkable.append((i, j))
                elif val == 3:
                    gun = (i, j)
                    walkable.append((i, j))
        return {
            "size": n,
            "walkable_cells": walkable,
            "walls": walls,
            "dox_locations": dox,
            "gun_location": gun,
            "agent_start": (0, 0),
            "mastermind_location": (n - 1, n - 1),
        }

    def generate_connections(self, grid: List[List[int]]) -> List[Tuple[str, str]]:
        n = len(grid)
        conns = []
        for i in range(n):
            for j in range(len(grid[i])):
                if grid[i][j] == 1:
                    continue
                curr = self.location_name((i, j))
                for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < n and 0 <= nj < len(grid[ni]) and grid[ni][nj] != 1:
                        conns.append((curr, self.location_name((ni, nj))))
        return conns

    def generate_guarded_connections(self, n: int) -> List[Tuple[str, str]]:
        mm = self.location_name((n - 1, n - 1))
        return [
            (self.location_name((n - 2, n - 1)), mm),
            (self.location_name((n - 1, n - 2)), mm),
        ]

    def generate_prompt_from_grid(self, grid: List[List[int]]) -> str:
        info = self.parse_grid(grid)
        n = info["size"]
        prompt += "## Mission Overview\n"
        prompt += (
            f"You are a secret agent operating in a {n}x{n} grid-based facility. "
            "Your mission is to infiltrate the facility, gather intelligence documents, "
            "obtain the gun, and kill the mastermind.\n\n"
        )
        prompt += "## Initial State\n\n"
        prompt += f"- **Your starting location**: {self.location_name(info['agent_start'])}\n"
        prompt += f"- **Mastermind's location**: {self.location_name(info['mastermind_location'])}\n"
        if info["gun_location"]:
            prompt += f"- **Gun location**: {self.location_name(info['gun_location'])}\n"
        else:
            prompt += "- **Gun location**: Not present in this map\n"
        if info["dox_locations"]:
            prompt += f"- **Document fragments**: {len(info['dox_locations'])} fragment(s) to collect\n"
            for idx, loc in enumerate(info["dox_locations"]):
                prompt += f"  - dox{idx} is at {self.location_name(loc)}\n"
        else:
            prompt += "- **Document fragments**: None present\n"
        prompt += "\n"
        prompt += "## Movement Rules\n\n"
        conns = self.generate_connections(grid)
        prompt += f"You can move between {len(conns)} pairs of adjacent locations:\n\n"
        for a, b in conns:
            prompt += f"- You can move from {a} to {b}\n"
        prompt += "\n"
        prompt += "## Available Actions\n\n"
        prompt += "You can perform the following actions. Each action has specific requirements:\n\n"
        prompt += "### 1. move(location)\n"
        prompt += "- **Description**: Move to an adjacent location\n"
        prompt += "- **Parameter**: `location` - the target location to move to\n"
        prompt += "- **Requirements**:\n"
        prompt += "  - The target location must be directly connected to your current location\n"
        prompt += "  - The connection must exist in the Movement Rules above\n"
        prompt += "- **Example**: `move(l0_1)`\n\n"
        prompt += "### 2. move_through_guards(location, dox)\n"
        prompt += "- **Description**: Move through guarded entrance by presenting assembled dox\n"
        prompt += "- **Parameters**:\n"
        prompt += "  - `location` - the target guarded location\n"
        prompt += "  - `dox` - the assembled document to present to guards\n"
        prompt += "- **Requirements**:\n"
        prompt += "  - You must have the assembled dox (all fragments collected)\n"
        prompt += "  - The target location must be accessible through a guarded connection\n"
        prompt += "- **Example**: `move_through_guards(l9_9, dox)`\n\n"
        prompt += "### 3. pickup(item)\n"
        prompt += "- **Description**: Pick up an item at your current location\n"
        prompt += "- **Parameter**: `item` - the item to pick up (gun or dox fragment)\n"
        prompt += "- **Requirements**:\n"
        prompt += "  - The item must be at your current location\n"
        prompt += "  - Valid items: gun, dox0, dox1, etc.\n\n"
        prompt += "### 4. kill(target)\n"
        prompt += "- **Description**: Kill a target\n"
        prompt += "- **Parameter**: `target` - the mastermind (or a guard if necessary)\n"
        prompt += "- **Requirements**:\n"
        prompt += "  - You must possess the gun\n"
        prompt += "  - You must be at the same location as the target\n"
        prompt += "- **Effects**: Target is eliminated\n\n"
        prompt += "## Goals\n\n"
        prompt += "- Collect all document fragments and assemble the dox\n"
        prompt += "- Obtain the gun\n"
        prompt += "- Kill the mastermind at the guarded location\n"
        prompt += "- Avoid walls and respect guarded entrances (use move_through_guards)\n"
        prompt += "\n## Output Format\n"
        prompt += "Return only a JSON array of actions in order, no explanations or additional text.\n"
        prompt += "Each action must include: subject, actionId, parameters, executed (boolean).\n"
        prompt += "Do not add commentary; respond with the JSON array only.\n"
        return prompt
