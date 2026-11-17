# AGENTS.md

This repository follows the Conclave-SDK 3-agent conventions.

## Project

Read these before changing anything, in this order:

| Document | What it decides |
| -------- | --------------- |
| [`design/SPEC.md`](./design/SPEC.md) | The design contract: every screen, state, measurement, key and line of text |
| [`design/tokens.json`](./design/tokens.json) | Every colour, size and type style the interface may set |
| [`docs/plans/2026-11-16-doubletake-foundation.md`](./docs/plans/2026-11-16-doubletake-foundation.md) | Architecture, decisions, repository layout, testing, release |
| [`todo/implementation-plan.md`](./todo/implementation-plan.md) | The build plan, generated from the TODO sections |

Where the code lives once `D00 T01` lands: `src/engine/` (the scan, hash, match and recycle library), `src/appcore/` (view models, with no XAML), `src/app/` (the WinUI 3 executable), `src/cli/` (a console program for tests), and `tests/`. Design sources are in `design/`, generated brand files in `resources/`, plan and review tooling in `scripts/`.

Commands that verify a change:

```powershell
python scripts/todo-graph.py validate                 # the TODO tree
python scripts/todo-graph.py plan --check             # the generated plan is current
python -m unittest discover -s scripts/tests          # the plan, review and kit tooling
node scripts/verify-agent-tiers.mjs                   # the Claude subagent definitions
pwsh scripts/check.ps1                                # the build, every test program and the plan checks (after D00 T01 §4)
```

Rules specific to DoubleTake:

- **The spec leads.** A change to how something looks, reads or behaves goes to `design/SPEC.md` first, in the same commit range, and the mockup is corrected with it. No XAML or C++ file sets a hex colour or a size the tokens hold: values come from `design/tokens.json` through the generated theme.
- **A photo is never deleted.** Unwanted copies go to the Recycle Bin through the engine's recycle function and nowhere else. No code path calls `DeleteFile`, `std::filesystem::remove` or a shell delete without the recycle flag on a user's file, and every group keeps at least one photo.
- **Tests never touch the owner's data.** Every test uses a temporary folder for photos and passes `--data-dir` for the index, settings and logs. A test recycles only files it created itself and restores or purges them in its own teardown, leaving the Recycle Bin as it found it. No test scans, reads or changes a folder outside `build/` and the system temporary folder.
- **A child process never outlives its test.** A test that starts `DoubleTake.exe`, `doubletake-cli.exe` or an installer stops the whole process tree on timeout and in teardown, and passes no window to console children.
- **A run never restarts itself.** An unattended run starts only when the operator starts it (`pwsh scripts/start-run.ps1`) and ends with its window. Nothing schedules, resumes or watches one.
- **Heavy jobs queue.** Run a full build or the full test suite as `bosun run -- <command>` when `bosun` is installed, and directly when it is not.
- **Windows only.** DoubleTake builds with MSVC and runs on Windows 10 version 1809 or later, x64. Do not add WSL, Linux or another compiler to the build. The unattended kit's tmux launcher (`scripts/unattended-run.py`) is installed but cannot build this project; `scripts/start-run.ps1` is how a run starts.
- **Licence.** The project is GPL-3.0-or-later. Every new dependency is checked for compatibility and recorded in `NOTICE.md` before it is used.
- **No in-app updating and no Microsoft Store.** The app only tells the user a new version exists and opens the download page (decision D7).

Who writes and who reviews: Claude Code (`opus`) or Antigravity writes; Codex (GPT-6.2 Astra, read-only) reviews, as pinned in `.conclave/reviewers.toml`. The writer never reviews its own work.

## Goal

Ship DoubleTake, a free GPL-3.0 Windows desktop app that finds duplicate photos by visual hashing, lets the user review each group side by side in the Darkroom design, and moves the unwanted copies to the Recycle Bin.

## Working rules

- Verify files, routes, schemas, tools, and commands before relying on them. A path someone mentions is a hypothesis until it is on disk.
- Inspect existing patterns, imports, the package manager, the framework, and the test commands before editing. Do not infer architecture or tool schemas from memory when the repository can answer.
- Resolve a tool by capability before path. Prefer explicit config, then discovery, then a setup-required state. Store discovered paths only in ignored local config and never hardcode user-specific absolute paths.
- Prefer global or user-level tool installs. Add repo-scoped wrappers only when they encode project-specific behavior or reproducible commands.
- Real data only. Demo or seed data stays behind an explicit demo mode and is labeled as such.
- Run the relevant typecheck, lint, and tests after a change.
- Fix at the owning layer: a setting in its setting, behaviour in the code that produces it, data in the data. No output filters that hide a problem. Code changes end the report with a `Layer:` line.
- Markdown prose is never hard-wrapped: one line per paragraph and per list item. Every Markdown table row stays `<= 120` characters so raw `.md` files never wrap.
- Never use em dashes or en dashes anywhere: prose, code, comments, commit messages and generated files.
- Temporary files and full logs go to scratch, never the repository: `R:\scratch` on Windows, `/mnt/r/scratch` on WSL (the same folder), or the session scratchpad when one is given.

## Operating directive

How to work without waiting to be told. When to ask the operator is listed under Safety, and only there.

- A task assigned is a task authorised: do it, then report what was done, with the evidence.
- Never end a turn with a question or an offer when the next step is known and unblocked: take the step.
- Finish the follow-ups this session can do safely (a config value, a setup step, a check to run again) and report them done, never as a list left for the operator.
- Ask the operator only for what Safety lists: once, with the options and the one you recommend, and keep working on everything the answer does not change.
- Fix forward: a risk found later is filed as ordinary work that blocks nothing, and a red check is fixed at its cause, never skipped or bypassed.
- Build the simplest design that meets the request in full, and add a check, gate or prerequisite only for a failure that has happened or one that would lose data, spend money or expose something.
- An unattended run never asks the operator: it takes the industry-standard option, records the decision and what reversing it would cost in the run file and files an owner item; it halts only through the run's own pause mechanism, and pauses instead of proceeding only for data loss, a credential, shared infrastructure or a calculation that looks wrong.

## Safety

- Local reversible work in the repository needs no confirmation, and neither does work outside it that the task authorised and that can be undone (a config value, a setup step, a deploy the task asked for).
- Ask the operator once before anything that destroys or exposes something, or that needs business context the repository lacks: dropping or overwriting data, a force-push, deleting outside the repository, creating, rotating or exposing a credential, sending mail or a message to a person, a SQL write or a production change with real blast radius.
- When a command needs sudo, give the operator the exact command to run with `! sudo ...`. Never store the sudo password.
- Never print, log, or commit a secret value.

## Git

A project with a branch workflow replaces the first rule with its own; the others hold everywhere.

- Develop on the main branch: commit there, with no feature branch, unless the operator asks for a branch in that task.
- Before staging, read `git status --short` and enough of the diff to understand every dirty file: another session or a person may be editing.
- Commit a safe side change (small, not secret, not generated, not in conflict) with the next coherent commit; stop and say why before touching one that conflicts, holds a secret or looks unsafe or generated.
- Never discard changes with `git reset`, `checkout`, `restore` or `clean` unless asked for that exact cleanup.
- After a commit, confirm it landed with `git log --oneline -1` and `git status --short`, and never filter hook output in a way that hides an error.
- When work is finished, remove the worktrees you or a subagent created, delete branches that are merged or whose content is verifiably on main, and prune dead worktree records.
- Never delete an unmerged branch whose content is not verifiably on main without asking.

## Skills

- Antigravity skills live in `.agents/skills/<name>/`, Claude skills in `.claude/skills/<name>/`, and Codex skills in `.codex/skills/<name>/`, all as real files, never symlinks. Change all three together.
- Follow [Agent Skills and Rules Structure](./docs/agent-skills-and-rules-structure.md) before adding or moving skills.
- Name a skill for its capability, not with a project prefix.
- Each agent reads and runs only its own directory (`.agents/` for Antigravity, `.claude/` for Claude Code, `.codex/` for Codex) and never edits another agent's skills unless asked.

## Subagents

- Delegate mechanical subtasks to subagents. Claude subagents pin an explicit `model:`: Sonnet by default, and Opus (with a `model_rationale:`) only where judgment quality needs it.
- Subagents read and run; they never write. Every Claude subagent declares an explicit `tools:` list without Edit, Write, MultiEdit, NotebookEdit or `*`. The main loop makes every change and verifies what subagents return.
- Antigravity uses native `Orchestrator (Carbon)` (`gemini-pro-orchestrator`), which plans on Carbon (`<plan_execute_protocol>`), hands execution to Hydrogen via `exit_plan_mode`, manages its own effort (rejecting `--effort`), and provides built-in subagents (`self`, `research`, `image-generator`) without custom `.agents/agents/*.md` files or wrapper scripts. Codex has no subagent definitions: it runs mechanical subtasks in the main session.
- Haiku is only for near-mechanical work, at least 90% mechanical (read-only lookups, inventories, structural checks), whose output a script or the main loop verifies. Pin `claude-haiku-5-5` or later, declare `mechanical_share:` (90 to 100), point `haiku_replay:` at a record of a known-answer replay that showed no loss against Sonnet, and give it no edit tools. Never use Haiku for review, audit, research, security, debugging, diagnosis, planning or design.
- Run `node scripts/verify-agent-tiers.mjs` after adding or changing a Claude agent definition in `.claude/agents/`; it enforces these rules.

## TODO workflow

Plan and build through the TODO system: [docs/todo-workflow.md](./docs/todo-workflow.md).
