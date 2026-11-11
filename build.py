"""Build the POLISCI 1 weekly-module site from modules.toml into docs/ (GitHub Pages, served from /docs).

    python build.py              write docs/index.html (+ docs/materials/ for any linked local files)
    python build.py --check      validate modules.toml only, write nothing

modules.toml is the only content source; this script holds the page template, styles and checks. It stops with an
error, and writes nothing, when a check fails:
  - a week lacks n, start or title, weeks are out of order, or a start date is not a Monday
  - a link is neither an absolute http(s) URL nor an existing file under materials/
External links are checked separately: python check_links.py
Needs Python 3.11+ (tomllib); no other dependencies.
"""
import datetime as dt, html, pathlib, re, shutil, sys, tomllib

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "modules.toml"
LINKS = (("readings", "Readings"), ("slides", "Slides"), ("homework", "Homework"))
errors = []


def load():
    try:
        data = tomllib.loads(SRC.read_text(encoding="utf-8-sig"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        sys.exit(f"build: cannot read {SRC.name}: {e}")
    weeks, last, local = data.get("week", []), 0, []
    if not weeks:
        errors.append("modules.toml has no [[week]] entries")
    for w in weeks:
        tag = f"week {w.get('n', '?')}"
        missing = [k for k in ("n", "start", "title") if not w.get(k)]
        if missing:
            errors.append(f"{tag}: missing {', '.join(missing)}")
            continue
        if w["n"] <= last:
            errors.append(f"{tag}: weeks must be numbered in increasing order")
        last = w["n"]
        try:
            d = dt.date.fromisoformat(str(w["start"]))
            if d.weekday() != 0:
                errors.append(f"{tag}: start {d} is not a Monday")
            w["start"] = d
        except ValueError:
            errors.append(f"{tag}: start '{w['start']}' is not YYYY-MM-DD")
        for key, _ in LINKS:
            v = str(w.get(key, "")).strip()
            w[key] = v
            if v in ("", "none") or re.match(r"https?://\S+$", v):
                continue
            if v.startswith("materials/") and (ROOT / v).is_file():
                local.append(v)
            else:
                errors.append(f"{tag}: {key} '{v}' is not an http(s) URL or an existing materials/ file")
    return data, weeks, local


def link_cell(w, key, label):
    v = w[key]
    if v == "none":
        return f'<span class="chip off">{label}<small>none this week</small></span>'
    if not v:
        return f'<span class="chip soon">{label}<small>coming soon</small></span>'
    ext = ' target="_blank" rel="noopener"' if v.startswith("http") else ""
    return f'<a class="chip" href="{html.escape(v)}"{ext}>{label}<small>open</small></a>'


def week_label(w):
    return w.get("label") or f"Week {w['n']}"


def span(w):
    s, e = w["start"], w["start"] + dt.timedelta(days=4)
    fmt = lambda d: d.strftime("%b ") + str(d.day)
    return f"{fmt(s)}–{e.day}" if e.month == s.month else f"{fmt(s)} – {fmt(e)}"


def render(data, weeks):
    course, term = html.escape(data.get("course", "POLISCI 1")), html.escape(data.get("term", ""))
    jump = "\n".join(f'<a href="#week-{w["n"]}">{html.escape(w.get("label") or str(w["n"]))}</a>' for w in weeks)
    cards = []
    for w in weeks:
        sessions = "".join(f"<li>{html.escape(s)}</li>" for s in w.get("sessions", []))
        note = f'<p class="note">{html.escape(w["note"])}</p>\n' if w.get("note") else ""
        links = "".join(link_cell(w, k, lab) for k, lab in LINKS)
        cards.append(f"""<section class="module" id="week-{w['n']}" data-start="{w['start'].isoformat()}">
<p class="kicker">{html.escape(week_label(w))} · {span(w)}</p>
<h2>{html.escape(w['title'])}</h2>
<ul class="sessions">{sessions}</ul>
{note}<div class="links">{links}</div>
</section>""")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{course} · {term}</title>
{FONTS}
<style>{CSS}</style>
</head>
<body>
<header class="site">
<p class="eyebrow">Stanford University · {term}</p>
<h1>{course}</h1>
<p class="intro">One module per week. Each module links that week's readings, slides and homework as they are posted.</p>
</header>
<nav class="jump" aria-label="Jump to week"><div class="jump-inner">
<a class="now" id="jump-now" href="#week-{weeks[0]['n']}">Jump to this week</a>
<span class="jump-label">Week</span>
{jump}
</div></nav>
<main>
{chr(10).join(cards)}
<p class="provenance">{FOOTER}</p>
</main>
<script>{JS}</script>
</body>
</html>
"""


def main():
    data, weeks, local = load()
    if errors:
        for e in errors:
            print("ERROR:", e, file=sys.stderr)
        sys.exit(f"build: {len(errors)} error(s); nothing written")
    if "--check" in sys.argv[1:]:
        print(f"checked {len(weeks)} week(s)")
        return
    out = ROOT / "docs"
    out.mkdir(exist_ok=True)
    for stale in out.iterdir():                  # docs/ is generated: clear everything but .nojekyll
        if stale.name != ".nojekyll":
            shutil.rmtree(stale) if stale.is_dir() else stale.unlink()
    for f in local:
        (out / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / f, out / f)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "index.html").write_text(render(data, weeks), encoding="utf-8", newline="\n")
    for w in weeks:
        state = "  ".join(f"{k}:{'none' if w[k] == 'none' else 'link' if w[k] else 'soon'}" for k, _ in LINKS)
        print(f"  {week_label(w):<8} {w['start']}  {state}")
    print(f"wrote docs/index.html (+{len(local)} materials file(s))")


FOOTER = ("Maintained by the POLISCI 1 instructors, Stanford University. Drafted with AI assistance (Claude) and "
          "reviewed by the instructors before publication; every external link is checked before each update.")

# "Jump to this week" = the last module whose Monday is on or before today; before term starts it says Week 1.
JS = """
(function () {
  var mods = Array.prototype.slice.call(document.querySelectorAll('.module'));
  if (!mods.length) return;
  var today = new Date(); today.setHours(0, 0, 0, 0);
  var day = function (m) { var p = m.dataset.start.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); };
  var cur = mods[0];
  mods.forEach(function (m) { if (day(m) <= today) cur = m; });
  var a = document.getElementById('jump-now');
  a.href = '#' + cur.id;
  if (day(mods[0]) > today) { a.textContent = 'Jump to Week 1'; return; }
  cur.classList.add('current');
  var pill = document.querySelector('.jump a[href="#' + cur.id + '"]:not(.now)');
  if (pill) pill.setAttribute('aria-current', 'true');
})();
"""

FONTS = ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:ital,wght@0,400;0,600;'
         '0,700;1,400&amp;family=Source+Serif+4:wght@400;600&amp;display=swap">')
LIGHT = ("--bg:#fbf8f4; --surface:#ffffff; --fg:#161719; --muted:#62666c; --line:#e8e1da; "
         "--accent:#8c1515; --accent-soft:#f3e6e6; --on-accent:#ffffff; color-scheme:light;")
DARK = ("--bg:#16181b; --surface:#1f2226; --fg:#e6e8eb; --muted:#9aa3ad; --line:#30353b; "
        "--accent:#e0858a; --accent-soft:#3a2324; --on-accent:#16181b; color-scheme:dark;")
CSS = """
:root { %LIGHT%
  --font-heading:"Source Serif 4", Georgia, serif;
  --font-body:"Source Sans 3", system-ui, -apple-system, "Segoe UI", sans-serif; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { %DARK% } }
:root[data-theme="dark"] { %DARK% }
* { box-sizing:border-box; }
html { scroll-behavior:smooth; scroll-padding-top:4.5rem; }
body { margin:0; background:var(--bg); color:var(--fg); font:17px/1.55 var(--font-body); -webkit-text-size-adjust:100%; }
a { color:var(--accent); text-underline-offset:.15em; }
:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.site, main, .jump-inner { max-width:48rem; margin:0 auto; padding-inline:16px; }
.site { padding-top:2.5rem; }
.eyebrow { margin:0; color:var(--muted); font-size:.85rem; letter-spacing:.06em; text-transform:uppercase; }
h1, h2 { font-family:var(--font-heading); font-weight:600; line-height:1.2; text-wrap:balance; }
h1 { font-size:2.1rem; margin:.3rem 0 .6rem; }
.intro { margin:0 0 1rem; color:var(--muted); }
.jump { position:sticky; top:0; z-index:2; background:var(--bg); border-bottom:1px solid var(--line); }
.jump-inner { display:flex; flex-wrap:wrap; align-items:center; gap:.4rem; padding-block:.65rem; }
.jump a { display:inline-block; min-width:2.25rem; padding:.3rem .6rem; border:1px solid var(--line); border-radius:999px;
  background:var(--surface); color:var(--fg); text-align:center; text-decoration:none; font-size:.9rem; }
.jump a:hover, .jump a[aria-current] { border-color:var(--accent); color:var(--accent); }
.jump a.now { background:var(--accent); border-color:var(--accent); color:var(--on-accent); font-weight:600; margin-right:.5rem; }
.jump-label { color:var(--muted); font-size:.85rem; }
main { padding-block:1.5rem 4rem; }
.module { background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:1.1rem 1.25rem 1.2rem; margin:0 0 1rem; }
.module.current { border-color:var(--accent); box-shadow:inset 4px 0 0 var(--accent); }
.kicker { margin:0; color:var(--muted); font-size:.88rem; font-weight:600; letter-spacing:.03em; }
.module h2 { font-size:1.25rem; margin:.2rem 0 .5rem; }
.sessions { margin:0 0 .5rem; padding-left:1.1rem; }
.sessions li { margin:.15rem 0; }
.note { margin:.25rem 0 .6rem; color:var(--muted); font-size:.92rem; }
.links { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:.5rem; margin-top:.75rem; }
.chip { display:flex; flex-direction:column; padding:.55rem .75rem; border:1px solid var(--line); border-radius:8px;
  font-weight:600; text-decoration:none; color:var(--accent); background:var(--accent-soft); }
.chip small { font-weight:400; font-size:.8rem; color:var(--muted); }
a.chip:hover { border-color:var(--accent); }
.chip.soon, .chip.off { background:transparent; color:var(--muted); }
.chip.off { opacity:.6; }
.provenance { margin-top:2rem; color:var(--muted); font-size:.88rem; }
@media (max-width: 560px) {
  body { font-size:16px; }
  h1 { font-size:1.7rem; }
  .links { grid-template-columns:minmax(0, 1fr); }
}
@media print {
  :root, :root:not([data-theme="light"]), :root[data-theme="dark"] { %LIGHT% }
  .jump { position:static; }
}
""".replace("%LIGHT%", LIGHT).replace("%DARK%", DARK)


if __name__ == "__main__":
    main()
