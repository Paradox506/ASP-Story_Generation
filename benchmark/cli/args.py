import argparse


def build_arg_parser():
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
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Only build prompts without calling LLM/ASP (will be persisted)",
    )
    parser.add_argument("--domains-root", help="Override domains root directory (default: benchmark/domains)")
    return parser


def parse_args(argv=None):
    return build_arg_parser().parse_args(argv)

