import json
import os
from pathlib import Path
from typing import Dict, Optional


class ArtifactWriter:
    """
    Responsible for run_id layout and writing artifacts to disk.
    """

    def __init__(self, output_dir: Path, domain: str, asp_version: str, model: str, instance_name: str):
        self.output_dir = output_dir
        self.domain = domain
        self.asp_version = asp_version
        self.model = model.replace("/", "_")
        self.instance_name = instance_name

    def ensure_dir(self, run_id: str) -> Path:
        dest_dir = (
            self.output_dir
            / run_id
            / self.domain
            / self.asp_version
            / self.model
            / self.instance_name
        )
        os.makedirs(dest_dir, exist_ok=True)
        return dest_dir

    def write(
        self,
        run_id: str,
        result: Dict,
        prompt: Optional[str],
        llm_raw: Optional[str],
        parse: Optional[Dict],
        asp: Optional[Dict],
        raw_clingo: Optional[str] = None,
        constraints: Optional[str] = None,
    ) -> Path:
        dest_dir = self.ensure_dir(run_id)
        (dest_dir / "result.json").write_text(json.dumps(result, indent=2))
        (dest_dir / "prompt.txt").write_text(prompt or "")
        if llm_raw is not None:
            (dest_dir / "llm_raw.txt").write_text(llm_raw)
        if parse is not None:
            (dest_dir / "parse.json").write_text(json.dumps(parse, indent=2))
        if asp is not None:
            (dest_dir / "asp.json").write_text(json.dumps(asp, indent=2))
        if result.get("evaluation") is not None:
            (dest_dir / "evaluation.json").write_text(json.dumps(result["evaluation"], indent=2))
        if raw_clingo is not None:
            (dest_dir / "clingo_raw.json").write_text(raw_clingo)
            (dest_dir / "clingo_stdout.txt").write_text(raw_clingo)
        if constraints is not None:
            (dest_dir / f"{self.domain}_NarrPlan.lp").write_text(constraints)
        if result.get("stage") == "prompt_only":
            (dest_dir / "PROMPT_ONLY").write_text("Prompt-only run (no LLM/ASP call)")
        return dest_dir

    def append_log(self, run_id: str, result: Dict):
        log_path = self.output_dir / "benchmark.log"
        timing = result.get("llm_timing", {}) or {}
        with open(log_path, "a") as f:
            f.write(
                f"{run_id} domain={self.domain} asp={self.asp_version} model={self.model} "
                f"instance={self.instance_name} stage={result.get('stage')} success={result.get('success')} "
                f"elapsed={timing.get('elapsed')} prompt_tokens={timing.get('prompt_tokens')} "
                f"completion_tokens={timing.get('completion_tokens')}\n"
            )
