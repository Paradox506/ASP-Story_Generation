from typing import Dict, List

from benchmark.asp.action_utils import ActionMapper

from .base import ConstraintBuilder


class WesternConstraintBuilder(ConstraintBuilder):
    def __init__(self, mapper: ActionMapper):
        super().__init__(mapper)

    def build(self, actions: List[Dict]) -> str:
        lines: List[str] = []
        for i, action in enumerate(actions):
            subj = action["subject"]
            aid = action["actionId"]
            params = action.get("parameters", [])
            functor = self.mapper.to_asp_functor(aid, params)
            # Action 1 (snakebite) is unintentional -> act/3
            if aid == 1:
                lines.append(f"act({subj}, {functor}, {i}).")
                continue
            # Action 6 (do nothing) not represented in ASP; skip
            if aid == 6:
                continue
            intention = self._default_intention(aid, params, subj)
            executed_flag = action.get("executed", True)
            if executed_flag:
                lines.append(f"act({subj}, {functor}, {intention}, {i}).")
            else:
                # use unexec_act to indicate non-executed intentional action
                lines.append(f"unexec_act({subj}, {functor}, {intention}, {i}).")
        return "\n".join(lines)

    def _default_intention(self, aid: int, params: List[str], subj: str) -> str:
        if aid == 2 and params:  # move(Dest)
            return f"at({subj},{params[0]})"
        if aid == 3 and len(params) >= 2:  # take(Obj, Ch)
            return f"possessed_by({params[0]},{subj})"
        if aid == 4 and params:  # heal(Target, Item)
            return f"alive({params[0]})"
        if aid == 5 and params:  # kill(Victim)
            return f"dead({params[0]})"
        return "alive(timmy)"
