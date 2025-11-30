from typing import Dict, List

from benchmark.asp.action_utils import ActionMapper, extract_intention

from .base import ConstraintBuilder


class AladdinConstraintBuilder(ConstraintBuilder):
    def __init__(self, mapper: ActionMapper, use_default_intention: bool = False):
        super().__init__(mapper)
        # Unintentional actions are encoded as act/3 in the ASP (no intention argument)
        self.unintentional_ids = {0, 7, 8}
        self.use_default_intention = use_default_intention

    def _default_intention(self, aid: int, params: List[str], subj: str) -> str:
        """
        Provide a valid intention/1 term when the character_plan does not give one.
        These are heuristic fallbacks aligned with declared intentions in domain.lp:
        - dead(X)
        - marry(X)
        - possessed_by(Obj, Subj)
        """
        if aid == 1 and len(params) >= 2:  # cast_love_spell(Target, Lover)
            return f"marry({params[1]})"
        if aid == 2 and len(params) >= 2:  # pillage(Body, Obj)
            return f"possessed_by({params[1]}, {subj})"
        if aid == 3 and params:  # kill(Victim)
            return f"dead({params[0]})"
        if aid == 4 and params:  # marry(Ch)
            return f"marry({params[0]})"
        if aid == 5 and len(params) >= 2:  # give(Givee, Obj)
            return f"possessed_by({params[1]}, {params[0]})"
        if aid == 6:  # move(Dest)
            return f"possessed_by(lamp, {subj})"
        if aid == 9 and len(params) >= 2:  # order_to_kill(Knight, Victim)
            return f"dead({params[1]})"
        if aid == 10 and params:  # order_to_obtain(Knight, Obj)
            return f"possessed_by({params[-1]}, {subj})"
        # generic safe fallback
        return "marry(polly)"

    def build(self, actions: List[Dict]) -> str:
        lines: List[str] = []
        for i, action in enumerate(actions):
            subj = action["subject"]
            aid = action["actionId"]
            params = action.get("parameters", [])
            functor = self.mapper.to_asp_functor(aid, params)
            if aid in self.unintentional_ids:
                # act/3 form for unintentional actions (appear_threatening, fall_in_love, do_nothing)
                lines.append(f"act({subj}, {functor}, {i}).")
                continue

            intention = extract_intention(action.get("character_plan", ""))
            if not intention and self.use_default_intention:
                intention = self._default_intention(aid, params, subj)
            if not intention:
                raise ValueError(f"Missing intention for actionId={aid} at step {i}")
            lines.append(f"act({subj}, {functor}, {intention}, {i}).")
        return "\n".join(lines)
