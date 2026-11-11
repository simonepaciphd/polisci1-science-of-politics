# POLISCI 1 · The Science of Politics · session guide

Public, student-facing pages for POLISCI 1 (Stanford, Winter 2027): what to prepare before each lecture and what to review after it.
Site: https://simonepaciphd.github.io/polisci1-science-of-politics/ (GitHub Pages, served from `docs/`).

Same system as the POLISCI 158 session guide (`simonepaciphd/polisci158-ai-politics`).

## Maintaining

```
sessions/sNN-slug.md    one file per session, the only content source (template: sessions/_TEMPLATE.md)
build.py                sessions/ -> docs/ (public) or _preview/ (--preview, drafts included)
check_links.py          checks every external link; run before each publish
slides/sNN-slides.html  optional approved class deck (speaker notes stripped); its presence approves publication
docs/                   generated site; do not edit by hand
```

The schedule and session titles live in `SCHEDULE` and `TITLES` at the top of `build.py`. They follow the draft
Winter 2027 sequence (17 lectures; midterm Wed Feb 3; no class Jan 18 or Feb 15). Update both when the sequence changes.

Weekly cycle, per session:

1. **Prep.** Draft or revise `sessions/sNN-*.md`, set `status: prep` once approved by the instructors.
2. `python check_links.py sNN` (no DEAD links; open MANUAL ones in a browser), then `python build.py`.
3. Commit `sessions/` and `docs/` together; push.
4. **Review.** After the session, fill in "After class", set `status: reviewed`, repeat steps 2-3.

`status: draft` pages never reach `docs/`; moving a page back to draft removes it on the next build.
`build.py` refuses to write when a linked item lacks a `<!-- from: ... -->` provenance comment, when public text cites
a restricted source (Canvas-only material, unpublished work, local files), or when template text is left in.

Requires Python 3.9+, pandoc 3.x, beautifulsoup4, and Quarto 1.10+ (only once a session is published).
