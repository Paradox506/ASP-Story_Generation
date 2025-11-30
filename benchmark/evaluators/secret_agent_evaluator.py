from typing import Dict


class SecretAgentEvaluator:
    def evaluate(self, asp_result: Dict, parse_result: Dict) -> Dict:
        satisfiable = asp_result.get("satisfiable", False)
        nonexec = asp_result.get("nonexec_feedback", []) or []
        causal_sound = satisfiable and len(nonexec) == 0
        goal_achieved = satisfiable
        return {
            "causal_sound": causal_sound,
            "goal_achieved": goal_achieved,
            "nonexec_count": len(nonexec),
            "nonexec_details": nonexec,
            "plan_length": len(parse_result.get("actions", []) if parse_result else []),
        }
