# ASP Story Generation Evaluation Pipeline

## TLDR

### Enviroment Set Up
```bash
git clone https://github.com/Paradox506/ASP-Story_Generation.git
cd ./ASP-Story_Generation
uv sync
export OPENAI_API_KEY="<Your OpenAI API Key>"
```
### Run the first instance of secret agent story domain using ChatGPT 4o
```bash
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain secret_agent \
  --model  chatgpt-4o-latest
```

### Run the first instance of aladdin story domain using ChatGPT o1
#### Note: it might take several minutes for o1 to respond
```bash
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain aladdin \
  --model  o1
```

### Run the first instance of western story domain using ChatGPT o1
#### Note: it might take several minutes for o1 to respond
```bash
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain western \
  --model  o1
```

### Run specific instance using specific model using Openrouter API

```bash
export OPENROUTER_API_KEY="<Your Openrouter API Key>"
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain <domain> \
  --instance <instance-path> \  
  --provider openrouter \
  --model  <model-id-defined-by-openrouter>
```
#### For example
Run secret agent on 16 x 16 map with 64 obstacles using Claude 3.7 Sonnet
```bash
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain secret_agent \
  --instance benchmark/domains/secret_agent/instances/random_grid_16x16_64obstacle_1key/random_grid_16x16_64obstacle_1key_0 \
  --provider openrouter \
  --model anthropic/claude-3.7-sonnet
```

### Generate Prompt without making LLM calls
```bash
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain <domain> \
  --instance <instance-path>  \
  --prompt-only
```

### Run verifier using an previous LLM response 
```bash
python benchmark/cli/run_benchmark.py \
  --response-file <path-to-llm_raw.txt>
```


## ASP Story Generation Evaluation Pipeline

This repository contains ASP encodings and prompts for three narrative planning domains (Secret Agent, Aladdin, Western), plus a Python benchmark runner.

The main pipeline is:

1. Build a domain-specific prompt from `benchmark/domains/<domain>/<asp_version>/prompts/` and the selected instance directory.
2. (Online mode) Call an LLM to generate a JSON plan.
3. Parse the JSON plan into a normalized action list.
4. Build a narrative plan ASP file (`<domain>_NarrPlan.lp`) from actions.
5. Validate with `clingo` using:
   - domain constraints (`benchmark/domains/<domain>/<asp_version>/constraints/*.lp`)
   - instance constraints (`benchmark/domains/<domain>/instances/**/instance.lp`)
   - generated narrative plan (`<domain>_NarrPlan.lp`)
6. Persist all artifacts under `results/`.

## Architecture

```text
┌───────────────────────────────────────────────────────────────────────────┐
│                           CLI ENTRYPOINT                                  │
│  python benchmark/cli/run_benchmark.py                                    │
│  (root shim: run_benchmark.py -> benchmark/cli/run_benchmark.py)          │
└───────────────┬───────────────────────────────────────────────────────────┘
                │ parses args + loads config (default + override)
                v
┌───────────────────────────────────────────────────────────────────────────┐
│                         CONFIG LAYER                                      │
│  benchmark/config/config_loader.py                                        │
│   - load_combined_config(config.default.yaml, user_config)                │
│   - deep_merge                                                            │
│   - to_experiment_config -> ExperimentConfig + LlmConfig                  │
│                                                                           │
│  benchmark/config/config_utils.py                                         │
│   - load_api_key(provider): env var or YAML provider.api_key              │
└───────────────┬───────────────────────────────────────────────────────────┘
                │ resolves: domains_root, instance selection, model/provider
                v
┌───────────────────────────────────────────────────────────────────────────┐
│                      DOMAIN REGISTRY / ADAPTERS                           │
│  benchmark/domain_registry.py                                             │
│   - get_adapter(domain)                                                   │
│   - default_instance_dirs(domains_root) -> first instance found           │
│   - evaluator_factory() -> domain evaluator                               │
└───────────────┬───────────────────────────────────────────────────────────┘
                │ constructs one ExperimentRunner per (model, instance, run)
                v
┌───────────────────────────────────────────────────────────────────────────┐
│                         EXPERIMENT RUNNER                                 │
│  benchmark/runner/experiment_runner.py                                    │
│  For each run:                                                            │
│   1) prompt = PromptBuilder.build_prompt(domains_root, instance_dir)      │
│   2) LLM: online call OR offline response-file OR prompt-only             │
│   3) parse = PlanParser.parse(llm_raw)                                    │
│   4) constraints_text = PlanParser.build_constraints(parse.actions)       │
│   5) asp = ASPValidator.validate_plan(..., constraints_text)              │
│   6) evaluation = Evaluator.evaluate(asp, parse, ...)                     │
│   7) persist artifacts + copy support files                               │
└───────────────┬───────────────────────────────────────────────────────────┘
                │
                │
                v
┌───────────────────────────────────────────────────────────────────────────┐
│                 PLAN PARSERS / CONSTRAINT BUILDING                        │
│ benchmark/llm_post_processing/plan_parser/                                │
│  - get_plan_parser(domain, domain_dir, instance_dir)                      │
│  - <DomainPlanParser>.parse(raw_text) -> normalized actions               │
│  - <DomainPlanParser>.build_constraints(actions, maxstep) -> <domain>.lp  │
│                                                                           │
│ (Internally may use benchmark/llm_post_processing/constraint_builder/*)   │
└───────────────┬───────────────────────────────────────────────────────────┘
                v
┌───────────────────────────────────────────────────────────────────────────┐
│                        ASP VALIDATION (CLINGO)                            │
│ benchmark/asp/validator.py                                                │
│  - Collect clingo input files:                                            │
│     domain_constraints/*.lp + instance_constraints/*.lp + plan.lp         │
│  - Run clingo (JSON output)                                               │
│  - Parse satisfiable / witnesses / conflicts / nonexec                    │
└───────────────┬───────────────────────────────────────────────────────────┘
                v
┌───────────────────────────────────────────────────────────────────────────┐
│                           EVALUATION LAYER                                │
│ benchmark/evaluators/*                                                    │
│  - Base metrics + domain-specific metrics  #TODO more analysis            │
│  - Consumes ASP outputs + parse outputs                                   │
└───────────────┬───────────────────────────────────────────────────────────┘
                v
┌───────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT / ARTIFACTS                              │
│ benchmark/io/artifact_writer.py                                           │
│  - Writes result.json, prompt.txt, llm_raw.txt, parse.json, asp.json      │
│  - Writes clingo_stdout.txt / clingo_raw.json                             │
│  - Writes <domain>_NarrPlan.lp                                            │
│                                                                           │
│ benchmark/io/support_files_copier.py                                      │
│  - Copies clingo input LPs into output:                                   │
│     domain_constraints/ and instance_constraints/                         │
│  - Copies response-file sibling txt files                                 │
│  - Writes collect.json manifest (src -> dest mapping)                     │
└───────────────────────────────────────────────────────────────────────────┘
```

```text
┌─────────────────┬───────────────┬───────────────────────┬───────────────────┐
│ Mode            │ LLM Call      │ Parse/Build           │ Clingo Validation │
├─────────────────┼───────────────┼───────────────────────┼───────────────────┤
│ Online          │ Yes           │ Yes                   │ Yes               │
│ Prompt-only     │ No            │ No                    │ No                │
│ Response-file   │ No            │ Yes                   │ Yes               │
└─────────────────┴───────────────┴───────────────────────┴───────────────────┘
```


## Requirements

- Python 3.10+
- `clingo` (available on PATH, or set `asp.clingo_path` in config)
- `uv` for dependency management (required)

## Install

This project is managed with `uv`:

```bash
uv sync
```

## Project Layout

- `benchmark/domains/<domain>/`
  - `<asp_version>/constraints/*.lp` (domain ASP constraints)
  - `<asp_version>/prompts/*` (prompt templates / prompt assets)
  - `instances/**/instance.lp` (instance ASP constraints; plus optional extra files like `loyalty.txt`)
- `benchmark/cli/run_benchmark.py` (main CLI)
- `benchmark/runner/experiment_runner.py` (single run execution)
- `benchmark/asp/validator.py` (clingo invocation + output parsing)
- `benchmark/llm_post_processing/` (plan parsers + constraint builders)

`asp_version` is typically `base` or `original`.

## Configuration

Config is YAML. The runner loads:

1. `config.default.yaml` (baseline defaults)
2. `--config <your.yaml>` (overrides, deep-merged)

CLI flags override both config files. In particular, `--provider`, `--model`, `--clingo`, `--maxstep`, `--output-dir`, `--runs`, `--workers`, `--max-tokens`, and `--max-output-tokens` are intended as quick overrides.

### Example: OpenAI config

`config.openai.yaml` is an example. 

Preferred: set an environment variable:

```bash
export OPENAI_API_KEY="..."
```

Or set it in a local YAML file (not recommended for shared repos):

```yaml
openai:
  api_key: ""
llm:
  provider: "openai"
```

### Provider and model via CLI

You can set provider/model on the command line without editing YAML:

```bash
export OPENAI_API_KEY="..."
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain secret_agent \
  --provider openai \
  --model openai/o1
```

Notes:

- For OpenAI, `openai/o1` is normalized to `o1` internally (to match the OpenAI API model naming).
- In response-file mode, no API call is made; `--provider/--model` only affect labeling and output paths.

### Key config fields

`domains_root` (top-level):
- Default: `benchmark/domains`
- Controls where the runner looks for domain constraints/prompts/instances.

`experiment`:
- `domain`: `western` | `secret_agent` | `aladdin`
- `asp_version`: `base` | `original` 
- `models`: llm model tag (dependes on provider e.g. `openai/chatgpt-4o-latest` for openrouter `chatgpt-4o-latest` for openai)
- `runs_per_instance`: repeat each instance N times
- `workers`: thread pool size for running multiple runs
- `output_dir`: where to write results (default `results`)
- `maxstep`: optional clingo constant (if null, uses `len(actions)+1`)
- `instances`: optional list of instance directories (see “Running Specific Instances”)

`asp`:
- `clingo_path`: command name or absolute path to `clingo`

`llm`:
- `provider`: `openai` | `openrouter` | `anthropic`
- `max_tokens`, `max_output_tokens`: global overrides (optional)
- `model_max_tokens`, `model_max_output_tokens`: per-model overrides (optional)
- `domain_max_output_tokens`: per-domain overrides (optional)

### Full config reference

Top-level:
- `domains_root` (string): where to find `benchmark/domains/<domain>/...` (default `benchmark/domains`)

`experiment`:
- `domain` (string): `western` | `secret_agent` | `aladdin`
- `asp_version` (string): `base` | `original`
- `models` (list[string]): list of model identifiers (used when `--model` is not provided)
- `runs_per_instance` (int): number of runs per instance (ignored in response-file mode)
- `instances` (list[string]): specific variation instance directories; each entry may be:
  - absolute path, or
  - path relative to repo root, or
  - path relative to `<domains_root>/<domain>/instances/` (e.g. `random_grid_10x10_25obstacle_1key/random_grid_10x10_25obstacle_1key_0`)
- `maxstep` (int|null): clingo max step constant; if null, uses `len(actions)+1`
- `output_dir` (string): results directory (default `results`)
- `workers` (int): number of parallel workers (default 1)

`asp`:
- `clingo_path` (string): `clingo` or an absolute path

`llm`:
- `provider` (string): `openai` | `openrouter` | `anthropic`
- `max_tokens` (int|null): optional global override
- `max_output_tokens` (int|null): optional global override
- `model_max_tokens` (map[string]int): optional per-model override
- `model_max_output_tokens` (map[string]int): optional per-model override
- `domain_max_output_tokens` (map[string]int): optional per-domain override

Provider credentials (either env var or YAML):
- OpenAI: `OPENAI_API_KEY` or `openai.api_key`
- OpenRouter: `OPENROUTER_API_KEY` or `openrouter.api_key` (also supports `~/.openrouter.yaml`)
- Anthropic: `ANTHROPIC_API_KEY` or `anthropic.api_key`

`logging` (optional):
- `level` (string): e.g. `INFO`
- `file` (string): e.g. `benchmark.log`

## Running

### Modes (online / prompt-only / response-file)

The runner supports three modes:

- Online mode: generates a prompt and calls an LLM provider (OpenAI/OpenRouter/Anthropic), then parses and validates with clingo.
- Prompt-only mode: generates and saves the prompt without calling an LLM or clingo.
- Response-file mode: replays a previously saved LLM response (`llm_raw.txt`) without calling an LLM, then parses and validates with clingo.

### Prompt-only mode (no LLM, no clingo)

```bash
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain secret_agent \
  --prompt-only \
  --output-dir results
```

This writes the prompt and support files to `results/.../PROMPT_ONLY`.

### Online mode (call an LLM)

Example (OpenAI):

```bash
export OPENAI_API_KEY="..."
python benchmark/cli/run_benchmark.py \
  --config config.openai.yaml \
  --domain secret_agent \
  --output-dir results
```

### Response-file mode (offline replay based on a previous llm ouput)

Use a pre-saved `llm_raw.txt` from a previous run:

```bash
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain secret_agent \
  --response-file results/<previous_run>/run_0000/secret_agent/base/o1/<instance>/llm_raw.txt \
  --output-dir results
```

The runner will infer the instance path from the response file directory if possible.

## Running Specific Instances

There are three ways to select instances:

1. `--instance <path-to-instance-dir>`

```bash
python benchmark/cli/run_benchmark.py \
  --config config.default.yaml \
  --domain secret_agent \
  --instance benchmark/domains/secret_agent/instances/random_grid_10x10_25obstacle_1key/random_grid_10x10_25obstacle_1key_0
```

2. `--instances <dir1> <dir2> ...` (multiple instances)

3. `experiment.instances` in your config YAML:

```yaml
experiment:
  domain: secret_agent
  instances:
    - random_grid_10x10_25obstacle_1key/random_grid_10x10_25obstacle_1key_0
    - random_grid_8x8_16obstacle_1key/random_grid_8x8_16obstacle_1key_0
```

Relative values are interpreted as:
- `<repo_root>/<value>` if that exists, otherwise
- `<domains_root>/<domain>/instances/<value>`

## Output Artifacts

Artifacts are written under a directory structure so you can diff runs and replay response files.

### Directory structure

For each run, files are written to:

```
results/<run_id>/run_<seq>/<domain>/<asp_version>/<model>/<instance_label>/
```

Where:

- `<run_id>` is a timestamp like `2025-12-08_22-53-30_PST`.
  - response-file mode runs append `_response_file`
  - prompt-only mode runs append `_prompt_only`
- `<seq>` is zero-padded (e.g. `0000`, `0001`) for multiple runs.
- `<domain>` is `secret_agent` (in examples below).
- `<asp_version>` is `base` or `original`.
- `<model>` is the model name with `/` replaced by `_` (e.g. `openai/o1` becomes `openai_o1`).
- `<instance_label>` is:
  - if the instance directory contains `instances/`, the last two path components (`<group>/<instance>`), e.g.
    `random_grid_10x10_25obstacle_1key/random_grid_10x10_25obstacle_1key_0`
  - otherwise the instance directory name

Example path (response-file):

```
results/2025-12-08_22-53-30_PST_response_file/run_0000/secret_agent/base/openai_o1/random_grid_10x10_25obstacle_1key/random_grid_10x10_25obstacle_1key_0/
```

### Files

Common files:

- `result.json`: high-level stage/success/metadata
- `prompt.txt`: prompt sent to the LLM (or built in prompt-only mode)
- `llm_raw.txt`: raw LLM output (or copied from response-file)
- `parse.json`: parsed actions + valid sets (even on parse failure)
- `asp.json`: structured ASP validation output (if validation ran)
- `clingo_stdout.txt` / `clingo_raw.json`: raw clingo output
- `<domain>_NarrPlan.lp`: generated narrative plan constraints
- `domain_constraints/`: copied domain LP inputs used for clingo
- `instance_constraints/`: copied instance LP inputs used for clingo
- `collect.json`: a manifest of copied support files and their source paths
