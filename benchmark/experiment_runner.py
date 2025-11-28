from pathlib import Path
from typing import Dict, Optional

from .asp_validator import ASPValidator
from .openrouter_client import OpenRouterClient
from .plan_parser import PlanParser
from .prompt_generator import PromptGenerator
from .config import load_api_key


class ExperimentRunner:
    """
    Minimal one-off runner for a single domain/instance/model.
    """

    def __init__(
        self,
        base_dir: Path,
        domain: str,
        asp_version: str,
        instance_dir: Path,
        model: str,
        clingo_path: str = "clingo",
        maxstep: int = 12,
        config_path: Optional[Path] = None,
    ):
        self.base_dir = base_dir
        self.domain = domain
        self.asp_version = asp_version
        self.instance_dir = instance_dir
        self.model = model
        self.clingo_path = clingo_path
        self.maxstep = maxstep
        self.config_path = config_path

        domain_dir = base_dir / domain / asp_version
        self.prompt_gen = PromptGenerator(domain, asp_version)
        self.parser = PlanParser(domain, domain_dir, instance_dir)
        self.validator = ASPValidator(domain, domain_dir, instance_dir, clingo_path=clingo_path)

    def run(self, response_text: Optional[str] = None) -> Dict:
        prompt = self.prompt_gen.load_prompt(self.base_dir, self.instance_dir)
        if response_text is None:
            api_key = load_api_key(self.config_path)
            client = OpenRouterClient(self.model, api_key=api_key)
            llm_result = client.generate(prompt)
            if not llm_result.get("success"):
                return {"stage": "llm", "success": False, "error": llm_result.get("error")}
            response_text = llm_result["content"]
            timing = llm_result
        else:
            timing = {"elapsed": None}

        parse_result = self.parser.parse(response_text)
        if not parse_result.get("success"):
            return {"stage": "parse", "success": False, "parse": parse_result, "llm_timing": timing}

        asp_result = self.validator.validate_plan(parse_result["actions"], maxstep=self.maxstep)

        return {
            "stage": "complete",
            "success": True,
            "prompt": prompt,
            "llm_timing": timing,
            "llm_raw": response_text,
            "parse": parse_result,
            "asp": asp_result,
        }
