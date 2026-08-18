#!/usr/bin/env python3
"""Tell the search engines this site changed, instead of waiting to be crawled.

    python3 site/_indexnow.py

Run this AFTER deploying and aliasing. It reads the live sitemap, so URLs that
are not yet serving would be submitted and then 404 for the crawler.

IndexNow is a push protocol supported by Bing, Yandex, Seznam and Naver. Google
does not participate, so this complements Search Console rather than replacing
it. Bing is worth more than its search share implies, because several AI answer
engines are built on its index.

The key file must stay reachable at https://<host>/<key>.txt or submissions are
rejected. That is the whole authentication scheme: proving you can write to the
domain you are claiming.
"""
import json
import re
import sys
import urllib.error
import urllib.request

KEY = "d0345b2d905d09455a3c28d2e9b77f0d"
HOST = "boiler.jejestudios.com"
ENDPOINT = "https://api.indexnow.org/IndexNow"


def main():
    xml = urllib.request.urlopen(f"https://{HOST}/sitemap.xml", timeout=30).read().decode()
    urls = re.findall(r"<loc>([^<]+)</loc>", xml)
    if not urls:
        sys.exit("no URLs in the sitemap; is the site deployed?")

    key_url = f"https://{HOST}/{KEY}.txt"
    served = urllib.request.urlopen(key_url, timeout=30).read().decode().strip()
    if served != KEY:
        sys.exit(f"{key_url} does not serve the key; submissions would be rejected")

    payload = {"host": HOST, "key": KEY, "keyLocation": key_url, "urlList": urls}
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f"submitted {len(urls)} URLs, HTTP {r.status}")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} {e.reason}: {e.read().decode()[:300]}")


if __name__ == "__main__":
    main()
