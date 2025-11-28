from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os

from benchmark.asp.validator import ASPValidator
from benchmark.llm_clients.openrouter_client import OpenRouterClient
from benchmark.llm_post_processing.plan_parser import get_plan_parser
from benchmark.prompts.prompt_builder import get_prompt_builder
from benchmark.config.config_utils import load_api_key
from benchmark.io.artifact_writer import ArtifactWriter
from benchmark.config.config_loader import ExperimentConfig, LlmConfig


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
        provider: str = "openrouter",
        clingo_path: str = "clingo",
        maxstep: int = 12,
        config_path: Optional[Path] = None,
        output_dir: Path = Path("results"),
        run_id_override: Optional[str] = None,
        max_tokens: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        exp_cfg: Optional[ExperimentConfig] = None,
        llm_cfg: Optional[LlmConfig] = None,
    ):
        self.base_dir = base_dir
        self.domain = domain
        self.asp_version = asp_version
        self.instance_dir = instance_dir
        self.model = model
        self.provider = provider
        self.clingo_path = clingo_path
        self.maxstep = maxstep
        self.config_path = config_path
        self.output_dir = output_dir
        self.run_id_override = run_id_override
        self.max_tokens = max_tokens
        self.max_output_tokens = max_output_tokens
        self.exp_cfg = exp_cfg
        self.llm_cfg = llm_cfg

        domain_dir = base_dir / domain / asp_version
        self.writer = ArtifactWriter(
            output_dir,
            domain,
            asp_version,
            model,
            instance_dir.name,
        )
        self.prompt_gen = get_prompt_builder(domain, asp_version)
        self.parser = get_plan_parser(domain, domain_dir, instance_dir)
        self.validator = ASPValidator(domain, domain_dir, instance_dir, clingo_path=clingo_path)
        self.evaluator = None
        if domain == "secret_agent":
            try:
                from benchmark.evaluators.causal_evaluator import CausalEvaluator

                self.evaluator = CausalEvaluator()
            except Exception:
                self.evaluator = None
        elif domain == "western":
            try:
                from benchmark.evaluators.conflict_evaluator import ConflictEvaluator

                self.evaluator = ConflictEvaluator()
            except Exception:
                self.evaluator = None
        elif domain == "aladdin":
            try:
                from benchmark.evaluators.intentionality_evaluator import IntentionalityEvaluator

                self.evaluator = IntentionalityEvaluator()
            except Exception:
                self.evaluator = None

    def run(self, response_text: Optional[str] = None, run_seq: int = 0) -> Dict:
        offline = response_text is not None
        prompt = self.prompt_gen.load_prompt(self.base_dir, self.instance_dir)
        base_id = self.run_id_override or datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d_%H-%M-%S_%Z")
        if offline:
            base_id = f"{base_id}_offline"
        run_id = f"{base_id}/run_{run_seq:04d}"
        if response_text is None:
            api_key = load_api_key(self.config_path, provider=self.provider)
            client = self._make_client(api_key)
            llm_result = client.generate(prompt)
            if not llm_result.get("success"):
                result = {
                    "stage": "llm",
                    "success": False,
                    "error": llm_result.get("error"),
                    "run_id": run_id,
                    "metadata": self._metadata(),
                    "llm_timing": llm_result,
                    "llm_raw": llm_result.get("content", "") or llm_result.get("error", ""),
                }
                self._persist_result(result, run_id, prompt, llm_raw=None, parse=None, asp=None)
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
                "offline": offline,
            }
            self._persist_result(result, run_id, prompt, response_text, parse_result, asp=None)
            return result

        constraints_text = self.parser.build_constraints(parse_result["actions"])
        # persist constraints early so we can reuse the file for clingo input
        constraints_path = self.writer.ensure_dir(run_id) / f"{self.domain}_NarrPlan.lp"
        constraints_path.write_text(constraints_text)
        asp_result = self.validator.validate_plan(
            parse_result["actions"],
            maxstep=self.maxstep,
            constraints_text=constraints_text,
            constraints_path=str(constraints_path),
        )

        evaluation = None
        if self.evaluator:
            expected_conflicts = 0
            if self.domain == "western":
                expected_conflicts = self._expected_conflicts()
                evaluation = self.evaluator.evaluate(asp_result, parse_result, expected_conflicts=expected_conflicts)
            else:
                evaluation = self.evaluator.evaluate(asp_result, parse_result)

        result = {
            "stage": "complete",
            "success": True,
            "prompt": prompt,
            "llm_timing": timing,
            "llm_raw": response_text,
            "parse": parse_result,
            "asp": asp_result,
            "clingo_stdout": self.validator.last_stdout if hasattr(self.validator, "last_stdout") else None,
            "run_id": run_id,
            "metadata": self._metadata(),
            "offline": offline,
            "offline": offline,
            "evaluation": evaluation,
        }
        self._persist_result(
            result,
            run_id,
            prompt,
            llm_raw=response_text,
            parse=parse_result,
            asp=asp_result,
            raw_clingo=self.validator.last_stdout if hasattr(self.validator, "last_stdout") else None,
            constraints=constraints_text,
        )
        return result

    def _make_client(self, api_key: Optional[str]):
        if self.provider == "openrouter":
            from benchmark.llm_clients.openrouter_client import OpenRouterClient

            return OpenRouterClient(
                self.model,
                api_key=api_key,
                max_tokens=self.max_tokens,
                max_output_tokens=self.max_output_tokens,
            )
        if self.provider == "openai":
            from benchmark.llm_clients.openai_client import OpenAIClient

            return OpenAIClient(
                self.model,
                api_key=api_key,
                max_tokens=self.max_tokens,
                max_output_tokens=self.max_output_tokens,
            )
        if self.provider == "anthropic":
            from benchmark.llm_clients.anthropic_client import AnthropicClient

            return AnthropicClient()
        raise ValueError(f"Unsupported provider {self.provider}")

    def _metadata(self) -> Dict:
        return {
            "domain": self.domain,
            "asp_version": self.asp_version,
            "model": self.model,
            "instance": self.instance_dir.name,
            "maxstep": self.maxstep,
        }

    def _expected_conflicts(self) -> int:
        # Placeholder: could read from config/goal if available
        return 0

    def _persist_result(
        self,
        result: Dict,
        run_id: str,
        prompt: Optional[str],
        llm_raw: Optional[str],
        parse: Optional[Dict],
        asp: Optional[Dict],
        raw_clingo: Optional[str] = None,
        constraints: Optional[str] = None,
    ) -> None:
        self.writer.write(run_id, result, prompt, llm_raw, parse, asp, raw_clingo=raw_clingo, constraints=constraints)
        self.writer.append_log(run_id, result)
