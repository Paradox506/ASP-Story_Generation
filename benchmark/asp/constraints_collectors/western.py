from pathlib import Path
from typing import List

from benchmark.asp.constraints_collectors.base import BaseConstraintsCollector


class WesternConstraintsCollector(BaseConstraintsCollector):
    """Collector for the Western domain."""

    def collect(self) -> List[str]:
        files: List[str] = []
        domain_root = self.domain_dir
        base_dir = domain_root.parent / "base"

        for name in ["domain.lp", "actions.lp"]:
            path = (
                base_dir / name
                if domain_root.name != "original" and base_dir.exists()
                else domain_root / name
            )
            if path.exists():
                files.append(str(path.resolve()))

        base_init = (
            base_dir / "init.lp"
            if domain_root.name != "original" and base_dir.exists()
            else domain_root / "init.lp"
        )
        if base_init.exists():
            files.append(str(base_init.resolve()))

        for name in ["instance_init.lp", "init.lp"]:
            path = self.instance_dir / name
            if path.exists():
                files.append(str(path.resolve()))
                break

        inst = self.instance_dir / "instance.lp"
        if inst.exists():
            files.append(str(inst.resolve()))

        goal = (
            base_dir / "goal.lp"
            if domain_root.name != "original" and base_dir.exists()
            else domain_root / "goal.lp"
        )
        if goal.exists():
            files.append(str(goal.resolve()))

        return files
