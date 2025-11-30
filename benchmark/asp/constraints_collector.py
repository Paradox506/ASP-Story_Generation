from pathlib import Path
from typing import List, Optional


class ConstraintsCollector:
    """
    Base collector responsible for listing LP files needed for a validation run.
    """

    def __init__(self, domain_dir: Path, instance_dir: Path):
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir

    def collect(self) -> List[str]:
        """
        Return an ordered list of LP file paths to feed into clingo.
        """
        raise NotImplementedError


class SecretAgentConstraintsCollector(ConstraintsCollector):
    """
    Collector that mirrors the prior ASPValidator _collect_files logic:
    - domain_dir may be base/original variant; if not original, prefer base/ for domain/actions/init/goal.
    - instance_dir may contain instance_init.lp or init.lp; take the first that exists.
    """

    def collect(self) -> List[str]:
        files: List[str] = []
        domain_root = self.domain_dir
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
            path = self.instance_dir / name
            if path.exists():
                files.append(str(path.resolve()))
                break

        # instance description
        inst = self.instance_dir / "instance.lp"
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


class WesternConstraintsCollector(ConstraintsCollector):
    """Western domain collector; same layout rules as the prior validator."""

    def collect(self) -> List[str]:
        files: List[str] = []
        domain_root = self.domain_dir
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
            path = self.instance_dir / name
            if path.exists():
                files.append(str(path.resolve()))
                break

        # instance description
        inst = self.instance_dir / "instance.lp"
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


class AladdinConstraintsCollector(ConstraintsCollector):
    """Aladdin domain collector; reuses the same path rules."""

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


def get_collector(domain: str, domain_dir: Path, instance_dir: Path, collector: Optional[ConstraintsCollector] = None) -> ConstraintsCollector:
    """
    Factory to obtain the proper collector per domain.
    """
    if collector is not None:
        return collector
    if domain == "secret_agent":
        return SecretAgentConstraintsCollector(domain_dir, instance_dir)
    if domain == "western":
        return WesternConstraintsCollector(domain_dir, instance_dir)
    if domain == "aladdin":
        return AladdinConstraintsCollector(domain_dir, instance_dir)
    raise NotImplementedError(f"Constraints collector not implemented for domain: {domain}")
