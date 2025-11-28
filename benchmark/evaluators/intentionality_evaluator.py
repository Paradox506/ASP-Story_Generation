from typing import Dict, List


class IntentionalityEvaluator:
    """
    Evaluator for Aladdin intentional planning.
    """

    def evaluate(self, asp_result: Dict, parse_result: Dict) -> Dict:
        nonexec = asp_result.get("nonexec_feedback", []) or []
        unjustified = asp_result.get("unjustified", []) or []
        open_frames = asp_result.get("open_commitment_frames", []) or []
        causal_sound = asp_result.get("satisfiable", False) and len(nonexec) == 0
        actions: List[Dict] = parse_result.get("actions", []) if parse_result else []
        intentional_actions = [a for a in actions if a.get("actionId") not in (0, 7, 8)]
        actions_with_plan = [a for a in intentional_actions if a.get("character_plan")]
        filled = [a for a in actions if a.get("_filled_params")]

        def _ratio(num: int, den: int) -> float:
            return num / den if den else 0.0

        # Simple coverage-based score: fraction with plans minus penalties
        intention_coverage = _ratio(len(actions_with_plan), len(intentional_actions))
        open_penalty = _ratio(len(open_frames), len(intentional_actions))
        unjust_penalty = _ratio(len(unjustified), len(intentional_actions))
        score = max(0.0, intention_coverage - open_penalty - unjust_penalty)

        return {
            "causal_sound": causal_sound,
            "intentionality_score": score,
            "intentional_actions": len(intentional_actions),
            "actions_with_plan": len(actions_with_plan),
            "open_frames_count": len(open_frames),
            "unjustified_count": len(unjustified),
            "nonexec_count": len(nonexec),
            "nonexec_details": nonexec,
            "open_frames_details": open_frames,
            "unjustified_details": unjustified,
            "filled_param_actions": len(filled),
            "plan_length": len(actions),
        }
