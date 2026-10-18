"""Validate skill metadata, local references and the portable payload."""
from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from build_release import ROOT, payload_files


def validate(root: Path = ROOT) -> dict:
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    if not frontmatter:
        raise ValueError("Missing YAML frontmatter")
    fields = dict(re.findall(r"^(\w+):\s*(.+)$", frontmatter.group(1), re.M))
    if fields.get("name") != "ted-pre-master" or not fields.get("description", "").strip('"'):
        raise ValueError("Invalid skill name or description")
    if re.search(r"\bTODO\b|\[TODO|\[TBD", text):
        raise ValueError("Unfinished skill scaffold")
    metadata = (root / "agents/openai.yaml").read_text(encoding="utf-8")
    ui = {k: json.loads(v) for k, v in re.findall(r'^\s{2}(\w+):\s*(".*")$', metadata, re.M)}
    if not 25 <= len(ui.get("short_description", "")) <= 64:
        raise ValueError("UI description must contain 25-64 characters")
    if "$ted-pre-master" not in ui.get("default_prompt", ""):
        raise ValueError("Default prompt must invoke the skill")
    links = 0
    docs = [root / "SKILL.md", root / "README.md"]
    for directory in ("references", "evaluation", "docs"):
        docs.extend(sorted((root / directory).rglob("*.md")))
    for doc in docs:
        for link in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if re.match(r"[a-z]+://", link) or link.startswith("#"):
                continue
            target = link.split("#", 1)[0].strip("<>")
            if target and not (doc.parent / target).exists():
                raise ValueError(f"Broken local link: {doc.name}: {link}")
            links += 1
    files = payload_files(root)
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Invalid version")
    cases = json.loads((root / "evaluation/cases.json").read_text(encoding="utf-8"))
    if len({row["id"] for row in cases}) != len(cases) or any(not row["prompt"].strip() for row in cases):
        raise ValueError("Invalid evaluation task records")
    verified = 0

    def verify_digest(relative: str, expected: str) -> None:
        nonlocal verified
        path = root / relative
        if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
            raise ValueError(f"Invalid evidence path: {relative}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Evidence digest mismatch: {relative}")
        verified += 1

    snapshot = json.loads((root / "evaluation/post-review-skill-manifest.json").read_text(encoding="utf-8"))
    for relative, expected in snapshot["files"].items():
        verify_digest(relative, expected)
    for name in ("outputs/manifest.json", "outputs/revision-manifest.json", "forward/manifest.json"):
        manifest = json.loads((root / "evaluation" / name).read_text(encoding="utf-8"))
        for row in manifest["outputs"]:
            verify_digest(row["file"], row["sha256"])
            if "parent_file" in row:
                verify_digest(row["parent_file"], row["parent_sha256"])
        for relative, expected in manifest.get("resources", {}).items():
            verify_digest(relative, expected)
        if "skill_manifest_sha256" in manifest:
            verify_digest(manifest["frozen_skill_manifest"], manifest["skill_manifest_sha256"])
    forward = json.loads((root / "evaluation/forward/cases.json").read_text(encoding="utf-8"))["cases"]
    verify_digest("evaluation/forward/cases.json", snapshot["forward_cases_sha256"])
    return {"status": "passed", "version": version, "payload_files": len(files),
            "local_links": links, "evaluation_tasks": len(cases), "forward_tasks": len(forward),
            "evidence_hashes_verified": verified}


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False))
