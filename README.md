# POLISCI 1 · The Science of Politics · course site

Public, student-facing page for POLISCI 1 (Stanford, Winter 2027): one module per week, each linking that week's
readings, slides and homework. Sticky "Jump to this week" button plus a week-by-week jump bar.
Site: https://simonepaciphd.github.io/polisci1-science-of-politics/ (GitHub Pages, served from `docs/`).

## Maintaining

```
modules.toml     one [[week]] block per week, the only content source (format notes at the top of the file)
materials/       optional local files to publish (e.g. materials/w03-slides.pdf); link them by that path
build.py         modules.toml -> docs/index.html (+ docs/materials/); python build.py --check validates only
check_links.py   checks every external link; run before each publish (python check_links.py 2 3 = weeks 2-3)
docs/            generated site; do not edit by hand
```

To post a week's material: put its URL (or `materials/...` path) in `readings`, `slides` or `homework`; leave `""`
for "coming soon" or write `"none"` for "none this week". Then `python check_links.py`, `python build.py`,
commit `modules.toml`, `materials/` and `docs/` together, and push.

The schedule follows the draft Winter 2027 sequence (17 lectures; midterm Wed Feb 3; no class Jan 18 or Feb 15;
homework weeks 2, 3, 4, 6, 7, 8, 9 as in Fall 2026). Update `modules.toml` when the sequence changes.

Requires Python 3.11+ (standard library only).
