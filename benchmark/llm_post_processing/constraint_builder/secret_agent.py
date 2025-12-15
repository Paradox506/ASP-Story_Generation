from typing import Any, Dict, List, Optional

from .base import ConstraintBuilder


class SecretAgentConstraintBuilder(ConstraintBuilder):
    def __init__(self, mapper):  # mapper unused, kept for interface compatibility
        super().__init__(mapper)

    def build(self, actions: List[Dict], maxstep: Optional[int] = None) -> str:
        max_const = maxstep or (len(actions) + 1)
        lines: List[str] = [f"#const maxstep={max_const}.", "% Secret Agent plan constraints"]
        for t, action in enumerate(actions):
            subj = action["subject"]
            functor = self.functor_from_action(action)
            lines.append(f":- not act({subj}, {functor}, {t}).")
        return "\n".join(lines) + "\n"

    def functor_from_action(self, action: Dict[str, Any]) -> str:
        functor = action.get("functor")
        params = action.get("parameters", [])
        if functor in ("move", "pickup") and len(params) == 1:
            return f"{functor}({params[0]})"
        if functor == "kill" and len(params) >= 2:
            return f"{functor}({params[0]},{params[1]})"
        if functor == "move_through_guards" and len(params) >= 2:
            return f"{functor}({params[0]},{params[1]})"
        if functor and params:
            joined = ",".join(str(p) for p in params)
            return f"{functor}({joined})"
        return str(functor) if functor else "act"
