"""Mechanical rehearsal notes; this tool does not grade speech quality."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

CUE = re.compile(r"\[(停顿|演示|切换|互动)\s*(\d+(?:\.\d+)?)\s*秒\]")
NOTE = re.compile(r"\[(?:画面|动作|提示)[：:][^\]\n]*\]")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$")


def select_lines(text: str, section: str | None) -> list[tuple[int, str]]:
    lines = list(enumerate(text.splitlines(), 1))
    if not section:
        return lines
    start = None
    level = None
    in_fence = False
    fence_char = ""
    for index, (_, line) in enumerate(lines):
        fence = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            if not in_fence:
                in_fence, fence_char = True, fence.group(1)[0]
            elif fence.group(1)[0] == fence_char:
                in_fence = False
            continue
        if in_fence:
            continue
        heading = HEADING.match(line)
        if heading:
            current_level = len(heading.group(1))
            if start is None and heading.group(2) == section:
                start, level = index + 1, current_level
            elif start is not None and current_level <= level:
                return lines[start:index]
    if start is None:
        raise ValueError(f"Section not found: {section}")
    return lines[start:]


def spoken_lines(text: str, section: str | None = None) -> tuple[list[tuple[int, str]], float]:
    lines = select_lines(text, section)
    result = []
    seconds = 0.0
    frontmatter = bool(lines and lines[0][0] == 1 and lines[0][1].strip() == "---")
    in_fence = False
    fence_char = ""
    for line_no, line in lines:
        if frontmatter:
            if line_no > 1 and line.strip() == "---":
                frontmatter = False
            continue
        fence = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            if not in_fence:
                in_fence, fence_char = True, fence.group(1)[0]
            elif fence.group(1)[0] == fence_char:
                in_fence = False
            continue
        if in_fence or HEADING.match(line) or re.match(r"^\s*\|.*\|\s*$", line):
            continue
        seconds += sum(float(match.group(2)) for match in CUE.finditer(line))
        line = CUE.sub("", line)
        line = NOTE.sub("", line)
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|>\s*)", "", line)
        result.append((line_no, line))
    return result, seconds


def inspect(text: str, section: str | None = None, cpm: float | None = None,
            forbid: tuple[str, ...] = (), patterns: tuple[str, ...] = ()) -> dict:
    if cpm is not None and cpm <= 0:
        raise ValueError("CPM must be positive")
    lines, fixed_seconds = spoken_lines(text, section)
    spoken = "\n".join(line for _, line in lines)
    han = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", spoken))
    digits = len(re.findall(r"[0-9]", spoken))
    latin = len(re.findall(r"[A-Za-z]", spoken))
    count = han + digits + latin
    hits = []
    for expression, literal in [(s, True) for s in forbid] + [(s, False) for s in patterns]:
        compiled = re.compile(re.escape(expression) if literal else expression)
        for line_no, line in lines:
            for match in compiled.finditer(line):
                hits.append({"line": line_no, "rule": expression, "match": match.group(0)})
    result = {"kind": "mechanical_rehearsal_notes", "section": section,
              "counting_rule": "Han characters + ASCII digits + Latin letters; punctuation excluded",
              "spoken_characters": count, "han_characters": han, "digits": digits,
              "latin_letters": latin, "fixed_cue_seconds": fixed_seconds,
              "user_constraint_hits": hits,
              "quality_assessment": "requires source checking, listening and rehearsal"}
    if cpm is not None:
        result["time_estimate"] = {"calibrated_characters_per_minute": cpm,
                                   "spoken_seconds": round(60 * count / cpm, 1),
                                   "total_seconds": round(60 * count / cpm + fixed_seconds, 1),
                                   "status": "estimate; measured delivery takes precedence"}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--section", help="Exact Markdown heading containing spoken text")
    parser.add_argument("--cpm", type=float, help="Speaker's measured speed using this counting rule")
    parser.add_argument("--forbid", action="append", default=[])
    parser.add_argument("--forbid-regex", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.input.read_text(encoding="utf-8-sig"), args.section, args.cpm,
                         tuple(args.forbid), tuple(args.forbid_regex))
    except (OSError, ValueError, re.error) as error:
        parser.exit(2, f"{error}\n")
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 1 if result["user_constraint_hits"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
