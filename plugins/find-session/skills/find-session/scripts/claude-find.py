#!/usr/bin/env python3
"""claude-find — search across all Claude Code sessions to locate which
project/terminal a conversation happened in.

Usage:
  claude-find <query> [query2 ...]      # all terms must match (AND), case-insensitive
  claude-find --any <t1> <t2> ...       # OR mode: match ANY term, rank by relevance
  claude-find -i                        # interactive: list every session w/ title
  claude-find <query> --full <n>        # print n chars of context per hit (default 200)

AND vs --any:
  Use AND (default) when you remember exact words ("sedia multipart").
  Use --any when you can only DESCRIBE the session — pass many synonyms and
  candidate keywords; sessions are ranked so the best fit floats to the top
  even though no single word is guaranteed to appear.

Examples:
  claude-find sedia multipart
  claude-find "mouse jiggler"
  claude-find --any compare overlay chart projects graph multi-series
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

def scan(terms, full, any_mode):
    """Search every transcript.

    AND mode (default): a line must contain ALL terms to count.
    OR mode (--any):    a line counts if it contains ANY term; sessions are
                        then ranked by relevance so a loose, described query
                        still surfaces the best-fitting session first.

    Relevance score per session =
        (# distinct query terms seen anywhere) * 10   <- coverage dominates
      + 5 if any term appears in the AI title       <- title is a strong signal
      + min(total line hits, 20) * 0.2              <- light recency-of-topic boost
    """
    terms_l = [t.lower() for t in terms]
    results = {}  # session file -> dict
    for f in glob.glob(os.path.join(ROOT, "*", "*.jsonl")):
        meta = {"file": f, "dir": os.path.dirname(f),
                "cwd": None, "branch": None, "title": None,
                "hits": [], "mtime": os.path.getmtime(f), "first_ts": None,
                "matched_terms": set(), "title_match": False}
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
                        tl = (o.get("aiTitle") or "").lower()
                        if any(t in tl for t in terms_l):
                            meta["title_match"] = True
                    if meta["first_ts"] is None and o.get("timestamp"):
                        meta["first_ts"] = o["timestamp"]
                    txt = extract_text(o)
                    if not txt:
                        continue
                    low = txt.lower()
                    present = [t for t in terms_l if t in low]
                    matched = bool(present) if any_mode else len(present) == len(terms_l)
                    if matched:
                        meta["matched_terms"].update(present)
                        idx = min((low.find(t) for t in present), default=0)
                        start = max(0, idx - full // 2)
                        snip = txt[start:start + full].replace("\n", " ")
                        meta["hits"].append((o.get("type"), snip))
        except Exception:
            continue
        if meta["hits"]:
            meta["score"] = (len(meta["matched_terms"]) * 10
                             + (5 if meta["title_match"] else 0)
                             + min(len(meta["hits"]), 20) * 0.2)
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
    ap.add_argument("--any", dest="any_mode", action="store_true",
                    help="OR mode: match ANY term, rank by relevance (for loose/described queries)")
    ap.add_argument("--full", type=int, default=200)
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()

    if a.help or (not a.query and not a.interactive):
        print(__doc__)
        return

    if not os.path.isdir(ROOT):
        print(c(f"No Claude Code history found at {ROOT} — nothing to search.", YEL))
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

    res = scan(a.query, a.full, a.any_mode)
    if not res:
        hint = "" if a.any_mode else "  (try --any for a looser, ranked search)"
        print(c(f"No sessions matched: {' '.join(a.query)}{hint}", YEL))
        return
    # OR mode → rank by relevance score; AND mode → newest first (terms already all matched)
    if a.any_mode:
        ordered = sorted(res.values(), key=lambda m: (m["score"], m["mtime"]), reverse=True)
        mode = "ranked by relevance"
    else:
        ordered = sorted(res.values(), key=lambda m: m["mtime"], reverse=True)
        mode = "newest first"
    print(c(f"\n{len(ordered)} session(s) match {a.query} ({mode}):\n", BOLD))
    for m in ordered:
        cwd = m["cwd"] or proj_from_dir(m["dir"])
        br = f"  ⎇ {m['branch']}" if m["branch"] else ""
        print(c(f"▶ {cwd}{br}", CYN))
        print(f"  {c(m['title'] or '(no title)', BOLD)}")
        score = (c(f"score {m['score']:.1f}  ·  ", GRN)
                 + c(f"{len(m['matched_terms'])}/{len(a.query)} terms  ·  ", DIM)
                 if a.any_mode else "")
        print(c("  ", DIM) + score + c(
                f"session {os.path.basename(m['file'])[:8]}  ·  "
                f"last active {fmt_time(datetime.fromtimestamp(m['mtime']).isoformat())}  ·  "
                f"{len(m['hits'])} hit(s)", DIM))
        for typ, snip in m["hits"][:3]:
            print(f"    {c(typ,MAG)}: …{snip.strip()}…")
        print()

if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # downstream pipe (e.g. `| head`) closed early — exit quietly
        try:
            sys.stdout.close()
        except Exception:
            pass
        os._exit(0)
    except KeyboardInterrupt:
        os._exit(130)
