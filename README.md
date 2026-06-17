# mateokappa-tools — Claude Code plugin marketplace

Plugins for Claude Code.

## find-session

Find which past Claude Code session, project, or terminal a conversation happened in by searching what you remember about it. Searches all local session transcripts (`~/.claude/projects/*/*.jsonl`) and returns the project path, git branch, session title, and matching snippets — ranked newest-first.

Just ask Claude in natural language:

- "which project did I set up the SEDIA API in?"
- "find the session where I discussed the jiggler server"
- "what terminal did I run that migration in"

## Install

In any Claude Code session:

```
/plugin marketplace add mateokappa/claude-find-marketplace
/plugin install find-session@mateokappa-tools
```

Then enable when prompted (or `/plugin enable find-session@mateokappa-tools`).

> Replace `mateokappa/claude-find-marketplace` with the actual `owner/repo` once pushed to GitHub.

## What's inside

```
.claude-plugin/marketplace.json        # catalog
plugins/find-session/
  .claude-plugin/plugin.json           # plugin manifest
  skills/find-session/
    SKILL.md                           # trigger + instructions
    scripts/claude-find.py             # the search tool (no deps, Python 3)
```

## License

MIT
