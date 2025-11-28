import json
import tempfile
from pathlib import Path
from typing import Dict, List
import subprocess

from .utils import ActionMapper, extract_intention


class ASPValidator:
    """
    Minimal clingo-based validator for one-off mode.
    Converts LLM actions into ASP constraints and inspects clingo JSON output.
    """

    def __init__(self, domain: str, domain_dir: Path, instance_dir: Path, clingo_path: str = "clingo"):
        self.domain = domain
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir
        self.clingo_path = clingo_path
        self.mapper = ActionMapper(domain)

    def _collect_files(self) -> List[str]:
        files: List[str] = []
        for name in ["domain.lp", "actions.lp"]:
            path = self.domain_dir / name
            if path.exists():
                files.append(str(path))
        # instance-specific
        for name in ["instance_init.lp", "init.lp"]:
            path = self.instance_dir / name
            if path.exists():
                files.append(str(path))
                break
        inst = self.instance_dir / "instance.lp"
        if inst.exists():
            files.append(str(inst))
        goal = self.domain_dir / "goal.lp"
        if goal.exists():
            files.append(str(goal))
        return files

    def _constraints_from_actions(self, actions: List[Dict]) -> str:
        lines: List[str] = []
        for t, action in enumerate(actions):
            subj = action["subject"]
            aid = action["actionId"]
            params = action.get("parameters", [])
            functor = self.mapper.to_asp_functor(aid, params)
            if self.domain == "aladdin":
                if aid in (0, 7, 8):
                    intention = "_"
                else:
                    intention = extract_intention(action.get("character_plan", "")) or "_"
                lines.append(f":- not act({subj}, {functor}, {intention}, {t}).")
            elif self.domain == "western":
                lines.append(f":- not act({subj}, {functor}, {t}).")
                executed_flag = action.get("executed", True)
                if executed_flag:
                    lines.append(f":- not executed({subj}, {functor}, {t}).")
                else:
                    lines.append(f":- executed({subj}, {functor}, {t}).")
            else:  # secret_agent
                lines.append(f":- not act({subj}, {functor}, {t}).")
        return "\n".join(lines)

    def validate_plan(self, actions: List[Dict], maxstep: int = 10) -> Dict:
        asp_constraints = self._constraints_from_actions(actions)
        with tempfile.NamedTemporaryFile("w+", suffix=".lp", delete=False) as tf:
            tf.write(asp_constraints)
            constraint_path = tf.name

        files = self._collect_files() + [constraint_path]
        cmd = [self.clingo_path, *files, "-c", f"maxstep={maxstep}", "--outf=2", "0"]
        proc = subprocess.run(cmd, capture_output=True, text=True)

        result: Dict = {
            "cmd": cmd,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "satisfiable": False,
            "nonexec_feedback": [],
            "unjustified": [],
            "open_commitment_frames": [],
            "conflicts": [],
        }

        try:
            data = json.loads(proc.stdout)
            if data.get("Result") == "SATISFIABLE":
                result["satisfiable"] = True
                values = data["Call"][0]["Witnesses"][0]["Value"] if data["Call"] and data["Call"][0]["Witnesses"] else []
                result.update(self._extract_symbols(values))
        except Exception:
            # leave parsed fields as defaults
            pass
        return result

    def _extract_symbols(self, values: List[str]) -> Dict:
        nonexec = []
        unjust = []
        open_frames = []
        conflicts = []
        for atom in values:
            if atom.startswith("nonexec_feedback"):
                nonexec.append(atom)
            elif atom.startswith("unjustified"):
                unjust.append(atom)
            elif atom.startswith("open_commitment_frame"):
                open_frames.append(atom)
            elif atom.startswith("conflict"):
                conflicts.append(atom)
        return {
            "nonexec_feedback": nonexec,
            "unjustified": unjust,
            "open_commitment_frames": open_frames,
            "conflicts": conflicts,
        }
