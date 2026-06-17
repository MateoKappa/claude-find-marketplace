# mateokappa-tools — Claude Code plugin marketplace

Plugins for Claude Code.

## find-session

Find which past Claude Code session, project, or terminal a conversation happened in by searching what you remember about it. Searches all local session transcripts (`~/.claude/projects/*/*.jsonl`) and returns the project path, git branch, session title, and matching snippets — ranked newest-first.

Just ask Claude in natural language:

- "which project did I set up Stripe webhooks in?"
- "find the session where I debugged that auth redirect loop"
- "what terminal did I run the database migration in"

Three ways to find a session, matched to how much you remember:

| You remember… | How it searches |
|---------------|-----------------|
| Exact words | AND match across all transcripts |
| Only a vague description | OR + synonym expansion, ranked by relevance |
| The project, not the words | Scopes to that repo and scans the **file names** each session touched — finds it even when the title is misleading |

## Install

In any Claude Code session:

```
/plugin marketplace add MateoKappa/claude-find-marketplace
/plugin install find-session@mateokappa-tools
```

Then enable when prompted (or `/plugin enable find-session@mateokappa-tools`).

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
