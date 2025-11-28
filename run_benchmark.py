import argparse
from pathlib import Path
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from benchmark.experiment_runner import ExperimentRunner
from benchmark.config_loader import load_combined_config, to_experiment_config
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
    parser.add_argument("--asp-version", help="Override asp version")
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
    args = parser.parse_args()

    cfg_path = Path(args.config) if args.config else None
    cfg = load_combined_config(Path("config.default.yaml"), cfg_path)
    exp_cfg, llm_cfg = to_experiment_config(cfg)

    domain = args.domain or exp_cfg.domain
    asp_version = args.asp_version or exp_cfg.asp_version
    model = args.model or llm_cfg.models[0]
    models = [model] if args.model else llm_cfg.models
    clingo_path = args.clingo or cfg["asp"]["clingo_path"]
    maxstep = args.maxstep or exp_cfg.maxstep
    output_dir = Path(args.output_dir or exp_cfg.output_dir)
    runs_per_instance = args.runs or exp_cfg.runs_per_instance
    workers = args.workers or exp_cfg.workers
    model_max_tokens_map = llm_cfg.model_max_tokens or {}
    model_max_map = llm_cfg.model_max_output_tokens or {}
    global_max_tokens = args.max_tokens or llm_cfg.max_tokens
    global_max_output_tokens = args.max_output_tokens or llm_cfg.max_output_tokens

    base = Path(__file__).parent
    if args.instances:
        instance_dirs = [Path(p) for p in args.instances]
    elif args.instance:
        instance_dirs = [Path(args.instance)]
    elif exp_cfg.instances:
        instance_dirs = [Path(p) for p in exp_cfg.instances]
    else:
        adapter = get_adapter(domain)
        instance_dirs = adapter.default_instance_dirs(base, asp_version)

    response_text = None
    if args.response_file:
        response_text = Path(args.response_file).read_text()

    run_id_base = Path(args.output or output_dir).name if args.output else None
    if not run_id_base:
        run_id_base = Path(output_dir).name
        # if output_dir is default "results", append timestamp to avoid clashes
        if run_id_base == "results":
            run_id_base = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")

    results: List[Dict[str, Any]] = []
    tasks = [(idx, m, inst) for idx, (m, inst) in enumerate([(m, inst) for m in models for inst in instance_dirs for _ in range(runs_per_instance)])]

    def run_task(seq: int, model_name: str, inst_dir: Path):
        # Resolve per-model max_output_tokens: CLI/global override first, otherwise model-specific map
        mot = global_max_output_tokens
        if mot is None:
            mot = model_max_map.get(model_name)
        mtok = global_max_tokens
        if mtok is None:
            mtok = model_max_tokens_map.get(model_name)
        runner = ExperimentRunner(
            base_dir=base,
            domain=domain,
            asp_version=asp_version,
            instance_dir=inst_dir,
            model=model_name,
            clingo_path=clingo_path,
            maxstep=maxstep,
            config_path=cfg_path,
            output_dir=output_dir,
            run_id_override=run_id_base,
            max_tokens=mtok,
            max_output_tokens=mot,
            exp_cfg=exp_cfg,
            llm_cfg=llm_cfg,
        )
        return runner.run(response_text=response_text, run_seq=seq)

    if workers and workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            future_map = {ex.submit(run_task, seq, m, inst): (m, inst) for seq, m, inst in tasks}
            for fut in as_completed(future_map):
                results.append(fut.result())
    else:
        for seq, m, inst in tasks:
            results.append(run_task(seq, m, inst))

    summary = summarize_results(results)

    output_data = {"summary": summary, "runs": results}

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
