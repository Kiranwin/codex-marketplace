# Blocking Exec PowerShell marketplace

This repository provides a Codex marketplace and a Windows-aware Blocking Exec plugin.

The plugin matches `Bash`, `PowerShell`, and `exec_command` PreToolUse events. It executes the original command synchronously in the hook, writes combined output to the system temporary directory, and replaces the command with a replay operation that preserves its final output and exit status.

## Important host limitation

This plugin works only when the Codex host routes the matching tool through its PreToolUse hook runtime. Installing a marketplace plugin cannot make an unhookable internal command channel hookable. Test with a short wait first; if it returns a running session early, the host did not invoke the hook for that call.

## Local test

```powershell
python .\plugins\blocking-exec-powershell\tests\test_hook.py
```

## Install from a cloned repository

```powershell
codex plugin marketplace add <repository-path>
codex plugin add blocking-exec-powershell@blocking-exec-powershell
```

Start a new Codex task after installation so the hooks are loaded.
