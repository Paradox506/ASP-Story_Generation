from pathlib import Path
from typing import Dict, List, Optional, Set
import re


def _read_optional(path: Path) -> str:
    return path.read_text() if path.exists() else ""


class BasePromptBuilder:
    """
    Build prompts with dynamic world/context sections plus the domain template.
    """

    def __init__(self, domain: str, asp_version: str = "original"):
        self.domain = domain
        self.asp_version = asp_version

    def build_prompt(self, base_dir: Path, instance_dir: Optional[Path] = None) -> str:
        domain_dir = base_dir / self.domain / self.asp_version
        template = self._load_template(domain_dir)
        characters, locations, objects, relations = self._load_static_facts(domain_dir, instance_dir)
        goal_text = self._load_goal(domain_dir)
        init_text = self._load_init(instance_dir or domain_dir)
        intro_text = self._load_intro(instance_dir)

        parts: List[str] = []
        parts.append(self._format_entities(characters, locations, objects, relations))
        parts.append(self._format_goal(goal_text))
        parts.append(self._format_initial_state(init_text))
        parts.append(self._format_actions_section(template))
        if intro_text:
            parts.append("Instance intro:\n" + intro_text)
        return "\n\n".join([p for p in parts if p])

    def _load_template(self, domain_dir: Path) -> str:
        prompt_path = domain_dir / "prompt.txt"
        if prompt_path.exists():
            return prompt_path.read_text()
        fallback = domain_dir.parent / "base" / "prompt.txt"
        return fallback.read_text()

    def _load_goal(self, domain_dir: Path) -> str:
        goal_path = domain_dir / "goal.lp"
        return goal_path.read_text() if goal_path.exists() else ""

    def _load_init(self, target_dir: Path) -> str:
        for name in ["instance_init.lp", "init.lp"]:
            p = target_dir / name
            if p.exists():
                return p.read_text()
        return ""

    def _load_intro(self, instance_dir: Optional[Path]) -> str:
        if instance_dir:
            return _read_optional(instance_dir / "intro.txt")
        return ""

    def _format_entities(
        self,
        characters: Set[str],
        locations: Set[str],
        objects: Set[str],
        relations: Dict[str, List[str]],
    ) -> str:
        lines = [
            "Entities:",
            f"- Characters: {', '.join(sorted(characters)) if characters else 'N/A'}",
            f"- Locations: {', '.join(sorted(locations)) if locations else 'N/A'}",
            f"- Objects: {', '.join(sorted(objects)) if objects else 'N/A'}",
        ]
        if relations:
            rel_lines = []
            for k, vals in relations.items():
                rel_lines.append(f"  * {k}: {', '.join(sorted(vals))}")
            lines.append("Static relations:\n" + "\n".join(rel_lines))
        return "\n".join(lines)

    def _format_goal(self, goal_text: str) -> str:
        return "Narrative goal:\n" + (goal_text.strip() or "N/A")

    def _format_initial_state(self, init_text: str) -> str:
        return "Initial state (ASP facts):\n" + (init_text.strip() or "N/A")

    def _format_actions_section(self, template: str) -> str:
        # Keep the domain-authored action/precondition/effect descriptions intact
        return template.strip()

    def _load_static_facts(
        self, domain_dir: Path, instance_dir: Optional[Path]
    ) -> (Set[str], Set[str], Set[str], Dict[str, List[str]]):
        chars: Set[str] = set()
        locs: Set[str] = set()
        objs: Set[str] = set()
        relations: Dict[str, List[str]] = {}

        def extract_atoms(path: Path, predicate: str) -> List[str]:
            items: List[str] = []
            if not path.exists():
                return items
            pattern = re.compile(rf"{predicate}\(\s*([^)]+?)\s*\)\s*\.")
            for line in path.read_text().splitlines():
                m = pattern.search(line)
                if m:
                    for chunk in m.group(1).split(";"):
                        items.append(chunk.strip())
            return items

        sources = [domain_dir / "domain.lp"]
        if instance_dir:
            sources.append(instance_dir / "instance.lp")
        for src in sources:
            chars.update(extract_atoms(src, "character"))
            locs.update(extract_atoms(src, "place") or extract_atoms(src, "location"))
            objs.update(extract_atoms(src, "object"))
            # catch generic attr(...) as relations
            if src.exists():
                for line in src.read_text().splitlines():
                    am = re.search(r"attr\(([^)]+)\)\s*\.", line)
                    if am:
                        rel = am.group(1).strip()
                        relations.setdefault("attributes", []).append(rel)
        return chars, locs, objs, relations


class AladdinPromptBuilder(BasePromptBuilder):
    pass


class WesternPromptBuilder(BasePromptBuilder):
    pass


class SecretAgentPromptBuilder(BasePromptBuilder):
    pass


def get_prompt_builder(domain: str, asp_version: str):
    if domain == "aladdin":
        return AladdinPromptBuilder(domain, asp_version)
    if domain == "western":
        return WesternPromptBuilder(domain, asp_version)
    if domain == "secret_agent":
        return SecretAgentPromptBuilder(domain, asp_version)
    return BasePromptBuilder(domain, asp_version)
