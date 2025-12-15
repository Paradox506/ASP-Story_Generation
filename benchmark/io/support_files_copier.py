import json
import shutil
from pathlib import Path


class SupportFilesCopier:
    """Copies clingo inputs and instance extras into the run directory."""

    def copy_support_files(
        self,
        dest_dir: Path,
        clingo_input_files: list,
        domain_root_dir: Path,
        instance_root_dir: Path,
        response_file_dir: Path | None,
    ) -> None:
        domain_dir = dest_dir / "domain_constraints"
        domain_dir.mkdir(parents=True, exist_ok=True)
        instance_dir = dest_dir / "instance_constraints"
        instance_dir.mkdir(parents=True, exist_ok=True)

        collected = []

        def is_instance_path(path: Path) -> bool:
            resolved = path.resolve()
            try:
                resolved.relative_to(instance_root_dir.resolve())
            except Exception:
                return False
            try:
                resolved.relative_to(domain_root_dir.resolve())
                return False
            except Exception:
                return True

        for filePath in clingo_input_files:
            try:
                src = Path(filePath)
                dest_name = src.name
                target_dir = instance_dir if is_instance_path(src) else domain_dir
                if dest_name == "init.lp" and not is_instance_path(src):
                    dest_name = "base_init.lp"
                dest_path = target_dir / dest_name
                shutil.copy(src, dest_path)
                collected.append({"source": str(src.resolve()), "dest": str(dest_path.resolve())})
            except Exception:
                pass

        for name in ["matrix.txt", "loyalty.txt", "intro.txt"]:
            p = instance_root_dir / name
            if p.exists():
                try:
                    dest_path = dest_dir / name
                    shutil.copy(p, dest_path)
                    collected.append({"source": str(p.resolve()), "dest": str(dest_path.resolve())})
                except Exception:
                    pass

        if response_file_dir:
            response_instance_constraints = response_file_dir / "instance_constraints"
            if response_instance_constraints.exists() and response_instance_constraints.is_dir():
                for src in response_instance_constraints.iterdir():
                    try:
                        dest_name = src.name
                        if dest_name == "init.lp":
                            dest_name = "base_init.lp"
                            dest_path = domain_dir / dest_name
                        else:
                            dest_path = instance_dir / dest_name
                        shutil.copy(src, dest_path)
                        collected.append({"source": str(src.resolve()), "dest": str(dest_path.resolve())})
                    except Exception:
                        pass
            for txt in response_file_dir.glob("*.txt"):
                try:
                    dest_path = dest_dir / txt.name
                    shutil.copy(txt, dest_path)
                    collected.append({"source": str(txt.resolve()), "dest": str(dest_path.resolve())})
                except Exception:
                    pass

        collectPath = dest_dir / "collect.json"
        try:
            collectPath.write_text(json.dumps(collected, indent=2))
        except Exception:
            pass
