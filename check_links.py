"""Check every external link in modules.toml.

    python check_links.py            all weeks
    python check_links.py 2 3        only weeks 2 and 3

Exit 1 when a link is dead (404/410, DNS failure, connection refused, timeout).
Links a site refuses to automated clients (401/403/429, some 5xx) are listed as MANUAL: open them in a browser
before publishing. Nothing is written except the report printed to stdout.
"""
import concurrent.futures as cf, pathlib, socket, ssl, sys, tomllib, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"
MANUAL_CODES = {401, 403, 405, 406, 429, 500, 502, 503, 520, 521, 522, 999}


def urls(prefixes):
    """External links in modules.toml, keyed by URL -> weeks that use them (prefixes: week numbers to keep)."""
    data = tomllib.loads((ROOT / "modules.toml").read_text(encoding="utf-8-sig"))
    found = {}
    for w in data.get("week", []):
        if prefixes and str(w.get("n")) not in prefixes:
            continue
        for key in ("readings", "slides", "homework"):
            u = str(w.get(key, "")).strip()
            if u.startswith(("http://", "https://")):
                found.setdefault(u, []).append(f"week {w.get('n')} {key}")
    return found


def probe(url):
    ctx = ssl.create_default_context()
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
                return "OK", r.status, r.geturl()
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (400, 403, 404, 405, 429, 500, 501, 503):
                continue                         # many servers mishandle HEAD; retry with GET
            return ("DEAD" if e.code in (404, 410) else "MANUAL" if e.code in MANUAL_CODES else "DEAD"), e.code, url
        except (urllib.error.URLError, socket.timeout, ConnectionError, ssl.SSLError) as e:
            if method == "HEAD":
                continue
            return "DEAD", str(getattr(e, "reason", e))[:60], url
    return "DEAD", "no response", url


def main():
    found = urls(sys.argv[1:])
    with cf.ThreadPoolExecutor(8) as ex:
        results = dict(zip(found, ex.map(probe, found)))
    dead = 0
    for u, (state, code, final) in sorted(results.items(), key=lambda kv: kv[1][0]):
        moved = f"  -> {final}" if final.rstrip("/") != u.rstrip("/") else ""
        print(f"{state:<6} {code!s:<5} {u}{moved}   [{', '.join(sorted(set(found[u])))}]")
        dead += state == "DEAD"
    manual = sum(1 for s, _, _ in results.values() if s == "MANUAL")
    print(f"\n{len(results)} link(s): {len(results) - dead - manual} ok, {manual} manual, {dead} dead")
    sys.exit(1 if dead else 0)


if __name__ == "__main__":
    main()
