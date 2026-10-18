"""Build the portable skill payload reproducibly; no private evaluation data."""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "ted-pre-master"


def payload_files(root: Path = ROOT) -> list[Path]:
    files = [root / "SKILL.md", root / "LICENSE", root / "agents/openai.yaml",
             root / "scripts/speech_check.py"]
    files.extend(p for p in (root / "references").rglob("*") if p.is_file())
    for path in files:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Invalid payload file: {path}")
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def build(root: Path, output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    files = payload_files(root)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            name = f"{SKILL_NAME}/{path.relative_to(root).as_posix()}"
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive integrity check failed")
        for path in files:
            assert archive.read(f"{SKILL_NAME}/{path.relative_to(root).as_posix()}") == path.read_bytes()
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(output.suffix + ".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    return {"archive": str(output), "files": len(files), "sha256": digest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    output = args.output or ROOT / "dist" / f"{SKILL_NAME}-v{version}.zip"
    print(json.dumps(build(ROOT, output), ensure_ascii=False))


if __name__ == "__main__":
    main()
