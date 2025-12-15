from typing import Dict, List, Optional

from benchmark.asp.action_utils import ActionMapper

from .base import ConstraintBuilder


class WesternConstraintBuilder(ConstraintBuilder):
    def __init__(self, mapper: ActionMapper, use_default_intention: bool = False):
        super().__init__(mapper)
        self.use_default_intention = use_default_intention

    def build(self, actions: List[Dict], maxstep: Optional[int] = None) -> str:
        max_const = maxstep or (len(actions) + 1)
        lines: List[str] = [f"#const maxstep={max_const}.", "% Western plan constraints"]
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
            intention = action.get("intention") or None
            if hasattr(action, "get") and "normalized_intention" in action:
                intention = action.get("normalized_intention") or intention
            if not intention and self.use_default_intention:
                intention = self.default_intention(aid, params, subj)
            if not intention:
                intention = "_"
            executed_flag = action.get("executed", True)
            if executed_flag:
                lines.append(f"act({subj}, {functor}, {intention}, {i}).")
            else:
                # use unexec_act to indicate non-executed intentional action
                lines.append(f"unexec_act({subj}, {functor}, {intention}, {i}).")
        lines.append(":- not conflict(_,_,_,_,_).")
        return "\n".join(lines)

    def default_intention(self, aid: int, params: List[str], subj: str) -> str:
        if aid == 2 and params:  # move(Dest)
            return f"at({subj},{params[0]})"
        if aid == 3 and len(params) >= 2:  # take(Obj, Ch)
            return f"possessed_by({params[0]},{subj})"
        if aid == 4 and params:  # heal(Target, Item)
            return f"alive({params[0]})"
        if aid == 5 and params:  # kill(Victim)
            return f"dead({params[0]})"
        return "alive(timmy)"
