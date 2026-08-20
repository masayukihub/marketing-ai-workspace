#!/usr/bin/env python3
"""Dependency-free workspace validation for local use and GitHub Actions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROOT = ["README.md", "AGENTS.md", ".gitignore", ".env.example"]
REQUIRED_MEMORY = ["PROJECT.md", "STATUS.md", "DECISIONS.md", "SOURCES.md", "TODO.md"]
PROHIBITED_NAMES = {".env", ".env.local", "credentials.json", "token.json"}
PROHIBITED_SUFFIXES = {".pem", ".key", ".p12"}
SKIP_PARTS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".jsonl", ".yaml", ".yml", ".csv", ".py",
    ".js", ".mjs", ".ts", ".tsx", ".rb", ".sh", ".html", ".css", ".toml"
}
SECRET_PATTERNS = {
    "private_key": re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    "assigned_secret": re.compile(
        r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password)"
        r"\s*[:=]\s*[\"']?([^\s\"']{12,})"
    ),
}
PLACEHOLDER_MARKERS = ("YOUR_", "EXAMPLE", "PLACEHOLDER", "${{", "NEED_CONFIRMATION", "PATH_TO_")


def iter_files():
    for path in ROOT.rglob("*"):
        if path.is_file() and not any(part in SKIP_PARTS for part in path.parts):
            yield path


def check_structure() -> list[str]:
    errors = []
    for item in REQUIRED_ROOT:
        if not (ROOT / item).is_file():
            errors.append(f"missing root file: {item}")
    for directory in ("skills", "projects", "memory", "data", "automations", "apps", "docs", "tests", ".github"):
        if not (ROOT / directory).is_dir():
            errors.append(f"missing root directory: {directory}")
    return errors


def check_memory() -> list[str]:
    errors = []
    base = ROOT / "memory/project-memory"
    for project in sorted(path for path in base.iterdir() if path.is_dir() and path.name != "_template"):
        for filename in REQUIRED_MEMORY:
            if not (project / filename).is_file():
                errors.append(f"project memory missing: {project.name}/{filename}")
    return errors


def check_links() -> list[str]:
    errors = []
    pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
    for path in iter_files():
        if path.suffix.lower() != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for target in pattern.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:", "#", "/Users/", "skill://")):
                continue
            candidate = (path.parent / unquote(target)).resolve()
            if not candidate.exists():
                errors.append(f"broken local link: {path.relative_to(ROOT)} -> {target}")
    return errors


def check_secrets() -> list[str]:
    errors = []
    for path in iter_files():
        relative = path.relative_to(ROOT)
        name = path.name.lower()
        if name in PROHIBITED_NAMES or path.suffix.lower() in PROHIBITED_SUFFIXES:
            if name != ".env.example":
                errors.append(f"prohibited sensitive filename: {relative}")
                continue
        if path.suffix.lower() not in TEXT_SUFFIXES and name != ".env.example":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for risk, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                snippet = match.group(0).upper()
                if any(marker in snippet for marker in PLACEHOLDER_MARKERS):
                    continue
                if "GITHUB_TOKEN" in snippet and "${{" in snippet:
                    continue
                errors.append(f"possible {risk}: {relative}")
                break
    return sorted(set(errors))


def check_large_files() -> list[str]:
    limit = 25 * 1024 * 1024
    return [
        f"large file over 25MB: {path.relative_to(ROOT)}"
        for path in iter_files() if path.stat().st_size > limit
    ]


CHECKS = {
    "structure": check_structure,
    "memory": check_memory,
    "links": check_links,
    "secrets": check_secrets,
    "large-files": check_large_files,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", choices=["all", *CHECKS], default="all")
    args = parser.parse_args()
    selected = CHECKS if args.check == "all" else {args.check: CHECKS[args.check]}
    failures = 0
    for name, function in selected.items():
        errors = function()
        if errors:
            failures += len(errors)
            print(f"FAIL {name} ({len(errors)})")
            for error in errors:
                print(f"- {error}")
        else:
            print(f"PASS {name}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
