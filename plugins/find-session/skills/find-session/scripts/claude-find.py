#!/usr/bin/env python3
"""claude-find — search across all Claude Code sessions to locate which
project/terminal a conversation happened in.

Usage:
  claude-find <query> [query2 ...]      # all terms must match (AND), case-insensitive
  claude-find -i                        # interactive: list every session w/ title
  claude-find <query> --full <n>        # print n chars of context per hit (default 200)

Examples:
  claude-find sedia multipart
  claude-find "mouse jiggler"
  claude-find hetzner --full 400
"""
import sys, os, json, glob, re, argparse
from datetime import datetime

ROOT = os.path.expanduser("~/.claude/projects")

# ANSI
def c(s, code): return f"\033[{code}m{s}\033[0m" if sys.stdout.isatty() else s
BOLD, DIM, GRN, YEL, CYN, MAG = "1", "2", "32", "33", "36", "35"

def proj_from_dir(d):
    """Decode the dashified project path back to a readable cwd."""
    name = os.path.basename(d)
    # leading '-' is the root '/', rest are path separators-ish
    return name

def extract_text(obj):
    """Pull searchable text out of one JSONL event."""
    t = obj.get("type")
    if t == "queue-operation":
        return obj.get("content", "") or ""
    if t in ("ai-title",):
        return obj.get("aiTitle", "") or ""
    if t in ("last-prompt",):
        return obj.get("lastPrompt", "") or ""
    msg = obj.get("message")
    if isinstance(msg, dict):
        ctn = msg.get("content")
        if isinstance(ctn, str):
            return ctn
        if isinstance(ctn, list):
            parts = []
            for b in ctn:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text":
                    parts.append(b.get("text", ""))
                elif b.get("type") == "tool_result":
                    cc = b.get("content")
                    if isinstance(cc, str):
                        parts.append(cc)
                    elif isinstance(cc, list):
                        parts += [x.get("text", "") for x in cc if isinstance(x, dict)]
                elif b.get("type") == "tool_use":
                    parts.append(json.dumps(b.get("input", {}))[:2000])
            return "\n".join(parts)
    return ""

def scan(terms, full):
    terms_l = [t.lower() for t in terms]
    results = {}  # session file -> dict
    for f in glob.glob(os.path.join(ROOT, "*", "*.jsonl")):
        meta = {"file": f, "dir": os.path.dirname(f),
                "cwd": None, "branch": None, "title": None,
                "hits": [], "mtime": os.path.getmtime(f), "first_ts": None}
        try:
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    if meta["cwd"] is None and o.get("cwd"):
                        meta["cwd"] = o["cwd"]
                    if meta["branch"] is None and o.get("gitBranch"):
                        meta["branch"] = o["gitBranch"]
                    if o.get("type") == "ai-title":
                        meta["title"] = o.get("aiTitle")
                    if meta["first_ts"] is None and o.get("timestamp"):
                        meta["first_ts"] = o["timestamp"]
                    txt = extract_text(o)
                    if not txt:
                        continue
                    low = txt.lower()
                    if all(term in low for term in terms_l):
                        # snippet around first matching term
                        idx = min((low.find(t) for t in terms_l if low.find(t) >= 0),
                                  default=0)
                        start = max(0, idx - full // 2)
                        snip = txt[start:start + full].replace("\n", " ")
                        meta["hits"].append((o.get("type"), snip))
        except Exception:
            continue
        if meta["hits"]:
            results[f] = meta
    return results

def fmt_time(ts):
    if not ts:
        return "?"
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return ts[:16]

def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("query", nargs="*")
    ap.add_argument("-i", "--interactive", action="store_true")
    ap.add_argument("--full", type=int, default=200)
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()

    if a.help or (not a.query and not a.interactive):
        print(__doc__)
        return

    if a.interactive:
        rows = []
        for f in glob.glob(os.path.join(ROOT, "*", "*.jsonl")):
            cwd = title = ts = None
            try:
                with open(f, encoding="utf-8") as fh:
                    for line in fh:
                        try:
                            o = json.loads(line)
                        except Exception:
                            continue
                        if cwd is None and o.get("cwd"):
                            cwd = o["cwd"]
                        if o.get("type") == "ai-title":
                            title = o.get("aiTitle")
                        if ts is None and o.get("timestamp"):
                            ts = o["timestamp"]
            except Exception:
                continue
            rows.append((os.path.getmtime(f), cwd or os.path.basename(os.path.dirname(f)),
                         title or "(no title)", os.path.basename(f)[:8], ts))
        rows.sort(reverse=True)
        for mt, cwd, title, sid, ts in rows:
            print(f"{c(fmt_time(ts),DIM)}  {c(cwd,CYN)}")
            print(f"    {c(title,BOLD)}  {c(sid,DIM)}")
        return

    res = scan(a.query, a.full)
    if not res:
        print(c(f"No sessions matched: {' '.join(a.query)}", YEL))
        return
    ordered = sorted(res.values(), key=lambda m: m["mtime"], reverse=True)
    print(c(f"\n{len(ordered)} session(s) match {a.query}:\n", BOLD))
    for m in ordered:
        cwd = m["cwd"] or proj_from_dir(m["dir"])
        br = f"  ⎇ {m['branch']}" if m["branch"] else ""
        print(c(f"▶ {cwd}{br}", CYN))
        print(f"  {c(m['title'] or '(no title)', BOLD)}")
        print(c(f"  session {os.path.basename(m['file'])[:8]}  ·  "
                f"last active {fmt_time(datetime.fromtimestamp(m['mtime']).isoformat())}  ·  "
                f"{len(m['hits'])} hit(s)", DIM))
        for typ, snip in m["hits"][:3]:
            print(f"    {c(typ,MAG)}: …{snip.strip()}…")
        print()

if __name__ == "__main__":
    main()
