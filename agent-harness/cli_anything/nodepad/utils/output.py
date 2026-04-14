"""Output formatting — human-readable and JSON modes."""

from __future__ import annotations

import json
import sys
from typing import Any


_json_mode = False


def set_json_mode(enabled: bool) -> None:
    global _json_mode
    _json_mode = enabled


def is_json_mode() -> bool:
    return _json_mode


def output(data: Any, human: str | None = None) -> None:
    """Print output — JSON dict in json mode, human-readable string otherwise."""
    if _json_mode:
        if isinstance(data, str):
            data = {"message": data}
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        if human is not None:
            print(human)
        elif isinstance(data, str):
            print(data)
        elif isinstance(data, dict):
            for k, v in data.items():
                print(f"  {k}: {v}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    print(json.dumps(item, indent=2, ensure_ascii=False, default=str))
                else:
                    print(f"  {item}")
        else:
            print(str(data))


def error(msg: str, exit_code: int = 1) -> None:
    """Print error and optionally exit."""
    if _json_mode:
        print(json.dumps({"error": msg}), file=sys.stderr)
    else:
        print(f"Error: {msg}", file=sys.stderr)
    if exit_code:
        sys.exit(exit_code)


def success(msg: str) -> None:
    """Print success message."""
    if _json_mode:
        print(json.dumps({"status": "ok", "message": msg}))
    else:
        print(msg)
