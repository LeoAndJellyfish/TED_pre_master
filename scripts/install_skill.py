"""Install a verified local skill payload into a new destination directory."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

from build_release import ROOT, payload_files


def default_destination() -> Path:
    codex_directory = Path(os.environ["CODEX_HOME"]).expanduser() if os.environ.get("CODEX_HOME") else Path.home() / ".codex"
    return codex_directory / "skills" / "ted-pre-master"


def install(destination: Path) -> dict:
    if destination.exists():
        raise FileExistsError(f"Destination already exists; review it before replacing: {destination}")
    files = payload_files(ROOT)
    destination.mkdir(parents=True)
    for source in files:
        relative = source.relative_to(ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert hashlib.sha256(target.read_bytes()).digest() == hashlib.sha256(source.read_bytes()).digest()
    return {"destination": str(destination.resolve()), "files": len(files), "verified": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=default_destination())
    args = parser.parse_args()
    try:
        result = install(args.dest)
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
