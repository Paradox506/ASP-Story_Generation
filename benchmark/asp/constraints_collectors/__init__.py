from pathlib import Path
from typing import Optional, List


class BaseConstraintsCollector:
    """
    Base collector responsible for listing LP files needed for a validation run.
    """

    def __init__(self, domain_dir: Path, instance_dir: Path):
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir

    def collect(self) -> List[str]:
        raise NotImplementedError


class SecretAgentConstraintsCollector(BaseConstraintsCollector):
    """Collector for the Secret Agent domain."""

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


class AladdinConstraintsCollector(BaseConstraintsCollector):
    """Collector for the Aladdin domain."""

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


def get_collector(domain: str, domain_dir: Path, instance_dir: Path, collector: Optional[BaseConstraintsCollector] = None) -> BaseConstraintsCollector:
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


__all__ = [
    "BaseConstraintsCollector",
    "get_collector",
    "SecretAgentConstraintsCollector",
    "WesternConstraintsCollector",
    "AladdinConstraintsCollector",
]
