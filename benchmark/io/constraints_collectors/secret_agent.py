from pathlib import Path
from typing import List

from benchmark.io.constraints_collectors.base import BaseConstraintsCollector


class SecretAgentConstraintsCollector(BaseConstraintsCollector):
    """Collector for the Secret Agent domain."""

    def collect(self) -> List[str]:
        files: List[str] = []
        seen = set()

        def add_path(p: Path):
            rp = str(p.resolve())
            if rp not in seen and p.exists():
                seen.add(rp)
                files.append(rp)

        constraints_dir = self.domain_dir / "constraints"
        for p in sorted(constraints_dir.glob("*.lp")):
            add_path(p)

        inst_constraints = self.instance_dir / "constraints"
        if inst_constraints.exists():
            for p in sorted(inst_constraints.glob("*.lp")):
                add_path(p)

        for p in sorted(self.instance_dir.glob("*.lp")):
            add_path(p)

        return files
