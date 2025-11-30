import argparse
from pathlib import Path
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
import shlex

from benchmark.runner.experiment_runner import ExperimentRunner
from benchmark.config.config_loader import load_combined_config, to_experiment_config
from benchmark.domains import get_adapter


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    completed = sum(1 for r in results if r.get("stage") == "complete")
    sat = sum(
        1
        for r in results
        if r.get("stage") == "complete" and r.get("asp", {}).get("satisfiable", False)
    )
    timing_vals = [r.get("llm_timing", {}) for r in results if r.get("llm_timing")]
    prompt_tokens = [t.get("prompt_tokens") for t in timing_vals if t.get("prompt_tokens") is not None]
    completion_tokens = [
        t.get("completion_tokens") for t in timing_vals if t.get("completion_tokens") is not None
    ]
    elapsed = [t.get("elapsed") for t in timing_vals if t.get("elapsed") is not None]

    def _avg(xs: List[float]) -> float:
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "total_runs": total,
        "completed_runs": completed,
        "sat_runs": sat,
        "success_rate": sat / total if total else 0.0,
        "avg_prompt_tokens": _avg(prompt_tokens),
        "avg_completion_tokens": _avg(completion_tokens),
        "avg_elapsed": _avg(elapsed),
    }


def main():
    parser = argparse.ArgumentParser(description="Minimal one-off benchmark runner")
    parser.add_argument("--config", default="config.yaml", help="Config YAML path")
    parser.add_argument("--domain", choices=["aladdin", "secret_agent", "western"], help="Override domain")
    parser.add_argument("--instance", help="Path to instance dir (defaults to domain/asp_version)")
    parser.add_argument("--model", help="Override model name")
    parser.add_argument("--clingo", help="Override clingo path")
    parser.add_argument("--maxstep", type=int, help="Override maxstep")
    parser.add_argument("--response-file", help="Use pre-saved LLM response instead of calling API")
    parser.add_argument("--output", help="Where to write JSON result")
    parser.add_argument("--output-dir", help="Base directory to store run artifacts")
    parser.add_argument("--runs", type=int, help="Runs per instance per model")
    parser.add_argument("--instances", nargs="+", help="Explicit instance directories (relative or absolute)")
    parser.add_argument("--workers", type=int, help="Number of parallel workers (default serial)")
    parser.add_argument("--max-tokens", type=int, help="Override LLM max_tokens")
    parser.add_argument("--max-output-tokens", type=int, help="Override LLM max_output_tokens if supported")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic"], help="LLM provider")
    parser.add_argument("--prompt-only", action="store_true", help="Only build prompts without calling LLM/ASP (will be persisted)")
    parser.add_argument("--use-author-parser", action="store_true", help="Use author-style constraint parser instead of default")
    parser.add_argument("--domains-root", help="Override domains root directory (default: benchmark/domains)")
    args = parser.parse_args()

    command_line = " ".join(shlex.quote(a) for a in [sys.executable, __file__, *sys.argv[1:]])
    cmd_meta = {"command": command_line, "cwd": str(Path.cwd()), "args": vars(args)}

    cfg_path = Path(args.config) if args.config else None
    cfg = load_combined_config(Path("config.default.yaml"), cfg_path)
    exp_cfg, llm_cfg = to_experiment_config(cfg)

    domain = args.domain or exp_cfg.domain
    asp_version_default = exp_cfg.asp_version
    if args.response_file:
        # Offline mode: use a single model label (no API calls)
        model = args.model or (llm_cfg.models[0] if llm_cfg.models else "mock")
        models = [model]
        runs_per_instance = 1
    else:
        model = args.model or llm_cfg.models[0]
        models = [model] if args.model else llm_cfg.models
        runs_per_instance = args.runs or exp_cfg.runs_per_instance
    clingo_path = args.clingo or cfg["asp"]["clingo_path"]
    provider = args.provider or llm_cfg.provider
    maxstep = args.maxstep or exp_cfg.maxstep
    output_dir = Path(args.output_dir or exp_cfg.output_dir)
    workers = args.workers or exp_cfg.workers
    domains_root = Path(args.domains_root or cfg.get("domains_root", exp_cfg.domains_root))
    if not domains_root.is_absolute():
        domains_root = Path(__file__).parent / domains_root
    model_max_tokens_map = llm_cfg.model_max_tokens or {}
    model_max_map = llm_cfg.model_max_output_tokens or {}
    domain_max_map = llm_cfg.domain_max_output_tokens or {}
    global_max_tokens = args.max_tokens or llm_cfg.max_tokens
    global_max_output_tokens = args.max_output_tokens or llm_cfg.max_output_tokens
    use_author_style = args.use_author_parser

    base = Path(__file__).parent
    def _normalize_instance_path(p: Path) -> Path:
        # If a file is provided (e.g., llm_raw.txt), use its parent directory as the instance dir.
        return p.parent if p.is_file() else p

    if args.instances:
        instance_dirs = [_normalize_instance_path(Path(p)) for p in args.instances]
    elif args.instance:
        instance_dirs = [_normalize_instance_path(Path(args.instance))]
    elif exp_cfg.instances:
        instance_dirs = [_normalize_instance_path(Path(p)) for p in exp_cfg.instances]
    else:
        adapter = get_adapter(domain)
        instance_dirs = adapter.default_instance_dirs(base, asp_version_default)

    response_text = None
    response_file_dir = None
    if args.response_file:
        resp_path = Path(args.response_file)
        response_text = resp_path.read_text()
        response_file_dir = resp_path.parent
    if args.prompt_only:
        response_text = ""  # force offline flow but skip ASP

    # Always use timestamp-based run_id to keep date/time in paths
    run_id_base = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d_%H-%M-%S_%Z")

    results: List[Dict[str, Any]] = []
    tasks = [(idx, m, inst) for idx, (m, inst) in enumerate([(m, inst) for m in models for inst in instance_dirs for _ in range(runs_per_instance)])]

    def infer_asp_version(inst_dir: Path, default_version: str) -> str:
        # Prefer explicit markers; otherwise try to infer from presence of instance files, fallback to default.
        for part in inst_dir.parts[::-1]:
            if part in ("base", "original"):
                return part
        if (inst_dir / "instance.lp").exists() or (inst_dir / "instance_init.lp").exists() or "instances" in inst_dir.parts:
            return "base"
        return default_version

    def run_task(seq: int, model_name: str, inst_dir: Path):
        # Resolve per-model max_output_tokens: CLI/global override first, otherwise model-specific map
        mot = global_max_output_tokens
        if mot is None:
            mot = model_max_map.get(model_name)
        if mot is None:
            mot = domain_max_map.get(domain)
        mtok = global_max_tokens
        if mtok is None:
            mtok = model_max_tokens_map.get(model_name)
        asp_version = infer_asp_version(inst_dir, exp_cfg.asp_version)

        def _normalize_model_for_provider(name: str, provider: str) -> str:
            if provider == "openai":
                if name == "openai/o1":
                    return "o1"
                if name == "openai/o1-mini":
                    return "o1-mini"
            return name

        normalized_model = _normalize_model_for_provider(model_name, provider)

        runner = ExperimentRunner(
            base_dir=base,
            domains_root=domains_root,
            domain=domain,
            asp_version=asp_version,
            instance_dir=inst_dir,
            model=normalized_model,
            provider=provider,
            clingo_path=clingo_path,
            maxstep=maxstep,
            config_path=cfg_path,
            output_dir=output_dir,
            run_id_override=run_id_base,
            max_tokens=mtok,
            max_output_tokens=mot,
            exp_cfg=exp_cfg,
            llm_cfg=llm_cfg,
            use_author_style=use_author_style,
            response_file_dir=response_file_dir,
        )
        if args.prompt_only:
            prompt = runner.prompt_gen.build_prompt(domains_root, inst_dir)
            run_id = f"{run_id_base}_prompt_only/run_{seq:04d}"
            result = {
                "stage": "prompt_only",
                "success": True,
                "prompt": prompt,
                "run_id": run_id,
                "metadata": {"domain": domain, "instance": inst_dir.name, "model": model_name},
                "invocation": cmd_meta,
            }
            runner._persist_result(result, run_id, prompt, llm_raw=None, parse=None, asp=None)
            runner.copy_support_files(run_id)
            print(f"--- Prompt saved for {inst_dir} at {run_id} ---")
            print(prompt)
            return result
        result = runner.run(response_text=response_text if args.response_file else None, run_seq=seq)
        result["invocation"] = cmd_meta
        return result

    if workers and workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            future_map = {ex.submit(run_task, seq, m, inst): (m, inst) for seq, m, inst in tasks}
            for fut in as_completed(future_map):
                results.append(fut.result())
    else:
        for seq, m, inst in tasks:
            results.append(run_task(seq, m, inst))

    summary = summarize_results(results)

    output_data = {"summary": summary, "runs": results, "invocation": cmd_meta}

    if args.output:
        Path(args.output).write_text(json.dumps(output_data, indent=2))
    else:
        print(json.dumps(output_data, indent=2))


if __name__ == "__main__":
    main()


def _auto_instances(base: Path, domain: str, asp_version: str):
    """
    Heuristic instance discovery when none provided.
    - Aladdin/Secret Agent/Western: default to domain/asp_version if files exist.
    - Secret Agent: if instances dir exists, pick first random instance.
    """
    candidate = base / domain / asp_version
    if candidate.exists():
        yield candidate
        return
    if domain == "secret_agent":
        inst_root = base / domain / "instances"
        if inst_root.exists():
            # pick first instance folder
            for p in sorted(inst_root.glob("*/*/*/")):
                yield p
                return
    # fallback to base/asp_version if exists
    fallback = base / domain / "base"
    if fallback.exists():
        yield fallback
