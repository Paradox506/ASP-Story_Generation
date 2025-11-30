from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os

from benchmark.asp.validator import ASPValidator
from benchmark.llm_clients.openrouter_client import OpenRouterClient
from benchmark.llm_post_processing.plan_parser import get_plan_parser
from benchmark.prompt_builders.prompt_builder import get_prompt_builder
from benchmark.config.config_utils import load_api_key
from benchmark.io.artifact_writer import ArtifactWriter
from benchmark.config.config_loader import ExperimentConfig, LlmConfig
import shutil
import os


class ExperimentRunner:
    """
    Minimal one-off runner for a single domain/instance/model.
    """

    def __init__(
        self,
        base_dir: Path,
        domains_root: Path,
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
        use_author_style: bool = False,
        response_file_dir: Optional[Path] = None,
        instance_label_override: Optional[str] = None,
    ):
        self.base_dir = base_dir
        self.domains_root = domains_root
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
        self.response_file_dir = response_file_dir
        # choose instance label: prefer override (e.g., response file subpath); otherwise infer
        if instance_label_override:
            self.instance_label = instance_label_override
        elif "instances" in set(instance_dir.parts):
            parts = instance_dir.parts
            self.instance_label = f"{parts[-2]}/{parts[-1]}"
        else:
            self.instance_label = instance_dir.name

        domain_dir = domains_root / domain / asp_version
        self.writer = ArtifactWriter(
            output_dir,
            domain,
            asp_version,
            model,
            self.instance_label,
        )
        self.prompt_gen = get_prompt_builder(domain, asp_version)
        self.parser = get_plan_parser(domain, domain_dir, instance_dir, use_author_style=use_author_style)
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
        prompt = self.prompt_gen.build_prompt(self.domains_root, self.instance_dir)
        base_id = self.run_id_override or datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d_%H-%M-%S_%Z")
        if offline:
            base_id = f"{base_id}_response_file"
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
                self.copy_support_files(run_id)
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
            self.copy_support_files(run_id)
            return result

        # determine maxstep: use configured value if provided, otherwise len(actions)+1
        effective_maxstep = self.maxstep or (len(parse_result["actions"]) + 1)

        try:
            constraints_text = self.parser.build_constraints(parse_result["actions"], maxstep=effective_maxstep)
            # persist constraints early so we can reuse the file for clingo input
            constraints_path = self.writer.ensure_dir(run_id) / f"{self.domain}_NarrPlan.lp"
            constraints_path.write_text(constraints_text)
            asp_result = self.validator.validate_plan(
                parse_result["actions"],
                maxstep=effective_maxstep,
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
            self.copy_support_files(run_id)
            return result
        except Exception as e:
            error_result = {
                "stage": "error",
                "success": False,
                "error": str(e),
                "run_id": run_id,
                "metadata": self._metadata(),
                "prompt": prompt,
                "llm_raw": response_text,
                "parse": parse_result,
                "offline": offline,
                "llm_timing": timing,
            }
            self._persist_result(
                error_result,
                run_id,
                prompt,
                llm_raw=response_text,
                parse=parse_result,
                asp=None,
                raw_clingo=None,
                constraints=None,
            )
            # still try to copy support files for debugging
            try:
                self.copy_support_files(run_id)
            except Exception:
                pass
            return error_result

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
            "instance": self.instance_label,
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

    def copy_support_files(self, run_id: str) -> None:
        """
        Copy ASP inputs into run directory:
        - Domain-level constraints -> domain_constraints/
        - Instance-level constraints -> instance_constraints/ (skipped when asp_version is base)
        - Instance extras (matrix.txt/loyalty.txt/intro.txt) -> run root
        """
        dest_dir = self.writer.ensure_dir(run_id)
        domain_dir = dest_dir / "domain_constraints"
        domain_dir.mkdir(parents=True, exist_ok=True)
        instance_dir = dest_dir / "instance_constraints"
        instance_dir.mkdir(parents=True, exist_ok=True)
        domain_root_dir = (self.domains_root / self.domain / self.asp_version).resolve()
        inst_root_dir = self.instance_dir.resolve()
        collected = []

        def _is_instance_path(p: Path) -> bool:
            rp = p.resolve()
            try:
                rp.relative_to(inst_root_dir)
            except Exception:
                return False
            # Exclude domain-root files even if instance_dir equals domain_root (e.g., base runs)
            try:
                rp.relative_to(domain_root_dir)
                return False
            except Exception:
                return True

        for f in self.validator.get_input_files():
            try:
                src = Path(f)
                dest_name = src.name
                target_dir = instance_dir if _is_instance_path(src) else domain_dir
                # avoid collision between base/init and instance init
                if dest_name == "init.lp" and not _is_instance_path(src):
                    dest_name = "base_init.lp"
                dest_path = target_dir / dest_name
                shutil.copy(src, dest_path)
                collected.append({"source": str(src.resolve()), "dest": str(dest_path.resolve())})
            except Exception:
                pass
        # copy instance-specific extras (matrix.txt, loyalty.txt, intro.txt, etc.)
        extras = ["matrix.txt", "loyalty.txt", "intro.txt"]
        for name in extras:
            p = self.instance_dir / name
            if p.exists():
                try:
                    dest_path = dest_dir / name
                    shutil.copy(p, dest_path)
                    collected.append({"source": str(p.resolve()), "dest": str(dest_path.resolve())})
                except Exception:
                    pass
        # If running from a response file, also copy any pre-existing instance_constraints next to it
        if self.response_file_dir:
            resp_ic = Path(self.response_file_dir) / "instance_constraints"
            if resp_ic.exists() and resp_ic.is_dir():
                for src in resp_ic.iterdir():
                    try:
                        dest_name = src.name
                        domain_init = self.domains_root / self.domain / self.asp_version / "constraints" / "init.lp"
                        # If init.lp shows up here, treat it as domain init to avoid polluting instance constraints
                        if dest_name == "init.lp":
                            dest_name = "base_init.lp"
                            dest_path = domain_dir / dest_name
                        else:
                            dest_path = instance_dir / dest_name
                        shutil.copy(src, dest_path)
                        collected.append({"source": str(src.resolve()), "dest": str(dest_path.resolve())})
                    except Exception:
                        pass

        # persist collection log
        collect_path = dest_dir / "collect.json"
        try:
            collect_path.write_text(json.dumps(collected, indent=2))
        except Exception:
            pass
