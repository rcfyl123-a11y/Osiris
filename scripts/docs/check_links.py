#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def iter_markdown_files() -> list[Path]:
    return sorted(DOCS_DIR.rglob("*.md"))


def is_relative_link(link: str) -> bool:
    return not (
        link.startswith("http://")
        or link.startswith("https://")
        or link.startswith("#")
        or link.startswith("mailto:")
    )


def normalize_link(path: str) -> str:
    return path.split("#", 1)[0].strip()


def check_links() -> int:
    missing: list[str] = []
    for md_file in iter_markdown_files():
        content = md_file.read_text(encoding="utf-8")
        for match in LINK_RE.findall(content):
            link = normalize_link(match)
            if not link or not is_relative_link(link):
                continue
            target = (md_file.parent / link).resolve()
            if not target.exists():
                missing.append(f"{md_file.relative_to(ROOT)} -> {link}")
    if missing:
        print("Missing doc links:")
        for item in missing:
            print(f"- {item}")
        return 1
    print("All relative doc links are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(check_links())
