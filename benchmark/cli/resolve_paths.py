from pathlib import Path


def infer_instance_dir_from_response_file(response_file_dir: Path, domains_root: Path, domain: str):
    parts = list(response_file_dir.parts)
    try:
        idx = parts.index(domain)
    except ValueError:
        return None
    if idx + 3 >= len(parts):
        return None
    rel = Path(*parts[idx + 3 :])
    candidate = domains_root / domain / "instances" / rel
    if candidate.exists():
        return candidate
    candidate = response_file_dir / "instance_constraints"
    if candidate.exists() and (candidate / "instance.lp").exists():
        return candidate
    return None


def infer_asp_version(instance_dir: Path, default_version: str) -> str:
    for part in instance_dir.parts[::-1]:
        if part in ("base", "original"):
            return part
    if (
        (instance_dir / "instance.lp").exists()
        or (instance_dir / "instance_init.lp").exists()
        or "instances" in instance_dir.parts
    ):
        return "base"
    return default_version


def normalize_model_for_provider(model_name: str, provider: str) -> str:
    if provider == "openai":
        if model_name == "openai/o1":
            return "o1"
        if model_name == "openai/o1-mini":
            return "o1-mini"
    return model_name


def derive_instance_label_override(domain: str, response_file_dir: Path):
    parts = list(response_file_dir.parts)
    try:
        idx = parts.index(domain)
        if idx + 3 < len(parts):
            rel = Path(*parts[idx + 3 :])
            if rel.parts:
                return rel.as_posix()
    except ValueError:
        return None
    return None


def resolve_instance_dir_for_response_file(instance_dir: Path, response_file_dir: Path) -> Path:
    response_instance_constraints = response_file_dir / "instance_constraints"
    if not (instance_dir / "instance.lp").exists() and (response_instance_constraints / "instance.lp").exists():
        return response_instance_constraints
    return instance_dir

