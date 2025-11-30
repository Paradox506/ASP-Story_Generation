from pathlib import Path
from typing import List


class BaseConstraintsCollector:
    """
    Base collector responsible for listing LP files needed for a validation run.
    """

    def __init__(self, domain_dir: Path, instance_dir: Path):
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir

    def collect(self) -> List[str]:
        raise NotImplementedError
