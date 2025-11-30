from typing import Dict


class BaseEvaluator:
    """Abstract base evaluator."""

    def evaluate(self, asp_result: Dict, parse_result: Dict, **kwargs) -> Dict:
        raise NotImplementedError
