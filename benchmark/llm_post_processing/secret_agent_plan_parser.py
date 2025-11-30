import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set

from benchmark.asp.action_utils import ActionMapper


logger = logging.getLogger(__name__)


class SecretAgentPlanParser:
    """
    Secret Agent-specific parser and constraint builder.
    - Expects LLM JSON array with fields: subject, actionId, parameters, executed (bool).
    - Generates constraint-style ASP (:- not act/... or :- not unexec_act/...) with maxstep header.
    """

    # ActionId mapping: accept both string and integer ids
    ACTION_MAP: Dict[str, Tuple[str, int]] = {
        "move": ("move", 1),
        "move_through_guards": ("move_through_guards", 2),
        "pickup": ("pickup", 1),
        "kill": ("kill", 2),
        "1": ("move", 1),
        "2": ("move_through_guards", 2),
        "3": ("pickup", 1),
        "4": ("kill", 2),
    }

    def __init__(self, domain_dir: Path, instance_dir: Path):
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir
        self.mapper = ActionMapper("secret_agent")
        self.valid_characters: Set[str] = set()
        self.valid_locations: Set[str] = set()
        self.valid_items: Set[str] = set()
        self._load_symbols()

    # -------- symbol loading --------
    def _load_symbols(self) -> None:
        # pull characters/locations/items from instance/domain files
        files = [
            self.domain_dir / "constraints" / "domain.lp",
            self.instance_dir / "instance.lp",
            self.instance_dir / "instance_init.lp",
        ]
        for f in files:
            if not f.exists():
                continue
            txt = f.read_text()
            self.valid_characters |= set(self._extract_atoms(txt, "character"))
            self.valid_locations |= set(self._extract_atoms(txt, "place"))
            self.valid_items |= set(self._extract_atoms(txt, "object"))

    @staticmethod
    def _extract_atoms(text: str, pred: str) -> List[str]:
        import re

        pat = re.compile(rf"{pred}\(([^)]+)\)")
        return [m.group(1) for m in pat.finditer(text)]

    # -------- parsing --------
    def parse(self, llm_output: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {"raw_output": llm_output, "success": False}
        data = self._load_json_array(llm_output)
        if isinstance(data, dict):  # error payload
            result.update(data)
            return result

        actions: List[Dict[str, Any]] = []
        for idx, act in enumerate(data):
            ok, parsed, err = self._parse_action(act)
            if not ok:
                result["error_type"] = "invalid_action"
                result["error_details"] = f"Action {idx}: {err}"
                result["partial_parse"] = actions
                return result
            actions.append(parsed)
        result["success"] = True
        result["actions"] = actions
        return result

    def _parse_action(self, act: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        required = ["subject", "actionId", "parameters"]
        for f in required:
            if f not in act:
                return False, None, f"Missing field {f}"

        subject = act["subject"]
        subject_norm, has_agent_token, subject_known = self._normalize_and_check_subject(subject)

        aid_raw = str(act["actionId"])
        if aid_raw not in self.ACTION_MAP:
            return False, None, f"Unknown actionId {aid_raw}"
        functor, arity = self.ACTION_MAP[aid_raw]

        params_raw = act.get("parameters") or {}
        params_list = self._normalize_params(functor, params_raw)
        if len(params_list) != arity:
            return False, None, f"Action {functor} expects {arity} params, got {len(params_list)}"

        param_error = self._validate_params(functor, params_list)
        if param_error:
            return False, None, param_error

        parsed = {
            "subject": "secret_agent",
            "original_subject": subject,
            "actionId": aid_raw,
            "functor": functor,
            "parameters": params_list,
            "executed": bool(act.get("executed", True)),
        }
        if not subject_known:
            parsed["unknown_subject"] = True
        if not has_agent_token:
            logger.warning(
                "SecretAgentPlanParser: subject without 'agent' token encountered: %s", subject
            )
        return True, parsed, ""

    def _normalize_params(self, functor: str, params: Any) -> List[str]:
        if isinstance(params, list):
            if functor == "kill" and len(params) == 1:
                return [str(params[0]), "gun"]
            return [str(p) for p in params]
        if not isinstance(params, dict):
            return []
        if functor == "move":
            return [str(params.get("location", ""))] if "location" in params else []
        if functor == "move_through_guards":
            loc = params.get("location")
            dox = params.get("dox", "dox")
            if loc is None:
                return []
            return [str(loc)] if dox is None else [str(loc), str(dox)]
        if functor == "pickup":
            return [str(params.get("item", ""))] if "item" in params else []
        if functor == "kill":
            target = params.get("target")
            if target is None:
                return []
            weapon = params.get("weapon", "gun")
            return [str(target), str(weapon)]
        return []

    def _validate_params(self, functor: str, params: List[str]) -> Optional[str]:
        if functor in ("move", "move_through_guards"):
            if params[0] not in self.valid_locations:
                return f"Unknown location {params[0]}"
        if functor == "kill":
            if params and (params[0] not in self.valid_characters and params[0] != "mastermind"):
                return f"Unknown target {params[0]}"
        if functor == "pickup":
            item = params[0]
            if item not in self.valid_items and not (item == "gun" or item.startswith("dox")):
                return f"Unknown item {params[0]}"
        return None

    def _normalize_and_check_subject(self, subject: Any) -> Tuple[Any, bool, bool]:
        subject_norm = self._normalize_subject(subject)
        has_agent_token = isinstance(subject, str) and ("agent" in subject.lower())
        subject_known = subject_norm in self.valid_characters or has_agent_token
        return subject_norm, has_agent_token, subject_known

    def _normalize_subject(self, subject: Any) -> Any:
        if not isinstance(subject, str):
            return subject
        name = subject.strip()
        return "secret_agent" if "agent" in name.lower() else name

    def _load_json_array(self, text: str) -> Any:
        try:
            data = json.loads(text)
        except Exception as e:
            return {"error_type": "invalid_json", "error_details": str(e)}
        if not isinstance(data, list):
            return {"error_type": "invalid_json", "error_details": "Expected a list of actions"}
        return data

    # -------- constraints --------
    def build_constraints(self, actions: List[Dict[str, Any]], maxstep: Optional[int] = None) -> str:
        max_const = maxstep or (len(actions) + 1)
        lines: List[str] = [f"#const maxstep={max_const}.", "% Secret Agent plan constraints"]
        for t, act in enumerate(actions):
            subj = act["subject"]
            functor = self._to_functor(act)
            executed = act.get("executed", True)
            if executed:
                lines.append(f":- not act({subj}, {functor}, {t}).")
            else:
                lines.append(f":- not unexec_act({subj}, {functor}, {t}).")
        return "\n".join(lines) + "\n"

    def _to_functor(self, act: Dict[str, Any]) -> str:
        functor = act["functor"]
        params = act["parameters"]
        if functor in ("move", "pickup") and len(params) == 1:
            return f"{functor}({params[0]})"
        if functor == "kill" and len(params) >= 2:
            return f"{functor}({params[0]},{params[1]})"
        if functor == "move_through_guards" and len(params) >= 2:
            return f"{functor}({params[0]},{params[1]})"
        # fallback
        return self.mapper.to_asp_functor(int(act["actionId"]) if act["actionId"].isdigit() else 0, params)
