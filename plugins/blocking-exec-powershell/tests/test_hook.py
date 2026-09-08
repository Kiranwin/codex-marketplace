from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "blocking_exec.py"
SPEC = importlib.util.spec_from_file_location("blocking_exec", HOOK)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def invoke(payload: dict) -> str:
    result = subprocess.run(
        [sys.executable, HOOK], input=json.dumps(payload), text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=ROOT, check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["hookSpecificOutput"]["updatedInput"]["cmd"]


payload = {
    "hook_event_name": "PreToolUse",
    "tool_name": "exec_command",
    "tool_input": {
        "cmd": "Write-Output 'start'; Start-Sleep -Seconds 2; Write-Output 'finish'; exit 13",
        "workdir": str(ROOT),
    },
}
started = time.monotonic()
replacement = invoke(payload)
assert time.monotonic() - started >= 1.8
replay = subprocess.run(
    ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", replacement],
    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
)
assert replay.returncode == 13, replay.stderr
assert replay.stdout.splitlines() == ["start", "finish"]
print("blocking-exec-powershell hook test: ok")
