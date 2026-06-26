"""Print OmniOps runtime mode and backend reachability."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.services.runtime_status import get_runtime_status  # noqa: E402


def main() -> None:
    print(json.dumps(get_runtime_status(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
