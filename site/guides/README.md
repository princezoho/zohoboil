# The Boiler guides

One command turns `posts/*.md` into the whole search surface.

```bash
python3 site/_build.py
cd site && npx vercel deploy --prod --yes
npx vercel alias set <printed-url> boiler.jejestudios.com
python3 _indexnow.py            # after the alias, never before
```

**The alias step is not optional.** The `boiler` Vercel project has no git
connection and the domain is attached by alias, so pushing to GitHub publishes
nothing and a deploy without an alias leaves the domain on the old build while
the new one 200s on its `vercel.app` URL.

## Writing a guide

Create `posts/your-slug.md`. The slug becomes the URL.

```
title: What Is Line Boil in Animation?
desc: The meta description. One sentence, under 160 characters.
answer: The single sentence an answer engine should be able to lift.
date: 2026-08-16
---
## A heading
A paragraph with **bold**, `code`, and [links](https://example.com).
- a list item
> a pull quote
| Column | Column |
| --- | --- |
| cell | cell |
```

All four front matter fields are required. The build fails loudly if one is
missing, rather than shipping a page with no description.

### The `answer` field carries the weight

It appears as the lede under the headline and as the `acceptedAnswer` in
FAQPage structured data. Answer engines quote a self-contained sentence that
sits near a matching heading, so write it to survive being lifted out of the
page with no surrounding context. "It depends on the footage" is worthless.
"Set Hold Frames to 2 so each drawing lasts two frames at 24fps" is quotable.

## What the build generates

| File | Contents |
| --- | --- |
| `guides/<slug>.html` | The page, with canonical, OG, Twitter, Article + Breadcrumb + FAQPage JSON-LD |
| `guides/index.html` | The hub, with CollectionPage JSON-LD |
| `sitemap.xml` | Every URL, with today as lastmod |
| `robots.txt` | Open, pointing at the sitemap |
| `llms.txt` | The product stated plainly for answer engines |

`index.html` at the site root is hand-written and is **not** generated. The
build checks it for a canonical, structured data, a guides link and a Halfsies
link, and prints a warning if any is missing.

## Facts live in one place

`FACTS` in `_build.py` feeds `llms.txt`. If the version, price, or system
requirements change, edit that list, rebuild, and update the matching
JSON-LD in `index.html`. Two sources of truth is how a site ends up telling
an answer engine the app costs money.

## Cross-promotion

Every guide carries a Halfsies card, and the landing page has a studio
section. Both are generated from constants at the top of `_build.py`
(`HALFSIES`, `HALFSIES_APP`), so a changed link is a one-line edit.

## Getting crawled

`_indexnow.py` pushes every sitemap URL to IndexNow, which Bing, Yandex, Seznam
and Naver consume. Run it after the alias step, because it reads the live
sitemap and would otherwise hand the crawlers URLs that are not serving yet.

Google does not support IndexNow. For Google the sitemap is already submitted
in Search Console, and the only accelerant is URL Inspection then Request
Indexing, which is manual and capped at roughly ten URLs a day.

The key file `d0345b2d905d09455a3c28d2e9b77f0d.txt` must keep serving its own
name at the site root. That file is the entire authentication scheme, so
deleting it silently breaks submissions.
