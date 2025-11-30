from typing import Dict, Any, List


class BaseEvaluator:
    """Abstract base evaluator."""

    def evaluate(self, asp_result: Dict, parse_result: Dict, **kwargs) -> Dict:
        satisfiable = asp_result.get("satisfiable", False)
        nonexec: List[Any] = asp_result.get("nonexec_feedback", []) or []
        actions = parse_result.get("actions", []) if parse_result else []
        executed = [a for a in actions if a.get("executed", True)]
        nonexecuted = [a for a in actions if not a.get("executed", True)]
        base = {
            "causal_sound": satisfiable and len(nonexec) == 0,
            "nonexec_count": len(nonexec),
            "nonexec_details": nonexec,
            "executed_actions": len(executed),
            "nonexecuted_actions": len(nonexecuted),
            "plan_length": len(actions),
        }
        extra = self.extra_metrics(asp_result, parse_result, **kwargs)
        base.update(extra or {})
        return base

    def extra_metrics(self, asp_result: Dict, parse_result: Dict, **kwargs) -> Dict:
        """
        Subclasses override to add domain-specific metrics/fields.
        """
        return {}
