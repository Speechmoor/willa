#!/usr/bin/env python3
"""Cache the Small Claims Court reference pages for offline use.

    python scripts/fetch_reference.py

Writes data/reference.json, read by the in-app Guide, FAQ and court-finder.
Run it while online; everything after that works offline.

The pages are cached rather than linked. An outbound link would tell
justice.gov.za that a particular person is preparing a claim, and
scripts/check_egress.py cannot detect it because the browser makes that
request rather than the application.

Text is reproduced as published, with its source URL and retrieval date,
rather than rewritten.
"""

from __future__ import annotations

import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config  # noqa: E402

OUT = config.DATA_DIR / "reference.json"
UA = "Willa-POC/0.1 (legal aid research tool; contact: local)"

SOURCES = {
    "guide": {
        "title": "Guide to the Small Claims Court",
        "url": "https://www.justice.gov.za/scc/scc.htm",
        "anchor": "Guide",
    },
    "faq": {
        "title": "Frequently asked questions",
        "url": "https://www.justice.gov.za/scc/scc_info.htm",
        "anchor": None,
    },
    "courts": {
        "title": "Find your court",
        "url": "https://www.justice.gov.za/contact/lowercourts_full.html?scc=1",
        "anchor": None,
    },
}

ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.I | re.S)
CELL = re.compile(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", re.I | re.S)
BLOCK = re.compile(r"<(h[1-4]|p|li|tr)\b[^>]*>(.*?)</\1>", re.I | re.S)
TAG = re.compile(r"<[^>]+>")
WS = re.compile(r"\s+")

"""Site furniture to discard.

Every page on justice.gov.za carries the department's masthead, a sidebar of
quick links, and a footer. Flattened into text those become a list of
unexplained words — "Tenders", "Jobs", "Newsroom" — sitting above the content
the reader actually asked for, and on the FAQ page the sidebar even repeats
the page's own title back at them.

Matching is on exact text, not on position or CSS class. Position is fragile
because the department's templates differ between the /scc/ pages and the
/contact/ one; class names are worse, because they change without notice and
fail silently when they do. An exact-match list is blunt but it is legible,
and when it goes stale the symptom is one stray line rather than a page that
has quietly lost half its content.

Deliberately NOT dropped when it appears as a heading: "Frequently Asked
Questions" and "Small Claims Court Guide" are real headings on their own
pages as well as sidebar links, so the filter below is applied to list items
only. Dropping them everywhere would decapitate the page.
"""
NAV_LABELS = {
    # masthead
    "dojcd", "about us", "resources", "newsroom", "courts", "tenders",
    "jobs", "contacts", "contact us", "home", "back", "top", "next",
    "previous", "search", "sitemap", "disclaimer", "privacy policy",
    # SCC sidebar / quick links
    "quick links", "forms", "frequently asked questions",
    "guidelines for commissioners & clerks",
    "guidelines for commissioners and clerks",
    "legislation", "list of scc courts", "small claims court guide",
    "videos", "small claims courts", "small claims court",
    "compliance with small claims court tariffs",
    # Second masthead row and footer nav, reported after the first pass.
    "links", "branches", "faqs", "faq", "media statements", "speeches",
    "reports", "newsletters", "events", "terms & conditions",
    "terms and conditions", "vacancies", "gallery", "photo gallery",
    "videos & photos", "browse", "site map",
}

# Sentences to drop, matched on how each opens because the tails vary. The
# last four are controls from the court list's interactive filter — a
# search box, a spreadsheet download, a notices link.
BOILERPLATE = (
    "enquiries/complaints",
    "please contact your nearest provincial office",
    "for more information regarding the small claims courts",
    "© department of justice",
    "copyright",
    "nr of courts",
    "type to filter courts",
    "download the list as an excel spreadsheet",
    "please check the operational notices",
    "only show small claims courts",
)

# Site name, to be trimmed off the <title> tag.
DEPT_BITS = re.compile(
    r"department of justice|constitutional development|dojcd|justice\.gov\.za"
    r"|republic of south africa|^south africa$|^doj",
    re.I)
TITLE_TAG = re.compile(r"<title\b[^>]*>(.*?)</title>", re.I | re.S)
SPLIT = re.compile(r"\s*(?:\||»|>|::|–|—)\s*|\s+-\s+")


def clean(fragment: str) -> str:
    return WS.sub(" ", html.unescape(TAG.sub(" ", fragment))).strip()


def page_title(markup: str) -> tuple[str, str]:
    """The page's own name, from its <title> tag.

    Taken from <title> rather than from the first heading in the body, because
    on these pages the first heading is not a name. On the guide it is "Small
    Claims Courts offer a quicker and easier way of resolving certain civil
    disputes..." and on the FAQ it is a full sentence in capitals. Those are
    body text that happens to be marked up as a heading, and using them would
    put a paragraph in the menu.

    Returns (cleaned, raw). The raw form is kept and printed so that when the
    trimming below gets it wrong — and eventually it will, because it is
    guessing at how one department formats one tag — the mistake is visible
    rather than silently becoming a menu label.
    """
    m = TITLE_TAG.search(markup)
    if not m:
        return "", ""
    raw = clean(m.group(1))
    parts = [p.strip() for p in SPLIT.split(raw) if p.strip()]
    kept = [p for p in parts if not DEPT_BITS.search(p)]
    # Longest surviving segment: on a "Site - Section - Page" title the page
    # name is the most specific thing left, and first/last ordering is not
    # consistent between these three pages.
    return (max(kept, key=len) if kept else raw), raw


def is_chrome(kind: str, text: str) -> bool:
    """Is this navigation furniture rather than content?

    Applies to every kind of block, not just list items. An earlier version
    checked list items only, on the theory that headings would be page titles
    worth keeping. In the actual markup "DoJCD" is a paragraph and both
    "Small Claims Courts" and "Quick Links" are headings, so that exemption
    protected exactly the three lines it needed to remove. The page's real
    name now comes from <title>, so nothing in the body needs protecting.
    """
    low = text.lower().strip(" ·:•-–—")
    if low.startswith(BOILERPLATE):
        return True
    return low in NAV_LABELS


def blocks(markup: str, title: str = "") -> list[dict]:
    """Flatten the page into headings, paragraphs and table rows.

    Rows are kept whole. The court list is a table of court name against
    province and address, and lifting each cell out as its own list item —
    which the first version did — severs exactly the association a reader
    needs. "Soweto", "Gauteng" as two bullets is worse than useless: it reads
    as two separate courts.

    `title` is the page's own name. Any block repeating it is dropped, so the
    name appears once — printed by the app from the stored title — rather than
    twice, once from us and once from the body.
    """
    seen_title = title.lower().strip()
    out: list[dict] = []
    for m in BLOCK.finditer(markup):
        kind = m.group(1).lower()

        if kind == "tr":
            cells = [clean(c) for c in CELL.findall(m.group(2))]
            cells = [c for c in cells if c]
            if not cells:
                continue
            text = " · ".join(cells)
        else:
            text = clean(m.group(2))

        norm = ("h" if kind.startswith("h") else
                "li" if kind in ("li", "tr") else "p")

        if len(text) < 3 or is_chrome(norm, text):
            continue
        if seen_title and text.lower().strip() == seen_title:
            continue

        out.append({"kind": norm, "text": text})

    # Collapse runs of identical lines — the courts table repeats headers.
    deduped: list[dict] = []
    for b in out:
        if deduped and deduped[-1] == b:
            continue
        deduped.append(b)

    # A heading with nothing under it is a section whose body was all chrome —
    # "Quick Links" survives the filter above as a heading, then has all six of
    # its links stripped, and would otherwise be left standing over nothing.
    pruned: list[dict] = []
    for i, b in enumerate(deduped):
        if b["kind"] == "h":
            nxt = next((x for x in deduped[i+1:] if x["kind"] != "h"), None)
            following_h = deduped[i+1] if i+1 < len(deduped) else None
            if nxt is None or (following_h and following_h["kind"] == "h" and
                               b["text"].lower() in NAV_LABELS):
                continue
        pruned.append(b)
    return pruned


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8", errors="replace")


def main() -> int:
    payload = {"fetched": date.today().isoformat(), "sections": {}}
    failures = 0

    for key, spec in SOURCES.items():
        print(f"Fetching {spec['url']}")
        try:
            markup = fetch(spec["url"])
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {type(exc).__name__}: {exc}")
            failures += 1
            continue
        title, raw = page_title(markup)
        # spec["title"] is now only a fallback, for a page with no <title>.
        title = title or spec["title"]
        body = blocks(markup, title)

        payload["sections"][key] = {
            "title": title,
            "title_raw": raw,
            "fallback_title": spec["title"],
            "source": spec["url"],
            "blocks": body,
        }
        print(f"  title: {title!r}")
        if raw and raw != title:
            print(f"    (from <title>: {raw!r})")
        print(f"  {len(body)} block(s)")

    if not payload["sections"]:
        print("\nNothing fetched. data/reference.json left untouched.")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"\nWritten to {OUT}")

    print("\nThese three titles are what the menu will show:\n")
    for key, sec in payload["sections"].items():
        print(f"  {key:7} {sec['title']}")
    print("\nThey come straight from each page's <title> tag with the")
    print("department's name trimmed off. If one of them reads badly, the")
    print("untrimmed original is kept alongside it in the JSON as title_raw.")

    print("\nThis is a snapshot, not a feed. Re-run before a release — the")
    print("monetary limit changed on 1 August 2026 and nothing noticed for")
    print("two weeks.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
