import argparse
from pathlib import Path
import json

from .plan_parser import parse_plan


def main():
    parser = argparse.ArgumentParser(description="Parse a plan JSON output given domain and instance.")
    parser.add_argument("--domain", required=True, choices=["aladdin", "secret_agent", "western"])
    parser.add_argument("--asp-version", default="original")
    parser.add_argument("--instance-dir", required=True, help="Path to instance directory")
    parser.add_argument("--input", required=True, help="File containing LLM output to parse")
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    domain_dir = base / args.domain / args.asp_version
    instance_dir = Path(args.instance_dir)
    llm_output = Path(args.input).read_text()

    result = parse_plan(args.domain, domain_dir, instance_dir, llm_output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
