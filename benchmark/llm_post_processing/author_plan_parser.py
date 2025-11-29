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
        self.mapper = ActionMapper(domain)
        self.require_conflict = require_conflict

    def build(self, actions: List[Dict[str, Any]], maxstep: int = 12) -> str:
        max_const = maxstep + 1
        lines: List[str] = [f"#const maxstep={max_const}.", f"% Author-style constraints with maxstep={maxstep}"]
        for t, action in enumerate(actions):
            subj = action["subject"]
            aid = action["actionId"]
            params = action.get("parameters", [])
            functor = self.mapper.to_asp_functor(aid, params)
            executed = action.get("executed", True)
            if executed:
                lines.append(f":- not act({subj}, {functor}, _, {t}).")
            else:
                lines.append(f":- not unexec_act({subj}, {functor}, _, {t}).")
        # always require at least one conflict by default
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
