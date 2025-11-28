import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from .action_utils import ActionMapper, extract_intention


class ConstraintBuilder:
    def __init__(self, mapper: ActionMapper):
        self.mapper = mapper

    def build(self, actions: List[Dict]) -> str:
        raise NotImplementedError


class AladdinConstraintBuilder(ConstraintBuilder):
    def __init__(self, mapper: ActionMapper):
        super().__init__(mapper)
        # Unintentional actions are encoded as act/3 in the ASP (no intention argument)
        self.unintentional_ids = {0, 7, 8}

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
            else:
                intention = extract_intention(action.get("character_plan", "")) or self._default_intention(aid, params, subj)
                lines.append(f"act({subj}, {functor}, {intention}, {i}).")
        return "\n".join(lines)


class WesternConstraintBuilder(ConstraintBuilder):
    def build(self, actions: List[Dict]) -> str:
        lines: List[str] = []
        for i, action in enumerate(actions):
            subj = action["subject"]
            aid = action["actionId"]
            params = action.get("parameters", [])
            functor = self.mapper.to_asp_functor(aid, params)
            lines.append(f":- not act({subj}, {functor}, {i}).")
            executed_flag = action.get("executed", True)
            if executed_flag:
                lines.append(f":- not executed({subj}, {functor}, {i}).")
            else:
                lines.append(f":- executed({subj}, {functor}, {i}).")
        return "\n".join(lines)


class SecretAgentConstraintBuilder(ConstraintBuilder):
    def build(self, actions: List[Dict]) -> str:
        lines: List[str] = []
        for i, action in enumerate(actions):
            subj = action["subject"]
            aid = action["actionId"]
            params = action.get("parameters", [])
            functor = self.mapper.to_asp_functor(aid, params)
            lines.append(f":- not act({subj}, {functor}, {i}).")
        return "\n".join(lines)


def get_constraint_builder(domain: str, mapper: ActionMapper) -> ConstraintBuilder:
    if domain == "aladdin":
        return AladdinConstraintBuilder(mapper)
    if domain == "western":
        return WesternConstraintBuilder(mapper)
    if domain == "secret_agent":
        return SecretAgentConstraintBuilder(mapper)
    raise ValueError(f"Unsupported domain {domain}")


class BasePlanParser:
    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path):
        self.domain = domain
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir
        self.mapper = ActionMapper(domain)
        self.builder = get_constraint_builder(domain, self.mapper)
        self.aliases: Dict[str, str] = {}
        self.valid_characters: Set[str] = set()
        self.valid_places: Set[str] = set()
        self.valid_objects: Set[str] = set()
        self.load_symbols()

    def load_symbols(self):
        def extract_atoms(path: Path, predicate: str) -> Set[str]:
            atoms: Set[str] = set()
            if not path.exists():
                return atoms
            pattern = re.compile(rf"{predicate}\(\s*([^)]+?)\s*\)\s*\.")
            for line in path.read_text().splitlines():
                m = pattern.search(line)
                if m:
                    for chunk in m.group(1).split(";"):
                        atoms.add(chunk.strip())
            return atoms

        for path in [
            self.domain_dir / "domain.lp",
            self.instance_dir / "instance.lp",
            self.instance_dir / "init.lp",
            self.instance_dir / "instance_init.lp",
        ]:
            self.valid_characters |= extract_atoms(path, "character")
            self.valid_places |= extract_atoms(path, "place") or extract_atoms(path, "location")
            self.valid_objects |= extract_atoms(path, "object")
        # allow domain-specific alias setup
        self.aliases.update(self.build_aliases())

    def build_aliases(self) -> Dict[str, str]:
        return {}

    def normalize_name(self, name: str) -> str:
        if not isinstance(name, str):
            return name
        raw = name.strip()
        lowered = raw.lower()
        if lowered in self.aliases:
            return self.aliases[lowered]
        return lowered

    def fill_params(self, aid: int, params: List[str], subj: str) -> List[str]:
        return params

    def validate_param_values(self, params: List[str]) -> bool:
        return True

    def build_constraints(self, actions: List[Dict]) -> str:
        return ""

    def parse(self, llm_output: str) -> Dict:
        result: Dict = {"raw_output": llm_output, "success": False}
        json_str = self.extract_json(llm_output)
        try:
            data = json.loads(json_str)
        except Exception as e:
            result["error_type"] = "invalid_json"
            result["error_details"] = str(e)
            return result

        if not isinstance(data, list):
            result["error_type"] = "invalid_json"
            result["error_details"] = "Top-level must be a list"
            result["partial_parse"] = data
            return result

        actions: List[Dict] = []
        for idx, item in enumerate(data):
            validation = self.validate_action(item)
            if validation is not True:
                result["error_type"] = validation["error_type"]
                result["error_details"] = f"Action {idx}: {validation['message']}"
                result["partial_parse"] = actions
                return result
            actions.append(item)

        result["success"] = True
        result["actions"] = actions
        return result

    def extract_json(self, text: str) -> str:
        try:
            json.loads(text)
            return text
        except Exception:
            pass
        m = re.search(r"```json\s*(\[.*?\])\s*```", text, re.S | re.I)
        if m:
            return m.group(1)
        m = re.search(r"(\[.*\])", text, re.S)
        if m:
            return m.group(1)
        return text

    def validate_action(self, action: Dict):
        if not isinstance(action, dict):
            return {"error_type": "invalid_json", "message": "Action must be object"}
        required = ["subject", "actionId", "parameters"]
        for f in required:
            if f not in action:
                return {"error_type": "missing_required_field", "message": f"Missing {f}"}
        subj = self.normalize_name(action["subject"])
        if self.valid_characters and subj not in self.valid_characters:
            return {"error_type": "invalid_character", "message": f"Unknown {subj}"}
        # persist normalized subject
        action["subject"] = subj
        aid_raw = action["actionId"]
        try:
            aid = int(aid_raw)
            action["actionId"] = aid
        except Exception:
            return {"error_type": "invalid_action_id", "message": f"Invalid actionId {aid_raw}"}
        if not self.mapper.has_action(aid):
            return {"error_type": "invalid_action_id", "message": f"Invalid id {aid}"}
        params = action.get("parameters", [])
        if not isinstance(params, list):
            return {"error_type": "invalid_parameters", "message": "Parameters must be list"}
        schema = self.mapper.schema(aid)
        if len(params) < schema.arity:
            filled = self.fill_params(aid, params, subj)
            if filled != params:
                action["parameters"] = filled
                action["filled_params"] = True
            params = filled
        if len(params) != schema.arity:
            return {
                "error_type": "invalid_parameters",
                "message": f"Expected {schema.arity} params, got {len(params)}",
            }
        normalized = [self.normalize_name(p) for p in params]
        if not self.validate_param_values(normalized):
            return {"error_type": "invalid_parameters", "message": "Parameter value invalid"}
        action["parameters"] = normalized
        return True


class AladdinPlanParser(BasePlanParser):
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

    def build_constraints(self, actions: List[Dict]) -> str:
        return self.builder.build(actions)


class SecretAgentPlanParser(BasePlanParser):
    def validate_param_values(self, params: List[str]) -> bool:
        for p in params:
            if p in self.valid_characters or p in self.valid_objects or p in self.valid_places:
                continue
            return False
        return True

    def build_constraints(self, actions: List[Dict]) -> str:
        return self.builder.build(actions)


class WesternPlanParser(BasePlanParser):
    def validate_param_values(self, params: List[str]) -> bool:
        for p in params:
            if p in self.valid_characters or p in self.valid_places:
                continue
            return False
        return True

    def build_constraints(self, actions: List[Dict]) -> str:
        return self.builder.build(actions)


def get_plan_parser(domain: str, domain_dir: Path, instance_dir: Path) -> BasePlanParser:
    if domain == "aladdin":
        return AladdinPlanParser(domain, domain_dir, instance_dir)
    if domain == "secret_agent":
        return SecretAgentPlanParser(domain, domain_dir, instance_dir)
    if domain == "western":
        return WesternPlanParser(domain, domain_dir, instance_dir)
    raise ValueError(f"Unsupported domain {domain}")
