from pathlib import Path
from typing import List


class ConstraintsCollector:
    """
    Base collector responsible for listing LP files needed for a validation run.
    """

    def __init__(self, domain_dir: Path, instance_dir: Path):
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir

    def collect(self) -> List[str]:
        raise NotImplementedError


def collect_common(domain_dir: Path, instance_dir: Path) -> List[str]:
    """
    Shared collection logic used by current domain collectors:
    - Prefer base/ for domain/actions/init/goal when domain_dir is not 'original'.
    - instance_init.lp > init.lp from the instance directory.
    - Include instance.lp.
    """
    files: List[str] = []
    domain_root = domain_dir
    base_dir = domain_root.parent / "base"

    # domain and actions
    for name in ["domain.lp", "actions.lp"]:
        path = (
            base_dir / name
            if domain_root.name != "original" and base_dir.exists()
            else domain_root / name
        )
        if path.exists():
            files.append(str(path.resolve()))

    # base init (if present)
    base_init = (
        base_dir / "init.lp"
        if domain_root.name != "original" and base_dir.exists()
        else domain_root / "init.lp"
    )
    if base_init.exists():
        files.append(str(base_init.resolve()))

    # instance init preference: instance_init.lp > init.lp
    for name in ["instance_init.lp", "init.lp"]:
        path = instance_dir / name
        if path.exists():
            files.append(str(path.resolve()))
            break

    # instance description
    inst = instance_dir / "instance.lp"
    if inst.exists():
        files.append(str(inst.resolve()))

    # goal
    goal = (
        base_dir / "goal.lp"
        if domain_root.name != "original" and base_dir.exists()
        else domain_root / "goal.lp"
    )
    if goal.exists():
        files.append(str(goal.resolve()))

    return files
