#!/usr/bin/env python3
"""Replay the captured output of a Bash command."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: replay.py <status> <log-path>", file=sys.stderr)
        return 2
    try:
        status = int(sys.argv[1])
        sys.stdout.buffer.write(Path(sys.argv[2]).read_bytes())
    except OSError as error:
        print(f"blocking-exec: cannot read captured output: {error}", file=sys.stderr)
        return 127
    except ValueError:
        return 2
    return status


if __name__ == "__main__":
    raise SystemExit(main())
