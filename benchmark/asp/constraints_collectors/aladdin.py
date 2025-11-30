from pathlib import Path
from typing import List

from benchmark.asp.constraints_collectors.base import BaseConstraintsCollector


class AladdinConstraintsCollector(BaseConstraintsCollector):
    """Collector for the Aladdin domain."""

    def collect(self) -> List[str]:
        files: List[str] = []
        constraints_dir = self.domain_dir / "constraints"

        for name in ["domain.lp", "actions.lp", "init.lp", "goal.lp"]:
            path = constraints_dir / name
            if path.exists():
                files.append(str(path.resolve()))

        for name in ["instance_init.lp", "init.lp"]:
            path = self.instance_dir / name
            if path.exists():
                files.append(str(path.resolve()))
                break

        inst = self.instance_dir / "instance.lp"
        if inst.exists():
            files.append(str(inst.resolve()))

        return files
