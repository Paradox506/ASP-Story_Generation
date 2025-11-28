import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from .utils import ActionMapper

# Static helper for CLI/standalone use
def parse_plan(domain: str, domain_dir: Path, instance_dir: Path, llm_output: str) -> Dict:
    """
    Convenience wrapper to parse an LLM output without instantiating ExperimentRunner.
    """
    parser = PlanParser(domain, domain_dir, instance_dir)
    return parser.parse(llm_output)


def _extract_atoms(path: Path, predicate: str) -> Set[str]:
    """
    Very lightweight ASP fact extractor: scans for predicate(args).
    Only supports ground facts; ignores rules.
    """
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


class PlanParser:
    """
    Parses and validates LLM output under the original paper prompts.
    Uses permissive JSON extraction (plain text -> json.loads -> regex fallback).
    """

    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path):
        self.domain = domain
        self.mapper = ActionMapper(domain)
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir
        self.valid_characters = self._load_symbols("character")
        self.valid_places = (
            self._load_symbols("place") or self._load_symbols("location")
        )
        self.valid_objects = self._load_symbols("object")
        self.aliases = self._build_aliases()

    def _build_aliases(self) -> Dict[str, str]:
        """
        Domain-specific alias map to tolerate descriptive prefixes from LLM outputs.
        Currently only used for Aladdin to strip role descriptors.
        """
        aliases: Dict[str, str] = {}
        if self.domain == "aladdin":
            prefixes = ["king ", "princess ", "knight ", "dragon ", "lamp spirit "]
            all_chars = self.valid_characters
            for ch in all_chars:
                for p in prefixes:
                    aliases[p + ch] = ch
        return aliases

    def _load_symbols(self, predicate: str) -> Set[str]:
        # Combine domain facts and instance facts
        symbols = set()
        for path in [
            self.domain_dir / "domain.lp",
            self.instance_dir / "instance.lp",
            self.instance_dir / "init.lp",
            self.instance_dir / "instance_init.lp",
        ]:
            symbols |= _extract_atoms(path, predicate)
        return symbols

    def parse(self, llm_output: str) -> Dict:
        result: Dict = {"raw_output": llm_output, "success": False}
        json_str = self._extract_json(llm_output)
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
            validation = self._validate_action(item)
            if validation is not True:
                result["error_type"] = validation["error_type"]
                result["error_details"] = f"Action {idx}: {validation['message']}"
                result["partial_parse"] = actions
                return result
            actions.append(item)

        result["success"] = True
        result["actions"] = actions
        return result

    def _validate_action(self, action: Dict):
        if not isinstance(action, dict):
            return {"error_type": "invalid_json", "message": "Action must be object"}
        required = ["subject", "actionId", "parameters"]
        if self.domain == "aladdin":
            aid = action.get("actionId")
            if aid not in (0, 7, 8):
                required.append("character_plan")
        for f in required:
            if f not in action:
                return {"error_type": "missing_required_field", "message": f"Missing {f}"}
        # subject
        subj = self._normalize_name(action["subject"])
        if self.valid_characters and subj not in self.valid_characters:
            return {"error_type": "invalid_character", "message": f"Unknown {subj}"}
        # actionId
        aid_raw = action["actionId"]
        try:
            aid = int(aid_raw)
            action["actionId"] = aid
        except Exception:
            return {"error_type": "invalid_action_id", "message": f"Invalid actionId {aid_raw}"}
        if aid not in self.mapper._schemas:
            return {"error_type": "invalid_action_id", "message": f"Invalid id {aid}"}
        # parameters
        params = action.get("parameters", [])
        if not isinstance(params, list):
            return {"error_type": "invalid_parameters", "message": "Parameters must be list"}
        schema = self.mapper.schema(aid)
        # Attempt domain-specific completion for Aladdin
        if self.domain == "aladdin" and len(params) < schema.arity:
            filled = self._maybe_fill_aladdin_params(aid, params, subj)
            if filled != params:
                action["_filled_params"] = True
            params = filled
            action["parameters"] = params
        if len(params) != schema.arity:
            return {
                "error_type": "invalid_parameters",
                "message": f"Expected {schema.arity} params, got {len(params)}",
            }
        # value checks
        if self.domain in ("aladdin", "secret_agent"):
            norm_params = [self._normalize_name(p) for p in params]
            action["parameters"] = norm_params
            for p in norm_params:
                if p in self.valid_characters or p in self.valid_objects or p in self.valid_places:
                    continue
        if self.domain == "western":
            norm_params = [self._normalize_name(p) for p in params]
            action["parameters"] = norm_params
            for p in norm_params:
                if p in self.valid_characters or p in self.valid_places:
                    continue
        return True

    def _normalize_name(self, name: str) -> str:
        """
        Normalize entity names by lowering, stripping, and applying alias map.
        """
        if not isinstance(name, str):
            return name
        raw = name.strip()
        lowered = raw.lower()
        if lowered in self.aliases:
            return self.aliases[lowered]
        return lowered

    def _maybe_fill_aladdin_params(self, aid: int, params: List[str], subj: str) -> List[str]:
        """
        Apply conservative default-filling for known arity=2 actions.
        """
        out = params[:]
        # cast_love_spell: target, lover -> if only target, assume lover=subj
        if aid == 1 and len(out) == 1:
            out.append(subj)
        # pillage: body, obj -> lamp is the only obj
        if aid == 2 and len(out) == 1:
            out.append("lamp")
        # give: givee, obj -> lamp unique
        if aid == 5 and len(out) == 1:
            out.append("lamp")
        # order_to_kill: knight, victim -> alice unique knight
        if aid == 9 and len(out) == 1:
            out.insert(0, "alice")
        # order_to_obtain: knight, obj -> alice unique knight, lamp unique object
        if aid == 10:
            if len(out) == 1:
                # if param looks like knight, prepend lamp; else assume knight=alice
                if out[0] in self.valid_characters:
                    out.append("lamp")
                    if out[0] != "alice":
                        out[0] = "alice"
                else:
                    out = ["alice", out[0]]
            elif len(out) == 0:
                out = ["alice", "lamp"]
        return out

    def _extract_json(self, text: str) -> str:
        # Try direct
        try:
            json.loads(text)
            return text
        except Exception:
            pass
        # Code block with json
        m = re.search(r"```json\s*(\[.*?\])\s*```", text, re.S | re.I)
        if m:
            return m.group(1)
        # First bracketed list
        m = re.search(r"(\[.*\])", text, re.S)
        if m:
            return m.group(1)
        return text
