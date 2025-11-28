import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from .utils import ActionMapper


class BasePlanParser:
    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path):
        self.domain = domain
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir
        self.mapper = ActionMapper(domain)
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
        aid_raw = action["actionId"]
        try:
            aid = int(aid_raw)
            action["actionId"] = aid
        except Exception:
            return {"error_type": "invalid_action_id", "message": f"Invalid actionId {aid_raw}"}
        if aid not in self.mapper._schemas:
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
        if not self.validate_param_values(params):
            return {"error_type": "invalid_parameters", "message": "Parameter value invalid"}
        # normalize params
        normalized = [self.normalize_name(p) for p in params]
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


class SecretAgentPlanParser(BasePlanParser):
    def validate_param_values(self, params: List[str]) -> bool:
        for p in params:
            if p in self.valid_characters or p in self.valid_objects or p in self.valid_places:
                continue
            return False
        return True


class WesternPlanParser(BasePlanParser):
    def validate_param_values(self, params: List[str]) -> bool:
        for p in params:
            if p in self.valid_characters or p in self.valid_places:
                continue
            return False
        return True


def get_plan_parser(domain: str, domain_dir: Path, instance_dir: Path) -> BasePlanParser:
    if domain == "aladdin":
        return AladdinPlanParser(domain, domain_dir, instance_dir)
    if domain == "secret_agent":
        return SecretAgentPlanParser(domain, domain_dir, instance_dir)
    if domain == "western":
        return WesternPlanParser(domain, domain_dir, instance_dir)
    raise ValueError(f"Unsupported domain {domain}")
