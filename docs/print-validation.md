# PR #1 print regression checks

Base: `9b2dd5f2ee0c4e593bd57fbde52ea0232edc6015` (current main checked on 2026-09-18).
PR #1 was already merged on 2026-09-16. This is a local follow-up patch, not a merge.

## Review disposition

- Explicit medium importance overriding legacy high tier: already fixed; retain the existing regression and add missing-importance fallback coverage.
- Impact horizon in the print overview: already fixed in the renderer; regenerate the stale checked-in preview.
- Unbounded summary, evidence titles and daily action: still present on main. Bound all print prose and disclose that this edition is an excerpt. Markdown/mobile retain full text.
- Partial-feed coverage warnings: still absent from print. Build one warning in `node_render` and pass it into the first printed page, including empty editions.
- Preview drift: regenerate via the existing script and compare both checked-in previews against fresh generation in a temporary directory.

## Print behavior

Keep the existing two-page split and font sizes. Tighten spacing, allow long Latin tokens to wrap, and use smaller per-field excerpt budgets so five long stories, optional history and coverage warnings fit together. Every excerpt uses an ellipsis when shortened. The footer directs readers to the full Markdown/mobile edition.

The physical layout gate uses Chromium, A4, CSS margins of 12 mm, 100% scale and Noto Sans SC. It checks both page count and visible content; counting HTML page containers alone cannot detect clipping. Other browsers, substituted fonts or user print-scale overrides need separate verification.

## Reproduce

```sh
uv sync --locked --extra dev
uv run python scripts/render_email_preview.py
uv run pytest -q
uv run mypy src
git diff --check
```

The optional browser suite requires Playwright, Chromium, pypdf and a Chinese font such as Noto Sans SC. It is skipped when the Python browser/PDF dependencies are absent; that skip is not layout verification.

```sh
uv run --extra dev --with playwright --with pypdf python -m playwright install chromium
uv run --extra dev --with playwright --with pypdf pytest tests/test_print_layout.py -q
```

For an existing Chromium binary, set `CHROMIUM_EXECUTABLE=/absolute/path/to/chromium`.

Browser cases: checked-in preview; zero, one and five stories with failed feeds; five simultaneous oversized Chinese fields; and mixed Chinese/long Latin fields. Stress cases include prior-report updates. Assertions cover two physical PDF pages, footer and text bounds, source links for every story, the coverage warning and the daily action. PDFs are written only into pytest's temporary directory for inspection.

No feeds, model APIs, publishing workflows or email delivery are invoked by these tests.

## Local result (2026-09-18)

- 421 tests passed, including all six physical-layout cases (Chromium 153, Noto Sans SC).
- `mypy src`: no issues in 13 source files.
- Generated preview and mixed-text stress PDF visually inspected; no clipping or footer overlap.
- Both preview files were regenerated; mobile preview stayed byte-identical, print preview changed.
- No remote branch, PR, review-thread state or publication was changed.
