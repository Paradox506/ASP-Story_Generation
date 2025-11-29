"""
Alternate plan parser/constraint builder that mirrors the author-log style:
- Do not assert act/unexec_act facts; instead emit constraints (:- not act(...).)
- Intentions are ignored; use '_' placeholder as the third argument.
- Optionally force the presence of at least one conflict/5 atom.
"""

from pathlib import Path
from typing import Dict, List, Any

from benchmark.asp.action_utils import ActionMapper
from benchmark.llm_post_processing.plan_parser import get_plan_parser


class AuthorStyleConstraintBuilder:
    def __init__(self, domain: str, require_conflict: bool):
        self.domain = domain
        self.mapper = ActionMapper(domain)
        self.require_conflict = require_conflict

    def _map_western(self, action: Dict[str, Any]) -> (str, bool):
        """
        Western conflict domain mapping (author-log style):
        1: snakebite (unintentional, act/3)
        2: move(Dest) (intentional, act/4)
        3: take(meds,carl)
        4: take(meds, Other)
        5: heal(Target, meds)
        """
        aid = action["actionId"]
        subj = action["subject"]
        params = action.get("parameters") or []
        txt = action.get("action", "")
        if aid == 1:
            return "snakebite", False
        if aid == 2:
            if not params:
                raise ValueError(f"move missing dest in action: {txt}")
            return f"move({params[0]})", True
        if aid == 3:
            return "take(meds,carl)", True
        if aid == 4:
            if not params:
                raise ValueError(f"take-from-other missing source in action: {txt}")
            return f"take(meds,{params[0]})", True
        if aid == 5:
            target = params[0] if params else subj
            return f"heal({target},meds)", True
        # fallback to mapper (should not normally happen)
        return self.mapper.to_asp_functor(aid, params), True

    def build(self, actions: List[Dict[str, Any]], maxstep: int = None) -> str:
        # maxstep const: T+1 where T is last timestep index; len(actions) fits that.
        max_const = len(actions) if maxstep is None else maxstep
        lines: List[str] = [f"#const maxstep={max_const}.", f"% Author-style constraints with maxstep={max_const}"]
        for t, action in enumerate(actions):
            subj = action["subject"]
            aid = action["actionId"]
            executed = action.get("executed", True)
            # domain-specific mapping
            if self.domain == "western":
                functor, intentional = self._map_western(action)
            else:
                functor = self.mapper.to_asp_functor(aid, action.get("parameters", []))
                intentional = True

            if executed:
                if intentional:
                    lines.append(f":- not act({subj}, {functor}, _, {t}).")
                else:
                    lines.append(f":- not act({subj}, {functor}, {t}).")
            else:
                if intentional:
                    lines.append(f":- not unexec_act({subj}, {functor}, _, {t}).")
                else:
                    lines.append(f":- not unexec_act({subj}, {functor}, {t}).")
        # conflict constraint only if enabled (default true for western)
        if self.require_conflict:
            lines.append(":- not conflict(_,_,_,_,_).")
        return "\n".join(lines)


class AuthorStylePlanParser:
    """
    Wrapper around the existing parsers: reuse domain-specific parsing/validation,
    but generate author-style constraints.
    """

    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path, require_conflict: bool = None):
        self.domain = domain
        self.inner = get_plan_parser(domain, domain_dir, instance_dir)
        # Conflict constraint only for western by default
        if require_conflict is None:
            require_conflict = domain == "western"
        self.builder = AuthorStyleConstraintBuilder(domain, require_conflict=require_conflict)

    def parse(self, llm_output: str) -> Dict[str, Any]:
        return self.inner.parse(llm_output)

    def build_constraints(self, actions: List[Dict[str, Any]], maxstep: int = 12) -> str:
        return self.builder.build(actions, maxstep=maxstep)
