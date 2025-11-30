from typing import Dict, List
from pathlib import Path

from benchmark.llm_post_processing.constraint_builder import AladdinConstraintBuilder
from .base_plan_parser import BasePlanParser


class AladdinPlanParser(BasePlanParser):
    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path):
        super().__init__(domain, domain_dir, instance_dir)
        self.builder = AladdinConstraintBuilder(self.mapper)

    def load_symbols(self):
        super().load_symbols()
        # Also accept characters that appear as the first argument of role/2 in the instance constraints
        inst_path = self.instance_dir / "instance.lp"
        if inst_path.exists():
            try:
                import re

                pat = re.compile(r"role\(\s*([^\s,()]+)")
                for line in inst_path.read_text().splitlines():
                    m = pat.search(line)
                    if m:
                        self.valid_characters.add(m.group(1).strip())
            except Exception:
                pass

    def build_aliases(self) -> Dict[str, str]:
        aliases: Dict[str, str] = {}
        prefixes = ["king ", "princess ", "knight ", "dragon ", "lamp spirit "]
        for ch in self.valid_characters:
            for p in prefixes:
                aliases[p + ch] = ch
        return aliases

    def fill_params(self, aid: int, params: List[str], subj: str) -> List[str]:
        out = params[:]
        if aid == 1 and len(out) == 1:
            out.append(subj)
        if aid == 2 and len(out) == 1:
            out.append("lamp")
        if aid == 5 and len(out) == 1:
            out.append("lamp")
        if aid == 9 and len(out) == 1:
            out.insert(0, "alice")
        if aid == 10:
            if len(out) == 1:
                if out[0] in self.valid_characters:
                    out.append("lamp")
                    if out[0] != "alice":
                        out[0] = "alice"
                else:
                    out = ["alice", out[0]]
            elif len(out) == 0:
                out = ["alice", "lamp"]
        return out

    def validate_param_values(self, params: List[str]) -> bool:
        for p in params:
            if p in self.valid_characters or p in self.valid_objects or p in self.valid_places:
                continue
            return False
        return True

    def build_constraints(self, actions: List[Dict], maxstep: int = None) -> str:
        try:
            return self.builder.build(actions, maxstep=maxstep)
        except TypeError:
            return self.builder.build(actions)
