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
        lines: List[str] = []
        lines.append("# Secret Agent Mission Briefing\n")
        lines.append("## Mission Overview\n")
        lines.append(
            f"You are a secret agent operating in a {n}x{n} grid-based facility. "
            "Your mission is to infiltrate the facility, gather intelligence documents, "
            "obtain the gun, and kill the mastermind.\n"
        )
        lines.append("## Initial State\n")
        lines.append(f"- **Your starting location**: {self.location_name(info['agent_start'])}")
        lines.append(f"- **Mastermind's location**: {self.location_name(info['mastermind_location'])}")
        if info["gun_location"]:
            lines.append(f"- **Gun location**: {self.location_name(info['gun_location'])}")
        else:
            lines.append("- **Gun location**: Not present in this map")
        if info["dox_locations"]:
            lines.append(f"- **Document fragments**: {len(info['dox_locations'])} fragment(s) to collect")
            for idx, loc in enumerate(info["dox_locations"]):
                lines.append(f"  - dox{idx} is at {self.location_name(loc)}")
        else:
            lines.append("- **Document fragments**: None present")
        lines.append("")
        lines.append("## Movement Rules")
        conns = self.generate_connections(grid)
        lines.append(f"You can move between {len(conns)} pairs of adjacent locations:")
        for a, b in conns:
            lines.append(f"- You can move from {a} to {b}")
        lines.append("")
        lines.append("## Available Actions")
        lines.append("You can perform the following actions. Each action has specific requirements:")
        lines.append("")
        lines.append("### 1. move(location)")
        lines.append("- Description: Move to an adjacent location")
        lines.append("- Parameter: `location` - the target location to move to")
        lines.append("- Requirements:")
        lines.append("  - The target location must be directly connected to your current location")
        lines.append("  - The connection must exist in the Movement Rules above")
        lines.append("- Example: `move(l0_1)`")
        lines.append("")
        lines.append("### 2. move_through_guards(location, dox)")
        lines.append("- Description: Move through guarded entrance by presenting assembled dox")
        lines.append("- Parameters:")
        lines.append("  - `location` - the target guarded location")
        lines.append("  - `dox` - the assembled document to present to guards")
        lines.append("- Requirements:")
        lines.append("  - You must have the assembled dox (all fragments collected)")
        lines.append("  - The target location must be accessible through a guarded connection")
        lines.append("- Example: `move_through_guards(l9_9, dox)`")
        lines.append("")
        lines.append("### 3. pickup(item)")
        lines.append("- Description: Pick up an item at your current location")
        lines.append("- Parameter: `item` - the item to pick up (gun or dox fragment)")
        lines.append("- Requirements:")
        lines.append("  - The item must be at your current location")
        lines.append("  - Valid items: gun, dox0, dox1, etc.")
        lines.append("")
        lines.append("### 4. kill(target)")
        lines.append("- Description: Kill a target")
        lines.append("- Parameter: `target` - the mastermind (or a guard if necessary)")
        lines.append("- Requirements:")
        lines.append("  - You must possess the gun")
        lines.append("  - You must be at the same location as the target")
        lines.append("- Effects: Target is eliminated")
        lines.append("")
        lines.append("## Goals")
        lines.append("- Collect all document fragments and assemble the dox")
        lines.append("- Obtain the gun")
        lines.append("- Kill the mastermind at the guarded location")
        lines.append("- Avoid walls and respect guarded entrances (use move_through_guards)")
        lines.append("")
        lines.append("## Output Format")
        lines.append("Return only a JSON array of actions in order, no explanations or additional text.")
        lines.append("Each action must include: subject, actionId, parameters, executed (boolean).")
        lines.append("Do not add commentary; respond with the JSON array only.")
        return "\n".join(lines) + "\n"
