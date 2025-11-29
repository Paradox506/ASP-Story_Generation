import json
from pathlib import Path
from typing import Dict, List, Any
import subprocess

from benchmark.asp.action_utils import ActionMapper


class WesternAuthorConstraintBuilder:
    """
    Reproduce the constraint encoding seen in the authors' logs for the Western domain.
    - actionId mapping: 1 snakebite, 2 move(dest), 3 take(meds,carl), 4 take(meds, other), 5 heal(target, meds) or kill?
      In the log, actionId 5 was “kill” (william kills hank), and actionId 4 was heal. We mirror that mapping.
    - executed=True -> act/4 with '_' intention placeholder.
    - executed=False -> unexec_act/4 with '_' placeholder.
    - Conflict requirement: add ':- not conflict(_,_,_,_,_).' to force at least one conflict.
    """

    def __init__(self):
        self.mapper = ActionMapper("western")

    def build_constraints(self, actions: List[Dict[str, Any]]) -> str:
        lines: List[str] = []
        for t, act in enumerate(actions):
            subj = act["subject"]
            aid = act["actionId"]
            params = act.get("parameters", [])
            # Normalize params to match authors' log:
            # id3: take(meds,carl) -> expect meds,carl
            if aid == 3:
                params = ["meds", "carl"]
            # id4: heal(target) -> heal(target,meds)
            if aid == 4 and len(params) == 1:
                params = [params[0], "meds"]
            # id5: kill(victim) per the log
            functor = self._to_functor(aid, params)
            executed = act.get("executed", True)
            if executed:
                lines.append(f":- not act({subj}, {functor}, _, {t}).")
            else:
                lines.append(f":- not unexec_act({subj}, {functor}, _, {t}).")
        # Require at least one conflict, per log
        lines.append(":- not conflict(_,_,_,_,_).")
        return "\n".join(lines)

    def _to_functor(self, aid: int, params: List[str]) -> str:
        # Authors' mapping from the log:
        # 1 snakebite/0; 2 move/1; 3 take/2; 4 heal/2; 5 kill/1.
        if aid == 1:
            return "snakebite"
        if aid == 2:
            return f"move({params[0]})"
        if aid == 3:
            return f"take({params[0]},{params[1]})"
        if aid == 4:
            return f"heal({params[0]},{params[1]})"
        if aid == 5:
            return f"kill({params[0]})"
        raise ValueError(f"Unsupported actionId {aid}")


class WesternAuthorValidator:
    """
    Standalone runner to validate a Western plan in the authors' style.
    It does not modify the main pipeline and can be invoked ad hoc.
    """

    def __init__(self, domain_dir: Path, instance_dir: Path, clingo_path: str = "clingo"):
        self.domain_dir = domain_dir
        self.instance_dir = instance_dir
        self.clingo_path = clingo_path
        self.builder = WesternAuthorConstraintBuilder()

    def build_constraints(self, actions: List[Dict[str, Any]]) -> str:
        return self.builder.build_constraints(actions)

    def validate(self, actions: List[Dict[str, Any]], constraints_path: Path, maxstep: int = 12) -> Dict[str, Any]:
        constraints_path.write_text(self.build_constraints(actions))
        files = [
            str(self.domain_dir / "domain.lp"),
            str(self.domain_dir / "actions.lp"),
            str(self.instance_dir / "instance_init.lp"),
            str(self.instance_dir / "instance.lp"),
            str(constraints_path),
        ]
        cmd = [self.clingo_path, *files, "-c", f"maxstep={maxstep}", "--outf=2", "0"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        out = {"cmd": cmd, "stdout": proc.stdout, "stderr": proc.stderr, "returncode": proc.returncode}
        try:
            data = json.loads(proc.stdout)
            out["result"] = data.get("Result")
        except Exception:
            pass
        return out
