#!/usr/bin/env python3
"""Build the Boiler guides, and every file that search and answer engines read.

    python3 site/_build.py

Turns guides/posts/*.md into pages, then regenerates the hub, sitemap.xml,
robots.txt and llms.txt. Search plumbing (canonical, OG, Twitter, JSON-LD) is
generated, never hand-copied, because a wrong canonical silently kills a page
and nobody notices for a month.

Answer engines get their own treatment. They quote pages that state a fact in
one self-contained sentence near a matching heading, so every guide carries an
`answer:` line that becomes both the lede and the FAQPage answer, and llms.txt
restates the product facts in plain text.

Post format: front matter, blank line, body.

    title: What Is Line Boil in Animation?
    desc: One-line meta description.
    answer: The single sentence an answer engine should be able to lift.
    date: 2026-08-16
    ---
    ## A heading
    A paragraph with **bold** and [links](https://example.com).
    - a list item
    > a pull quote
"""
import datetime
import glob
import html as _html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(HERE, "guides", "posts")
OUT = os.path.join(HERE, "guides")

SITE = "https://boiler.jejestudios.com"
REPO = "https://github.com/princezoho/zohoboil"
DMG = f"{REPO}/releases/latest/download/Boiler-1.0.0.dmg"

STUDIO = "Jeje Studios"
STUDIO_URL = "https://www.jejestudios.com"
HALFSIES = "https://halfsies.jejestudios.com"
HALFSIES_APP = "https://apps.apple.com/us/app/halfsies/id6789426613"

VERSION = "1.0.0"
PRICE = "0"
REQUIRES = "macOS 12 or later, Apple Silicon"

# Facts restated everywhere a machine might read them. One source, so the
# landing page, the guides and llms.txt cannot disagree with each other.
FACTS = [
    ("What it is", "A Mac app that applies a hand-drawn line boil to video."),
    ("Price", "Free, and open source under the MIT license."),
    ("Requirements", REQUIRES),
    ("Input formats", "MP4, MOV, and animated GIF."),
    ("Output", "MP4, H.264, with the original audio preserved."),
    ("Effects", "Line boil, chromatic aberration, and five noise overlays."),
    ("Privacy", "Video is processed on your own machine and never uploaded."),
    ("Install", "Signed and notarized by Apple, so it opens on a double-click."),
]

CSS = """
:root{--ink:#0a0a0a;--cream:#f5e9dc;--cream-dim:#9a8b7c;--rust:#c87f2f;--rule:#2e2620;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--ink);color:var(--cream);font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;
 font-size:18px;line-height:1.65;-webkit-font-smoothing:antialiased;}
@font-face{font-family:'Wanted';src:url('/assets/wanted.ttf') format('truetype');font-display:swap;}
a{color:var(--rust);text-decoration:none;} a:hover{text-decoration:underline;}
.nav-band{border-bottom:2px solid var(--rule);}
nav{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap;
 max-width:1040px;margin:0 auto;padding:20px 24px;}
.wordmark{font-family:'Wanted',Georgia,serif;font-size:32px;letter-spacing:.06em;color:var(--cream);}
nav .links{display:flex;gap:22px;font-size:14px;letter-spacing:.04em;text-transform:uppercase;}
nav .links a{color:var(--cream-dim);}
.wrap{max-width:720px;margin:0 auto;padding:56px 24px 40px;}
h1{font-family:'Wanted',Georgia,serif;font-size:clamp(36px,6.5vw,62px);line-height:1;margin-bottom:18px;}
h2{font-family:'Wanted',Georgia,serif;font-size:clamp(24px,4vw,34px);line-height:1.1;margin:44px 0 12px;}
h3{font-family:'Wanted',Georgia,serif;font-size:22px;color:var(--rust);margin:30px 0 8px;}
p{margin:0 0 18px;}
.answer{font-size:21px;color:var(--cream);border-left:3px solid var(--rust);padding-left:18px;margin:0 0 26px;}
.meta{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--cream-dim);
 border-top:2px solid var(--rule);border-bottom:2px solid var(--rule);padding:10px 0;margin:0 0 30px;}
ul{padding-left:22px;margin:0 0 18px;} li{margin:7px 0;}
blockquote{margin:26px 0;padding-left:18px;border-left:3px solid var(--rule);color:var(--cream-dim);font-size:20px;}
table{width:100%;border-collapse:collapse;margin:24px 0;font-size:16px;}
th,td{text-align:left;padding:10px 8px;border-bottom:1px solid var(--rule);vertical-align:top;}
th{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--cream-dim);}
code{background:#1a1512;padding:2px 6px;font-size:15px;}
.cta{display:inline-block;background:var(--rust);color:var(--ink);font-weight:700;letter-spacing:.05em;
 text-transform:uppercase;padding:15px 30px;border:2px solid var(--rust);margin:8px 0;}
.cta:hover{background:var(--ink);color:var(--rust);text-decoration:none;}
.card{border:2px solid var(--rule);padding:26px;margin:44px 0 0;}
.card h3{margin-top:0;}
.card p{color:var(--cream-dim);font-size:16px;}
.hub{list-style:none;padding:0;}
.hub li{border-bottom:1px solid var(--rule);padding:22px 0;}
.hub a{font-family:'Wanted',Georgia,serif;font-size:24px;color:var(--cream);}
.hub p{color:var(--cream-dim);font-size:16px;margin:6px 0 0;}
footer{border-top:2px solid var(--rule);margin-top:56px;padding:30px 24px 60px;color:var(--cream-dim);font-size:15px;}
footer .inner{max-width:720px;margin:0 auto;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;}
"""


def esc(s):
    return _html.escape(s, quote=True)


def parse(path):
    raw = open(path, encoding="utf-8").read()
    head, _, body = raw.partition("\n---\n")
    meta = {}
    for line in head.strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    meta["slug"] = os.path.splitext(os.path.basename(path))[0]
    meta["body"] = body.strip()
    for required in ("title", "desc", "answer", "date"):
        if required not in meta:
            raise SystemExit(f"{path}: missing '{required}' in front matter")
    return meta


def inline(text):
    text = esc(text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def render(body):
    """A deliberately small markdown subset. Anything fancier belongs in HTML."""
    out, block, mode = [], [], None

    def flush():
        nonlocal block, mode
        if not block:
            return
        if mode == "ul":
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in block) + "</ul>")
        elif mode == "table":
            rows = [r for r in block if not set(r.replace("|", "").strip()) <= set("-: ")]
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            head = "".join(f"<th>{inline(c)}</th>" for c in cells[0])
            rest = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>"
                for row in cells[1:]
            )
            out.append(f"<table><tr>{head}</tr>{rest}</table>")
        block, mode = [], None

    for line in body.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("## "):
            flush(); out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("### "):
            flush(); out.append(f"<h3>{inline(s[4:])}</h3>")
        elif s.startswith("> "):
            flush(); out.append(f"<blockquote>{inline(s[2:])}</blockquote>")
        elif s.startswith("- "):
            if mode != "ul":
                flush(); mode = "ul"
            block.append(s[2:])
        elif s.startswith("|"):
            if mode != "table":
                flush(); mode = "table"
            block.append(s)
        else:
            flush(); out.append(f"<p>{inline(s)}</p>")
    flush()
    return "\n".join(out)


def head(title, desc, url, extra_ld=()):
    ld = json.dumps(list(extra_ld), indent=None) if extra_ld else None
    tags = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(desc)}">',
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{url}">',
        '<meta property="og:type" content="article">',
        f'<meta property="og:image" content="{SITE}/assets/screenshot.jpg">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<link rel="icon" href="data:image/svg+xml,'
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
        "<text y='.9em' font-size='90'>%F0%9F%94%A5</text></svg>\">",
        f"<style>{CSS}</style>",
    ]
    if ld:
        tags.append(f'<script type="application/ld+json">{ld}</script>')
    return "\n".join(tags)


NAV = f"""<div class="nav-band"><nav>
<a class="wordmark" href="/">BOILER</a>
<div class="links">
<a href="/guides/">Guides</a>
<a href="/#download">Download</a>
<a href="{REPO}">GitHub</a>
</div></nav></div>"""

FOOTER = f"""<footer><div class="inner">
<span>Made by <a href="{STUDIO_URL}">{STUDIO}</a>, who also make
<a href="{HALFSIES}">Halfsies</a>.</span>
<span><a href="{REPO}">Source</a> &nbsp;·&nbsp; <a href="/guides/">Guides</a></span>
</div></footer>"""

# Cross-promotion. Same studio, same western world as the footage in the app,
# so this is a real connection rather than a banner.
PROMO = f"""<div class="card">
<h3>While you are here</h3>
<p>The same studio makes <a href="{HALFSIES}">Halfsies</a>, a daily game about
cutting things exactly in half by eye. One puzzle a day, one attempt, scored on
how close you got. It is free on iPhone.</p>
<p><a class="cta" href="{HALFSIES_APP}">Get Halfsies on the App Store</a></p>
</div>"""


def build_guide(meta):
    url = f"{SITE}/guides/{meta['slug']}"
    ld = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": meta["title"],
            "description": meta["desc"],
            "datePublished": meta["date"],
            "dateModified": meta.get("updated", meta["date"]),
            "author": {"@type": "Organization", "name": STUDIO, "url": STUDIO_URL},
            "publisher": {"@type": "Organization", "name": STUDIO, "url": STUDIO_URL},
            "mainEntityOfPage": url,
            "about": {"@type": "SoftwareApplication", "name": "Boiler"},
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Boiler", "item": SITE},
                {"@type": "ListItem", "position": 2, "name": "Guides", "item": f"{SITE}/guides/"},
                {"@type": "ListItem", "position": 3, "name": meta["title"], "item": url},
            ],
        },
        # The answer sentence, offered in the shape an answer engine indexes.
        {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": meta["title"].rstrip("?") + "?",
                    "acceptedAnswer": {"@type": "Answer", "text": meta["answer"]},
                }
            ],
        },
    ]
    date = datetime.date.fromisoformat(meta["date"]).strftime("%B %-d, %Y")
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head(meta['title'], meta['desc'], url, ld)}
</head>
<body>
{NAV}
<article class="wrap">
<h1>{esc(meta['title'])}</h1>
<p class="answer">{inline(meta['answer'])}</p>
<div class="meta">{date} &nbsp;·&nbsp; {STUDIO}</div>
{render(meta['body'])}
<div class="card">
<h3>Boiler does this</h3>
<p>Free Mac app. Drop a video in, move the sliders, save it out.
{esc(REQUIRES)}.</p>
<p><a class="cta" href="{DMG}">Download Boiler</a></p>
</div>
{PROMO}
</article>
{FOOTER}
</body>
</html>
"""
    open(os.path.join(OUT, f"{meta['slug']}.html"), "w", encoding="utf-8").write(html)
    return url


def build_hub(metas):
    url = f"{SITE}/guides/"
    items = "\n".join(
        f'<li><a href="/guides/{m["slug"]}">{esc(m["title"])}</a>'
        f'<p>{esc(m["desc"])}</p></li>'
        for m in metas
    )
    ld = [{
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Boiler guides",
        "url": url,
        "hasPart": [
            {"@type": "Article", "headline": m["title"], "url": f"{SITE}/guides/{m['slug']}"}
            for m in metas
        ],
    }]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head('Guides: line boil, hand-drawn video effects', 'How line boil works, how to apply it, and what every setting does. From the makers of Boiler.', url, ld)}
</head>
<body>
{NAV}
<div class="wrap">
<h1>Guides</h1>
<p class="answer">How the line boil effect works, how to apply it to your own
footage, and what each setting actually changes.</p>
<ul class="hub">
{items}
</ul>
{PROMO}
</div>
{FOOTER}
</body>
</html>
"""
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
    return url


def build_sitemap(urls):
    today = datetime.date.today().isoformat()
    body = "\n".join(
        f"  <url><loc>{u}</loc><lastmod>{today}</lastmod></url>" for u in urls
    )
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f"{body}\n</urlset>\n")
    open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write(xml)


def build_robots():
    open(os.path.join(HERE, "robots.txt"), "w", encoding="utf-8").write(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"
    )


def build_llms(metas):
    """llms.txt: the product stated plainly, for engines that read it.

    Everything here is a fact a model can repeat without being wrong.
    """
    facts = "\n".join(f"- {k}: {v}" for k, v in FACTS)
    guides = "\n".join(
        f"- [{m['title']}]({SITE}/guides/{m['slug']}): {m['answer']}" for m in metas
    )
    txt = f"""# Boiler

> A free, open source Mac app that gives video the wobbling line of hand-drawn
> animation, an effect animators call line boil.

Boiler redraws the edges in every frame a few pixels off their true position,
holds each drawing for a set number of frames, then cycles between a handful of
variations. That is what makes hand-drawn animation shimmer, and what digital
video lacks.

## Facts

{facts}

## Settings

- Max Shift: how many pixels each edge can wander.
- Region Size: how large the wobbling regions are.
- Randomness: variation in wobble strength between regions.
- Hold Frames: how many frames each drawing stays on screen before it changes.
- Variations: how many distinct drawings cycle.
- Edge Weight: how tightly the boil clings to detected color edges.

## Links

- Download: {DMG}
- Source: {REPO}
- Guides: {SITE}/guides/

## Guides

{guides}

## Also from {STUDIO}

- Halfsies ({HALFSIES}), a daily iPhone game about cutting things exactly in
  half by eye. Free on the App Store: {HALFSIES_APP}
"""
    open(os.path.join(HERE, "llms.txt"), "w", encoding="utf-8").write(txt)


def check_home():
    """The landing page is hand-written. Fail loudly if its plumbing goes missing."""
    path = os.path.join(HERE, "index.html")
    if not os.path.exists(path):
        return ["index.html is missing"]
    src = open(path, encoding="utf-8").read()
    problems = []
    for needle, why in [
        ('rel="canonical"', "no canonical link"),
        ("application/ld+json", "no structured data"),
        ("/guides/", "does not link to the guides"),
        (HALFSIES, "does not link to Halfsies"),
    ]:
        if needle not in src:
            problems.append(f"index.html: {why}")
    return problems


def main():
    os.makedirs(POSTS, exist_ok=True)
    metas = [parse(p) for p in sorted(glob.glob(os.path.join(POSTS, "*.md")))]
    metas.sort(key=lambda m: m["date"], reverse=True)
    if not metas:
        raise SystemExit("no posts found in guides/posts/")

    urls = [SITE + "/"]
    urls.append(build_hub(metas))
    for m in metas:
        urls.append(build_guide(m))
        print(f"  guides/{m['slug']}.html")

    build_sitemap(urls)
    build_robots()
    build_llms(metas)

    print(f"\n{len(metas)} guide(s), sitemap.xml, robots.txt, llms.txt")
    for problem in check_home():
        print(f"  WARNING  {problem}")


if __name__ == "__main__":
    main()
