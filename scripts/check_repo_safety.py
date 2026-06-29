"""Repository safety checks for release and CI.

The script intentionally checks only git-tracked files. It avoids scanning
untracked local directories such as .venv, Docker volumes, and caches.
"""

from __future__ import annotations

import subprocess
import sys
import re
from pathlib import Path


RISKY_PATH_PARTS = {
    ".venv/",
    "__pycache__/",
    ".pytest_cache/",
    "docker/volumes/",
    "docker-volumes/",
    "volumes/",
}
RISKY_SUFFIXES = {".log"}
OPENAI_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    tracked_files = _tracked_files(root)
    failures: list[str] = []

    _check_tracked_paths(tracked_files, failures)
    _check_env_example(root, tracked_files, failures)
    _check_key_markers(root, tracked_files, failures)

    if failures:
        print("Repo safety check failed.")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("Repo safety check passed.")
    return 0


def _tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        item.decode("utf-8")
        for item in result.stdout.split(b"\0")
        if item
    ]


def _check_tracked_paths(tracked_files: list[str], failures: list[str]) -> None:
    if ".env" in tracked_files:
        failures.append(".env is tracked by git")

    for path in tracked_files:
        normalized = path.replace("\\", "/")
        if any(part in f"{normalized}/" for part in RISKY_PATH_PARTS):
            failures.append(f"tracked cache or volume path: {path}")
        if Path(path).suffix in RISKY_SUFFIXES:
            failures.append(f"tracked temporary log file: {path}")


def _check_env_example(
    root: Path,
    tracked_files: list[str],
    failures: list[str],
) -> None:
    example = ".env.live.example"
    if example not in tracked_files:
        return

    content = (root / example).read_text(encoding="utf-8", errors="ignore")
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("LLM_API_KEY="):
            _, value = stripped.split("=", 1)
            if value.strip():
                failures.append(".env.live.example contains a non-empty LLM_API_KEY")


def _check_key_markers(
    root: Path,
    tracked_files: list[str],
    failures: list[str],
) -> None:
    for path in tracked_files:
        full_path = root / path
        if not full_path.is_file():
            continue
        try:
            content = full_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if OPENAI_KEY_PATTERN.search(content):
            failures.append(f"possible OpenAI API key in {path}")


if __name__ == "__main__":
    sys.exit(main())
