#!/usr/bin/env python3
"""Run supported PreToolUse commands synchronously and replay final output.

The host must expose a matching PreToolUse event. This hook cannot intercept a
tool call that the Codex host does not route through its hooks runtime.
"""

from __future__ import annotations

import json
import os
import secrets
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path


LOG_DIR = Path(tempfile.gettempdir()) / "blocking-exec"
SUPPORTED_TOOLS = {"Bash", "PowerShell", "exec_command"}


def command_field(tool_name: str) -> str:
    return "cmd" if tool_name == "exec_command" else "command"


def get_command(payload: dict, tool_name: str) -> str | None:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get(command_field(tool_name))
    return command if isinstance(command, str) else None


def get_cwd(payload: dict) -> str | None:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("workdir", "cwd"):
            value = tool_input.get(key)
            if isinstance(value, str) and value:
                return value
    value = payload.get("cwd")
    return value if isinstance(value, str) and value else None


def shell_argv(tool_name: str, command: str) -> list[str]:
    if tool_name == "Bash":
        return ["bash", "-lc", command]
    return [
        "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
        "-ExecutionPolicy", "Bypass", "-Command", command,
    ]


def run_command(tool_name: str, command: str, cwd: str | None, log_path: Path) -> int:
    with log_path.open("wb") as log:
        try:
            process = subprocess.Popen(
                shell_argv(tool_name, command), cwd=cwd, stdout=log,
                stderr=subprocess.STDOUT,
            )
        except OSError as error:
            log.write(f"failed_to_start: {error}\n".encode())
            return 127
        return process.wait()


def powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def replay_command(tool_name: str, status: int, log_path: Path) -> str:
    plugin_root = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
    if tool_name == "Bash":
        replay = plugin_root / "scripts" / "replay.py"
        return "python {} {} {}".format(
            shlex.quote(str(replay)), status, shlex.quote(str(log_path))
        )
    replay = plugin_root / "scripts" / "replay.ps1"
    return (
        "& powershell.exe -NoLogo -NoProfile -NonInteractive "
        "-ExecutionPolicy Bypass -File {} {}; exit $LASTEXITCODE"
    ).format(powershell_quote(str(replay)), powershell_quote(f"{status}|{log_path}"))


def new_log_path() -> Path:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR / f"{secrets.token_hex(16)}.log"


def main() -> int:
    payload = json.load(sys.stdin)
    tool_name = payload.get("tool_name")
    if payload.get("hook_event_name") != "PreToolUse" or tool_name not in SUPPORTED_TOOLS:
        return 0
    command = get_command(payload, tool_name)
    if command is None:
        return 0

    log_path = new_log_path()
    status = run_command(tool_name, command, get_cwd(payload), log_path)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": {
                command_field(tool_name): replay_command(tool_name, status, log_path)
            },
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
