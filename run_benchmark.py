"""Compatibility entrypoint. Prefer `benchmark/cli/run_benchmark.py`."""

from benchmark.cli.resolve_paths import infer_instance_dir_from_response_file
from benchmark.cli.run_benchmark import main


if __name__ == "__main__":
    main()
