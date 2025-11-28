import argparse
from pathlib import Path
import json

from benchmark.experiment_runner import ExperimentRunner
from benchmark.config import load_api_key


def main():
    parser = argparse.ArgumentParser(description="Minimal one-off benchmark runner")
    parser.add_argument("--domain", choices=["aladdin", "secret_agent", "western"], default="aladdin")
    parser.add_argument("--asp-version", default="original", help="base or original")
    parser.add_argument("--instance", default=None, help="Path to instance dir (defaults to domain/asp_version)")
    parser.add_argument("--model", default="openai/gpt-4o")
    parser.add_argument("--clingo", default="clingo")
    parser.add_argument("--maxstep", type=int, default=12)
    parser.add_argument("--response-file", help="Use pre-saved LLM response instead of calling API")
    parser.add_argument("--output", help="Where to write JSON result")
    parser.add_argument("--config", help="Optional config YAML containing openrouter.api_key")
    parser.add_argument("--output-dir", default="results", help="Base directory to store run artifacts")
    args = parser.parse_args()

    base = Path(__file__).parent
    if args.instance:
        instance_dir = Path(args.instance)
    else:
        # default to original directory
        instance_dir = base / args.domain / args.asp_version

    response_text = None
    if args.response_file:
        response_text = Path(args.response_file).read_text()

    runner = ExperimentRunner(
        base_dir=base,
        domain=args.domain,
        asp_version=args.asp_version,
        instance_dir=instance_dir,
        model=args.model,
        clingo_path=args.clingo,
        maxstep=args.maxstep,
        config_path=Path(args.config) if args.config else None,
        output_dir=Path(args.output_dir),
    )
    result = runner.run(response_text=response_text)

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2))
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
