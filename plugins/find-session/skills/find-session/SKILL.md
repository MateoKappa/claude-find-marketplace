---
name: find-session
description: Find which past Claude Code session, project, or terminal a conversation happened in by searching the content the user remembers. Use when the user says things like "which project did I work on X in", "find the session where I discussed Y", "what terminal did I run that Claude session", "search my old Claude chats for Z", "I don't remember which project had ...". Searches all local session transcripts and returns the project path, git branch, session title, and matching snippets.
metadata:
  author: mateokappa
  version: "1.0.0"
---

# Find Session

Locate a past Claude Code conversation across all projects/terminals by searching what the user remembers about it.

## When to use

Trigger when the user wants to find a previous session but doesn't recall which project or terminal it was in. Example phrasings:
- "which project did I set up the SEDIA API in?"
- "find the Claude session where I discussed the jiggler server"
- "what terminal did I run that migration in"
- "search my old chats for the airtable thing"

## How it works

Claude Code stores every session as a JSONL transcript under `~/.claude/projects/<dashified-cwd>/<session-id>.jsonl`. Each event carries `cwd`, `gitBranch`, an `aiTitle`, and the message text. The bundled script searches all of them.

## How to run

Run the bundled script with the user's remembered keywords as arguments:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-$CLAUDE_SKILL_DIR}/skills/find-session/scripts/claude-find.py" <term1> [term2 ...]
```

`$CLAUDE_PLUGIN_ROOT` is set when this runs as an installed plugin; `$CLAUDE_SKILL_DIR` when run as a bare skill (in which case the script is at `$CLAUDE_SKILL_DIR/scripts/claude-find.py`). If neither resolves, use the absolute path to this skill's `scripts/claude-find.py`.

Guidelines:
- Pull the most distinctive nouns from the user's request as search terms (e.g. project names, tech, unusual words). Multiple terms = AND match.
- If the user gives a vague request, run with 1–2 strong keywords first, then narrow.
- Results are ranked newest-first and show: project path, git branch, session title, session id, and matching snippets.
- To browse everything instead of searching: `python3 .../claude-find.py -i`
- For more snippet context: append `--full 400`.

## Reporting back

Summarize the top matches for the user in plain language: which **project / folder** each match is in, its **session title**, when it was **last active**, and a one-line snippet of why it matched. Lead with the most likely answer. If only one project matches, just name it directly.
