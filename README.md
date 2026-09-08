# blocking-exec marketplace

A [Codex plugin marketplace][marketplace-docs] repository that ships a single
plugin: [`blocking-exec`](./plugins/blocking-exec), which makes shell-style tool
calls run to completion and return their real, captured output.

## What the plugin does

`blocking-exec` is a **PreToolUse hook**. For every `Bash`, `PowerShell`, and
`exec_command` tool call it intercepts, the hook:

1. runs the original command synchronously to completion (never returning early),
   capturing its combined stdout+stderr to a file in the system temp dir, and
2. replaces the original command with a **replay** operation that re-emits the
   captured output and reproduces the original process exit status.

The model therefore sees faithful output and correct exit codes instead of a
running session being cut short.

### Important host limitation

The plugin works only when the Codex host routes the matching tool call through
its PreToolUse hook runtime. Installing a marketplace plugin **cannot** turn an
unhookable internal command channel into a hookable one. If a call returns a
"still running" session early, the host simply did not invoke the hook for that
call. Test with a short wait first to confirm hook delivery on your setup.

## Repository layout

```text
.
├── .agents/plugins/
│   └── marketplace.json        # Codex marketplace catalog (repo scope)
├── plugins/
│   └── blocking-exec/          # the plugin bundle
│       ├── .codex-plugin/
│       │   └── plugin.json     # plugin manifest (required by Codex)
│       ├── hooks/
│       │   ├── blocking_exec.py   # the PreToolUse hook entry point
│       │   └── hooks.json         # hook event registration
│       ├── scripts/
│       │   ├── replay.py        # Bash replay command
│       │   └── replay.ps1       # PowerShell replay command
│       └── tests/
│           └── test_hook.py    # end-to-end hook test
└── README.md
```

The plugin name (`blocking-exec`) matches the marketplace entry so the install
identifier is `blocking-exec@codex-marketplace`.

## Install

Two options, depending on which surface you add the marketplace from.

### Codex CLI

```powershell
# from a git clone of this repo
codex plugin marketplace add <repository-path>
codex plugin install blocking-exec@codex-marketplace
```

`codex plugin marketplace add .` works too when run from the repository root,
because Codex discovers the catalog at `.agents/plugins/marketplace.json`.

### ChatGPT desktop / Codex app

The desktop app reads repo-scoped marketplaces automatically from
`.agents/plugins/marketplace.json`. Open the **Plugins** browser, find the
`codex-marketplace` tab, and enable `blocking-exec`.

> Start a new Codex task after installing so the hooks are loaded.

## How it works

Event registration ([`hooks.json`](./plugins/blocking-exec/hooks/hooks.json))
matches the `Bash|PowerShell|exec_command` tools on `PreToolUse`. The
registered command runs
[`blocking_exec.py`](./plugins/blocking-exec/hooks/blocking_exec.py), which
reads the hook payload from stdin. The hook ignores any event or tool it does
not support and otherwise leaves the payload unchanged.

For a supported call it:

- resolves the working directory (`workdir` / `cwd`),
- executes the command via `bash -lc` (Bash) or `powershell.exe` (others),
  streaming combined output into a random temp log file,
- replies with `permissionDecision: allow` and an `updatedInput` whose command
  is replaced by the matching replay script,
- returns the replay's own exit status, which reproduces the original.

## Local test

Test requires PowerShell (for the PowerShell side of the hook) and Python
3.x on `PATH`:

```powershell
python plugins\blocking-exec\tests\test_hook.py
```

Run it from any directory; paths are resolved relative to the test file.

## Marketplace catalog

The catalog lives at
[`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json) — the
location Codex checks for a repository-scoped marketplace. It lists the plugin
entry, policy (`AVAILABLE`, auth `ON_INSTALL`), and category.

<!--- links --->
[marketplace-docs]: https://developers.openai.com/codex/plugins
