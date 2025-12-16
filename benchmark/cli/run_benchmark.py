import json
import shlex
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

if __package__ is None:  # Allows running as a script: python benchmark/cli/run_benchmark.py ...
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root))

from benchmark.cli.args import parse_args
from benchmark.cli.resolve_paths import (
    derive_instance_label_override,
    infer_asp_version,
    infer_instance_dir_from_response_file,
    normalize_model_for_provider,
    resolve_instance_dir_for_response_file,
)
from benchmark.config.config_loader import load_combined_config, to_experiment_config
from benchmark.domain_registry import get_adapter
from benchmark.reporting.summary import summarize_results
from benchmark.runner.experiment_runner import ExperimentRunner


def main(argv=None):
    args = parse_args(argv)

    command_line = " ".join(
        shlex.quote(a) for a in [sys.executable, str(Path(sys.argv[0]).resolve()), *sys.argv[1:]]
    )
    cmd_meta = {"command": command_line, "cwd": str(Path.cwd()), "args": vars(args)}

    cfg_path = Path(args.config) if args.config else None
    cfg = load_combined_config(Path("config.default.yaml"), cfg_path)
    exp_cfg, llm_cfg = to_experiment_config(cfg)

    domain = args.domain or exp_cfg.domain
    asp_version_default = exp_cfg.asp_version

    if args.response_file:
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
        domains_root = Path(__file__).resolve().parents[2] / domains_root

    base = Path.cwd()

    response_text = None
    response_file_dir = None
    if args.response_file:
        response_file = Path(args.response_file)
        response_text = response_file.read_text()
        response_file_dir = response_file.parent

    instance_dirs = []
    if args.instances:
        for p in args.instances:
            instance_dirs.append(Path(p) if Path(p).is_absolute() else base / p)
    elif args.instance:
        instance_dirs = [Path(args.instance) if Path(args.instance).is_absolute() else base / args.instance]
    elif response_file_dir:
        inferred = infer_instance_dir_from_response_file(response_file_dir, domains_root, domain)
        if inferred is None:
            raise ValueError(f"Cannot infer instance dir from response file dir: {response_file_dir}")
        instance_dirs = [inferred]
    elif exp_cfg.instances:
        resolved = []
        for inst in exp_cfg.instances:
            inst_path = Path(inst)
            if inst_path.is_absolute():
                resolved.append(inst_path)
                continue
            candidate = base / inst_path
            if candidate.exists():
                resolved.append(candidate)
                continue
            candidate = domains_root / domain / "instances" / inst_path
            resolved.append(candidate)
        instance_dirs = resolved
    else:
        adapter = get_adapter(domain)
        instance_dirs = adapter.default_instance_dirs(domains_root)
        if not instance_dirs:
            expected = domains_root / domain / "instances"
            raise ValueError(
                f"No instances found under {expected}. Use --instance/--instances to specify manually."
            )

    run_id_base = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d_%H-%M-%S_%Z")

    global_max_output_tokens = args.max_output_tokens or llm_cfg.max_output_tokens
    global_max_tokens = args.max_tokens or llm_cfg.max_tokens
    model_max_map = llm_cfg.model_max_output_tokens or {}
    domain_max_map = llm_cfg.domain_max_output_tokens or {}
    model_max_tokens_map = llm_cfg.model_max_tokens or {}

    results = []
    tasks = [
        (idx, m, inst)
        for idx, (m, inst) in enumerate(
            [(m, inst) for m in models for inst in instance_dirs for unused in range(runs_per_instance)]
        )
    ]

    def run_task(seq, model_name, inst_dir):
        max_output_tokens = global_max_output_tokens
        if max_output_tokens is None:
            max_output_tokens = model_max_map.get(model_name)
        if max_output_tokens is None:
            max_output_tokens = domain_max_map.get(domain)

        max_tokens = global_max_tokens
        if max_tokens is None:
            max_tokens = model_max_tokens_map.get(model_name)

        asp_version = infer_asp_version(inst_dir, exp_cfg.asp_version)
        normalized_model = normalize_model_for_provider(model_name, provider)

        instance_label_override = None
        if response_file_dir:
            instance_label_override = derive_instance_label_override(domain, response_file_dir)

        inst_dir_for_runner = inst_dir
        if response_file_dir:
            inst_dir_for_runner = resolve_instance_dir_for_response_file(inst_dir, response_file_dir)

        runner = ExperimentRunner(
            base_dir=base,
            domains_root=domains_root,
            domain=domain,
            asp_version=asp_version,
            instance_dir=inst_dir_for_runner,
            model=normalized_model,
            provider=provider,
            clingo_path=clingo_path,
            maxstep=maxstep,
            config_path=cfg_path,
            output_dir=output_dir,
            run_id_override=run_id_base,
            max_tokens=max_tokens,
            max_output_tokens=max_output_tokens,
            exp_cfg=exp_cfg,
            llm_cfg=llm_cfg,
            response_file_dir=response_file_dir,
            instance_label_override=instance_label_override,
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
            runner.persist_result(result, run_id, prompt, llm_raw=None, parse=None, asp=None)
            runner.copy_support_files(run_id)
            print(f"--- Prompt saved for {inst_dir} at {run_id} ---")
            print(prompt)
            return result

        result = runner.run(response_text=response_text if args.response_file else None, run_seq=seq)
        result["invocation"] = cmd_meta
        return result
    
    total_tasks = len(tasks)
    if workers and workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {}
            for i, (seq, m, inst) in enumerate(tasks, start=1):
                print(f"[{i}/{total_tasks}] START domain={domain} model={m} instance={inst}")
                future = executor.submit(run_task, seq, m, inst)
                future_map[future] = (i, m, inst)

            for future in as_completed(future_map):
                i, m, inst = future_map[future]
                result = future.result()
                meta = result.get("metadata") or {}
                asp = result.get("asp") or {}
                satisfiable = asp.get("satisfiable")
                if satisfiable is True:
                    clingo_result = "SATISFIABLE"
                elif satisfiable is False:
                    clingo_result = "UNSATISFIABLE"
                else:
                    clingo_result = "N/A"

                out_path = (
                    f"{output_dir}/"
                    f"{result.get('run_id')}/"
                    f"{meta.get('domain')}/"
                    f"{meta.get('asp_version')}/"
                    f"{str(meta.get('model','')).replace('/','_')}/"
                    f"{meta.get('instance')}"
                )

                print(
                    f"[{i}/{total_tasks}] DONE  "
                    f"Plan:{clingo_result} "
                    f"domain={meta.get('domain')} "
                    f"model={meta.get('model')} "
                    f"instance={meta.get('instance')} "
                    f"stage={result.get('stage')} "
                    f"out={out_path}",
                    file=sys.stderr,
                    flush=True,
                )
                results.append(result)

    else:
        for i, (seq, m, inst) in enumerate(tasks, start=1):
            print(f"[{i}/{total_tasks}] START domain={domain} model={m} instance={inst}")
            result = run_task(seq, m, inst)
            meta = result.get("metadata") or {}
            asp = result.get("asp") or {}
            satisfiable = asp.get("satisfiable")
            if satisfiable is True:
                clingo_result = "SATISFIABLE"
            elif satisfiable is False:
                clingo_result = "UNSATISFIABLE"
            else:
                clingo_result = "N/A"

            out_path = (
                f"{output_dir}/"
                f"{result.get('run_id')}/"
                f"{meta.get('domain')}/"
                f"{meta.get('asp_version')}/"
                f"{str(meta.get('model','')).replace('/','_')}/"
                f"{meta.get('instance')}"
            )

            print(
                f"[{i}/{total_tasks}] DONE  "
                f"Plan: {clingo_result} "
                f"domain={meta.get('domain')} "
                f"model={meta.get('model')} "
                f"instance={meta.get('instance')} "
                f"stage={result.get('stage')} "
                f"out={out_path}",
                file=sys.stderr,
                flush=True,
            )
            results.append(result)

    summary = summarize_results(results)
    output_data = {"summary": summary, "runs": results, "invocation": cmd_meta}

    if args.output:
        Path(args.output).write_text(json.dumps(output_data, indent=2))
    # else:
    #     print(json.dumps(output_data, indent=2))


if __name__ == "__main__":
    main()
