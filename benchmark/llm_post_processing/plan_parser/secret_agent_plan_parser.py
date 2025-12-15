import json
import logging
from pathlib import Path

from benchmark.llm_post_processing.constraint_builder import SecretAgentConstraintBuilder

from .base_plan_parser import BasePlanParser


logger = logging.getLogger(__name__)


class SecretAgentPlanParser(BasePlanParser):
    """Secret agent plan parser and constraint builder."""

    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path):
        super().__init__(domain, domain_dir, instance_dir)
        self.builder = SecretAgentConstraintBuilder(self.mapper)

    def parse(self, llm_output: str) -> dict:
        result = {"raw_output": llm_output, "success": False}
        text = self.extract_json(llm_output)
        try:
            data = json.loads(text)
        except Exception as exc:
            result["error_type"] = "invalid_json"
            result["error_details"] = str(exc)
            return result

        if not isinstance(data, list):
            result["error_type"] = "invalid_json"
            result["error_details"] = "Top-level must be a list"
            result["partial_parse"] = data
            return result

        actions = []
        for index, item in enumerate(data):
            ok, parsed, error = self.parse_action(item)
            if not ok:
                result["error_type"] = "invalid_action"
                result["error_details"] = f"Action {index}: {error}"
                result["partial_parse"] = actions
                return result
            actions.append(parsed)

        result["success"] = True
        result["actions"] = actions
        return result

    def parse_action_id(self, value):
        if isinstance(value, int):
            mapping = {1: "move", 2: "move_through_guards", 3: "pickup", 4: "kill"}
            return mapping.get(value)
        if isinstance(value, str):
            raw = value.strip().lower()
            mapping = {
                "1": "move",
                "2": "move_through_guards",
                "3": "pickup",
                "4": "kill",
                "move": "move",
                "move_through_guards": "move_through_guards",
                "pickup": "pickup",
                "kill": "kill",
            }
            return mapping.get(raw)
        return None

    def parse_action(self, action: dict) -> tuple:
        if not isinstance(action, dict):
            return False, None, "Action must be object"
        for field in ["subject", "actionId", "parameters"]:
            if field not in action:
                return False, None, f"Missing {field}"

        originalSubject = action.get("subject")
        hasAgentToken = isinstance(originalSubject, str) and ("agent" in originalSubject.lower())
        if isinstance(originalSubject, str) and not hasAgentToken:
            logger.warning("Secret agent subject without 'agent' token: %s", originalSubject)

        actionId = self.parse_action_id(action.get("actionId"))
        if actionId is None:
            return False, None, f"Unknown actionId {action.get('actionId')}"
        arity = {"move": 1, "move_through_guards": 2, "pickup": 1, "kill": 2}[actionId]

        paramsValue = action.get("parameters")
        params = self.parse_parameters(actionId, paramsValue)
        params = self.fill_missing_params(actionId, params)
        if len(params) != arity:
            return False, None, f"Action {actionId} expects {arity} params, got {len(params)}"
        if not self.validate_param_values(actionId, params):
            return False, None, "Parameter value invalid"

        unknownSubject = False
        if isinstance(originalSubject, str):
            unknownSubject = (originalSubject not in self.valid_characters) and (not hasAgentToken)

        parsed = {
            "subject": "secret_agent",
            "original_subject": originalSubject,
            "actionId": actionId,
            "functor": actionId,
            "parameters": params,
            "executed": True,
            "original_executed": bool(action.get("executed", True)),
        }
        if unknownSubject:
            parsed["unknown_subject"] = True
        return True, parsed, ""

    def parse_parameters(self, actionId: str, value) -> list:
        if isinstance(value, list):
            return [self.normalize_name(v) for v in value]
        if isinstance(value, dict):
            if actionId == "move":
                return [self.normalize_name(value.get("location"))]
            if actionId == "move_through_guards":
                return [self.normalize_name(value.get("location")), self.normalize_name(value.get("dox", "dox"))]
            if actionId == "pickup":
                return [self.normalize_name(value.get("item"))]
            if actionId == "kill":
                return [self.normalize_name(value.get("target")), self.normalize_name(value.get("weapon", "gun"))]
        return []

    def fill_missing_params(self, actionId: str, params: list) -> list:
        paramsList = [p for p in params if p]
        if actionId == "kill" and len(paramsList) == 1:
            paramsList.append("gun")
        if actionId == "move_through_guards" and len(paramsList) == 1:
            paramsList.append("dox")
        return paramsList

    def validate_param_values(self, actionId: str, params: list) -> bool:
        if actionId in ("move", "move_through_guards"):
            return params[0] in self.valid_places
        if actionId == "pickup":
            item = params[0]
            if item == "gun":
                return True
            if isinstance(item, str) and item.startswith("dox"):
                return True
            return item in self.valid_objects
        if actionId == "kill":
            target = params[0]
            if target == "mastermind":
                return True
            return target in self.valid_characters
        return False

    def build_constraints(self, actions: list, maxstep: int = None) -> str:
        try:
            return self.builder.build(actions, maxstep=maxstep)
        except TypeError:
            return self.builder.build(actions)
