import argparse
from pathlib import Path
import json

from benchmark.experiment_runner import ExperimentRunner
from benchmark.config import load_config


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
    args = parser.parse_args()

    cfg_path = Path(args.config) if args.config else None
    cfg = load_config(cfg_path)

    domain = args.domain or cfg["experiment"]["domain"]
    asp_version = args.asp_version or cfg["experiment"]["asp_version"]
    model = args.model or cfg["experiment"]["models"][0]
    clingo_path = args.clingo or cfg["asp"]["clingo_path"]
    maxstep = args.maxstep or cfg["experiment"]["maxstep"]
    output_dir = Path(args.output_dir or cfg["experiment"]["output_dir"])

    base = Path(__file__).parent
    if args.instance:
        instance_dir = Path(args.instance)
    else:
        instance_dir = base / domain / asp_version

    response_text = None
    if args.response_file:
        response_text = Path(args.response_file).read_text()

    runner = ExperimentRunner(
        base_dir=base,
        domain=domain,
        asp_version=asp_version,
        instance_dir=instance_dir,
        model=model,
        clingo_path=clingo_path,
        maxstep=maxstep,
        config_path=cfg_path,
        output_dir=output_dir,
    )
    result = runner.run(response_text=response_text)

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
