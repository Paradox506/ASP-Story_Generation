from pathlib import Path
from typing import Dict, List

from benchmark.llm_post_processing.constraint_builder import WesternConstraintBuilder
from .base_plan_parser import BasePlanParser


class WesternPlanParser(BasePlanParser):
    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path):
        super().__init__(domain, domain_dir, instance_dir)
        self.builder = WesternConstraintBuilder(self.mapper)

    def load_symbols(self):
        super().load_symbols()
        # additionally parse map locations from domains-based western prompts if available
        try:
            map_path = self.domain_dir / "prompts" / "2map.txt"
            if map_path.exists():
                import re

                locs = set()
                for line in map_path.read_text().splitlines():
                    for m in re.finditer(r"location\s+([A-Za-z0-9_]+)", line):
                        locs.add(m.group(1))
                self.valid_places |= locs
        except Exception:
            pass
        # also pull characters explicitly declared in instance.lp via character/1
        inst_path = self.instance_dir / "instance.lp"
        if inst_path.exists():
            try:
                pattern = re.compile(r"character\(\s*([^)]+?)\s*\)\s*\.")
                for line in inst_path.read_text().splitlines():
                    m = pattern.search(line)
                    if m:
                        for chunk in m.group(1).split(";"):
                            self.valid_characters.add(chunk.strip())
            except Exception:
                pass

    def fill_params(self, aid: int, params: List[str], subj: str) -> List[str]:
        out = params[:]
        # Action 3: take from merchant carl (expects Obj, Ch)
        if aid == 3:
            if len(out) == 0:
                out = ["meds", "carl"]
            elif len(out) == 1:
                # if only object provided, append carl; if only character provided, prepend meds
                if out[0] == "carl" or out[0] in self.valid_objects:
                    out.append("carl")
                else:
                    out = ["meds", out[0]]
        # Action 4: take from another character (expects Obj, Ch!=carl)
        if aid == 4:
            if len(out) == 0:
                out = ["meds", subj]  # default other character as subject? fallback
            elif len(out) == 1:
                # treat the single param as character, prepend meds
                out = ["meds", out[0]]
        # Action 5: heal(Target, Item) - if item missing, default to meds
        if aid == 5 and len(out) == 1:
            out.append("meds")
        return out

    def validate_param_values(self, params: List[str]) -> bool:
        for p in params:
            if p in self.valid_characters or p in self.valid_places or p in self.valid_objects:
                continue
            return False
        return True

    def normalize_intention(self, intention: str, subj: str) -> str:
        """Map free-form intention to a valid western intention."""
        if not intention:
            return ""
        intent = intention.strip().lower()
        # allow formats like "alive(agent_0)" / "dead(agent_1)" / "possessed_by(meds,agent_1)"
        def _wrap(name: str) -> str:
            return name.strip()

        # direct passthrough if already valid
        if intent.startswith("alive(") or intent.startswith("dead(") or intent.startswith("possessed_by("):
            return intent
        # loose matches
        for ch in self.valid_characters:
            if ch in intent:
                if "dead" in intent:
                    return f"dead({ch})"
                if "alive" in intent:
                    return f"alive({ch})"
        if "possess" in intent or "med" in intent:
            return f"possessed_by(meds,{subj})"
        return ""

    def build_constraints(self, actions: List[Dict], maxstep: int = None) -> str:
        # normalize intentions on actions to ensure they are valid
        for act in actions:
            raw_intent = act.get("intention") or ""
            act["normalized_intention"] = self.normalize_intention(raw_intent, act.get("subject", ""))
        try:
            return self.builder.build(actions, maxstep=maxstep)
        except TypeError:
            return self.builder.build(actions)
