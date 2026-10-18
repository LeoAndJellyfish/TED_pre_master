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
    current_path = root / "evaluation/versions" / version / "skill-manifest.json"
    if current_path.exists():
        current_snapshot = json.loads(current_path.read_text(encoding="utf-8"))
    elif version == "1.0.0":
        current_snapshot = snapshot
    else:
        raise ValueError(f"Missing current-version skill snapshot: {version}")
    if current_path.exists() and current_snapshot.get("version") != version:
        raise ValueError("Current-version skill snapshot has a different version")
    if set(current_snapshot["files"]) != {path.relative_to(root).as_posix() for path in files}:
        raise ValueError("Current-version snapshot does not cover the complete payload")
    for relative, expected in current_snapshot["files"].items():
        verify_digest(relative, expected)
    manifests = [root / "evaluation" / name for name in
                 ("outputs/manifest.json", "outputs/revision-manifest.json", "forward/manifest.json")]
    if current_snapshot.get("evidence_manifest"):
        manifests.append(root / current_snapshot["evidence_manifest"])
    current_outputs = 0
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if current_snapshot.get("evidence_manifest") and manifest_path == root / current_snapshot["evidence_manifest"]:
            if manifest.get("version") != version:
                raise ValueError("Current-version evidence manifest has a different version")
        if manifest.get("version") == version:
            current_outputs += len(manifest["outputs"])
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
    if current_snapshot.get("forward_input_sha256"):
        verify_digest(f"evaluation/versions/{version}/forward-case.json", current_snapshot["forward_input_sha256"])
    return {"status": "passed", "version": version, "payload_files": len(files),
            "local_links": links, "evaluation_tasks": len(cases), "forward_tasks": len(forward),
            "current_version_trial_outputs": current_outputs, "evidence_hashes_verified": verified}


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False))
