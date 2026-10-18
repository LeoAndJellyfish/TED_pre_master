"""Validate skill metadata, local references and the portable payload."""
from __future__ import annotations

import json
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
    docs = [root / "SKILL.md", root / "README.md", *sorted((root / "references").glob("*.md"))]
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
    return {"status": "passed", "version": version, "payload_files": len(files),
            "local_links": links, "evaluation_tasks": len(cases)}


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False))
