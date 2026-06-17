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
python3 "$CLAUDE_SKILL_DIR/scripts/claude-find.py" <term1> [term2 ...]
```

If `$CLAUDE_SKILL_DIR` is not set, use the absolute path to this skill's `scripts/claude-find.py`.

Pick the search mode based on what the user gives you:

**A. They remember exact words → AND search (default).**
Pull the distinctive terms (project names, tech, unusual words) and pass them directly:
`... claude-find.py sedia multipart`
All terms must appear. Results are newest-first.

**B. They DESCRIBE the session in their own words → `--any` search.**
This is the important case. The user's words may not match the transcript's words, so YOU bridge the gap: expand their description into a broad set of candidate keywords and synonyms — 4–10 terms covering different ways the topic could have been written — and pass them with `--any`:

> User: "find where I overlaid multiple projects on one graph to compare them"
> You run: `... claude-find.py --any compare overlay chart graph projects "multi-series" line area`

`--any` matches sessions containing ANY term and **ranks by relevance** (term coverage + title match + hit count), so the best-fitting session floats to the top even if no single word was guaranteed. Each result shows a `score` and `N/M terms`.

Then **read the top 3–5 results and judge** which one actually matches the user's description — don't just echo the #1 score. Use the titles and snippets to decide, and say which you're confident about. If nothing fits, broaden the synonyms and run `--any` again.

**C. They name a PROJECT/repo but not the words → `--project` scope.**
Often the strongest signal. Session titles can be misleading (a landing-page redesign might be titled "tv-mode-progress-timeline"), and the work may never use the user's vocabulary in prose — but the **file names** do. When the user mentions a project ("...on precon", "in the dashboard repo"):

> User: "where I was making multiple versions of a landing page on precon"
> You run: `... claude-find.py --project precon`

With no query, `--project` lists that repo's sessions newest-first **and the files each one wrote/edited**. A line like `files: version-four.tsx×15, version-two.tsx×14` reveals the session even when the title and message text don't. Then narrow if needed: `--project precon --any landing mockup hero version`.

**Rule of thumb:** if the user names a project, ALWAYS try `--project <name>` first — scanning file paths beats guessing synonyms. Combine modes freely: `--project`, `--any`, and plain terms all stack.

Other flags:
- `-i` — browse every session (project + title); add `--project` to scope.
- `--full 400` — more snippet context per hit.

## Reporting back

Summarize the top matches for the user in plain language: which **project / folder** each match is in, its **session title**, when it was **last active**, and a one-line snippet of why it matched. Lead with the most likely answer. If only one project matches, just name it directly.
