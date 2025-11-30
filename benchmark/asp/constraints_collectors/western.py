from pathlib import Path
from typing import List

from benchmark.asp.constraints_collectors.base import BaseConstraintsCollector


class WesternConstraintsCollector(BaseConstraintsCollector):
    """Collector for the Western domain."""

    def collect(self) -> List[str]:
        files: List[str] = []
        constraints_dir = self.domain_dir / "constraints"

        for name in ["domain.lp", "actions.lp", "init.lp"]:
            path = constraints_dir / name
            if path.exists():
                files.append(str(path.resolve()))

        # instance-specific constraints (if any)
        inst_constraints = self.instance_dir / "constraints"
        if inst_constraints.exists():
            for p in sorted(inst_constraints.glob("*.lp")):
                files.append(str(p.resolve()))

        for name in ["instance_init.lp", "init.lp"]:
            path = self.instance_dir / name
            if path.exists():
                files.append(str(path.resolve()))
                break

        inst = self.instance_dir / "instance.lp"
        if inst.exists():
            files.append(str(inst.resolve()))

        goal = constraints_dir / "goal.lp"
        if goal.exists():
            files.append(str(goal.resolve()))

        return files
