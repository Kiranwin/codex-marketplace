# blocking-exec

A Codex **PreToolUse hook plugin** that makes `Bash`, `PowerShell`, and
`exec_command` tool calls run to completion and then replay their real output
back to the model.

## Files

| Path | Purpose |
| --- | --- |
| `.codex-plugin/plugin.json` | Plugin manifest required by Codex; points at the hooks file. |
| `hooks/hooks.json` | Registers the hook on the `PreToolUse` event for the `Bash\|PowerShell\|exec_command` tools. |
| `hooks/blocking_exec.py` | The hook entry point executed by Codex. |
| `scripts/replay.py`  | Replays output for commands that were run through `bash`. |
| `scripts/replay.ps1` | Replays output for commands that were run through `powershell.exe`. |
| `tests/test_hook.py` | End-to-end test: intercepts, runs, and replays a PowerShell command. |

## Behavior

On each matching `PreToolUse` event the hook runs the requested command
synchronously, streaming its combined standard output (and error) into a
temporary log file under the system temp directory (`blocking-exec/`). It then
answers `permissionDecision: allow` and rewrites the command to a small
**replay** invocation that:

- writes the captured bytes back to stdout, and
- exits with the original command's exit status.

Net effect: the tool call is blocking, and its returned output and exit code
are truthful. No standalone/external process is spawned — the command runs in
the hook sub-process just as the host tool would have run it.

### Environment

Logs live in `%TEMP%\blocking-exec` (on Windows) — the exact path mirrors
`tempfile.gettempdir()`, so on POSIX hosts it is the usual `/tmp/blocking-exec`.
Replay scripts and the hook resolve the plugin root from `$PLUGIN_ROOT` if set,
falling back to the directory layout relative to their own file. No state is
kept in the repository.

## Hooking caveats

- The hook only fires if the **host** routes the matching tool through its hook
  runtime. Marketplace installation cannot make an unhookable internal command
  channel hookable — verify with a short wait on your host first.
- The hook rewrites *every* supported command on `PreToolUse`. It deliberately
  does not double-run anything itself: it runs the original command once, then
  substitutes the replay as the command the host would otherwise execute.

## Local development

Python 3.x must be on `PATH`. PowerShell is required to exercise the
`PowerShell`/`exec_command` branch of the hook and its replay script.

```powershell
# from the repository root
python plugins/blocking-exec/tests/test_hook.py
```

Expected output: `blocking-exec hook test: ok` (exit code 0). The test injects
a `Write-Output`/`Start-Sleep`/`exit 13` command, verifies the hook is blocking,
and confirms the replayed output (`start`, `finish`) and exit status (`13`).

## License

MIT.
