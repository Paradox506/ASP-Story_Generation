from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import json
import os

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
        output_dir: Path = Path("results"),
    ):
        self.base_dir = base_dir
        self.domain = domain
        self.asp_version = asp_version
        self.instance_dir = instance_dir
        self.model = model
        self.clingo_path = clingo_path
        self.maxstep = maxstep
        self.config_path = config_path
        self.output_dir = output_dir

        domain_dir = base_dir / domain / asp_version
        self.prompt_gen = PromptGenerator(domain, asp_version)
        self.parser = PlanParser(domain, domain_dir, instance_dir)
        self.validator = ASPValidator(domain, domain_dir, instance_dir, clingo_path=clingo_path)

    def run(self, response_text: Optional[str] = None) -> Dict:
        prompt = self.prompt_gen.load_prompt(self.base_dir, self.instance_dir)
        run_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        if response_text is None:
            api_key = load_api_key(self.config_path)
            client = OpenRouterClient(self.model, api_key=api_key)
            llm_result = client.generate(prompt)
            if not llm_result.get("success"):
                result = {
                    "stage": "llm",
                    "success": False,
                    "error": llm_result.get("error"),
                    "run_id": run_id,
                    "metadata": self._metadata(),
                    "llm_timing": llm_result,
                }
                self._persist_result(result, run_id, prompt, response_text=None, parse=None, asp=None)
                return result
            response_text = llm_result["content"]
            timing = llm_result
        else:
            timing = {"elapsed": None, "prompt_tokens": None, "completion_tokens": None}

        parse_result = self.parser.parse(response_text)
        if not parse_result.get("success"):
            result = {
                "stage": "parse",
                "success": False,
                "parse": parse_result,
                "llm_timing": timing,
                "run_id": run_id,
                "metadata": self._metadata(),
            }
            self._persist_result(result, run_id, prompt, response_text, parse_result, asp=None)
            return result

        asp_result = self.validator.validate_plan(parse_result["actions"], maxstep=self.maxstep)

        result = {
            "stage": "complete",
            "success": True,
            "prompt": prompt,
            "llm_timing": timing,
            "llm_raw": response_text,
            "parse": parse_result,
            "asp": asp_result,
            "run_id": run_id,
            "metadata": self._metadata(),
        }
        self._persist_result(result, run_id, prompt, response_text, parse_result, asp_result)
        return result

    def _metadata(self) -> Dict:
        return {
            "domain": self.domain,
            "asp_version": self.asp_version,
            "model": self.model,
            "instance": self.instance_dir.name,
            "maxstep": self.maxstep,
        }

    def _persist_result(
        self,
        result: Dict,
        run_id: str,
        prompt: Optional[str],
        llm_raw: Optional[str],
        parse: Optional[Dict],
        asp: Optional[Dict],
    ) -> None:
        """
        Save result JSON and a short log line. Directory layout:
        results/{domain}/{asp_version}/{model}/{instance}/{run_id}/result.json
        """
        instance_name = self.instance_dir.name
        dest_dir = (
            self.output_dir
            / run_id
            / self.domain
            / self.asp_version
            / self.model.replace("/", "_")
            / instance_name
        )
        os.makedirs(dest_dir, exist_ok=True)
        (dest_dir / "result.json").write_text(json.dumps(result, indent=2))
        (dest_dir / "prompt.txt").write_text(prompt or "")
        if llm_raw is not None:
            (dest_dir / "llm_raw.txt").write_text(llm_raw)
        if parse is not None:
            (dest_dir / "parse.json").write_text(json.dumps(parse, indent=2))
        if asp is not None:
            (dest_dir / "asp.json").write_text(json.dumps(asp, indent=2))

        log_path = self.output_dir / "benchmark.log"
        with open(log_path, "a") as f:
            timing = result.get("llm_timing", {}) or {}
            f.write(
                f"{run_id} domain={self.domain} asp={self.asp_version} model={self.model} "
                f"instance={instance_name} stage={result.get('stage')} success={result.get('success')} "
                f"elapsed={timing.get('elapsed')} prompt_tokens={timing.get('prompt_tokens')} "
                f"completion_tokens={timing.get('completion_tokens')}\n"
            )
