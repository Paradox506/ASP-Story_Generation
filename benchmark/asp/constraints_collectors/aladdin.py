from pathlib import Path
from typing import List

from benchmark.asp.constraints_collectors.base import ConstraintsCollector, collect_common


class AladdinConstraintsCollector(ConstraintsCollector):
    """Collector for the Aladdin domain."""

    def collect(self) -> List[str]:
        return collect_common(self.domain_dir, self.instance_dir)
