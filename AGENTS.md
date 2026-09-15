# AI News Agent

## Purpose
- Build the daily AI digest locally with an agent.
- Publish the final issue through GitHub Actions so the issue author is `app/github-actions`.

## Preferred Agent Flow
1. `UV_CACHE_DIR=.uv-cache uv sync --locked`
2. `uv run python src/main.py --check-issue --issue-status-file digest-issue-status.json`
3. Stop if `digest-issue-status.json` says `ok: true` and `exists: true`.
4. Stop if it says `ok: false` and `retryable: false`.
5. If it says `ok: false` and `retryable: true`, continue.
6. `RSS_MAX_WORKERS=2 RSS_TIMEOUT=15 uv run python src/main.py --candidates-only --status-file digest-run-status.json`
7. If `digest-run-status.json` says `feed_fetch_failed` or `empty_snapshot_with_feed_errors`, retry once with `RSS_MAX_WORKERS=1 RSS_TIMEOUT=20`.
8. If the retry still fails, stop and report the failure reason.
9. If status is healthy, write `digest-decisions.json` using the repo decision schema.
10. `uv run python src/main.py --apply-decisions digest-decisions.json`
11. `uv run python src/main.py --dispatch-publish`
12. Wait briefly, then re-run `--check-issue` to confirm the issue exists.

## Defaults
- Prefer the agent path above for daily runs.
- Do not use `uv run python src/main.py` for the daily automation path unless explicitly asked. That is the repo's default graph path and may use the repo LLM API path.
- `--publish-issue` is a manual fallback only.
- `--dispatch-publish` is the normal final publish path.
- `--dispatch-publish` needs workflow-dispatch-capable GitHub auth through authenticated local `gh`, or through `DIGEST_GITHUB_TOKEN`, `GITHUB_TOKEN` / `GH_TOKEN` in CI-style environments.
- For local Codex automation, use authenticated local `gh`; if it fails with 401, re-authenticate `gh` instead of switching the runbook to direct publish.

## Status Artifacts
- `digest-run-status.json`: feed health and candidate export status.
- `digest-issue-status.json`: issue existence or GitHub preflight status.
- `digest-candidates.json`: grouped candidate snapshot.
- `digest-decisions.json`: agent editorial decisions.
- `news.md`: rendered digest body.

## Decision Shape
- For the full input contract, inspect the current `digest-candidates.json`, including `decision_guidance`, and the decision-schema section in [docs/development.md](docs/development.md). `keep_id`, `duplicate_ids`, `off_topic_ids`, and `top_stories` refer to candidate `item_id` values such as `g1i1`, never the article's `id` or `link`.
- Choose cluster categories from the snapshot's top-level `categories` list, not the candidate item's category (which may be `All`).
- Copy candidate `snapshot_id` exactly into decisions schema v2 with kind `ai-news-agent.decisions`.
- Include every candidate group exactly once and disposition every item exactly once as keep, duplicate, or off-topic.
- Represent every distinct kept item, including `discovery_only`, as an explicit singleton cluster with `duplicate_ids: []`.
- `--apply-decisions` invalidates any existing `news.md` before validation. If it exits nonzero, stop and do not run `--dispatch-publish`.
- If binding or exhaustive validation fails, stop before dispatch; never repair the decisions with local passthrough.
- `clusters`: duplicate groups with `keep_id` and `duplicate_ids`
- `top_stories`: omit or use `[]` for automatic selection; otherwise supply unique strings naming your requested `keep_id` values, before internal promotion. Duplicate/off-topic IDs, URLs, and malformed values are rejected.
- `executive_summary`
- `off_topic_ids`

## Generated Files
- Treat `digest-candidates.json`, `digest-decisions.json`, `digest-run-status.json`, `digest-issue-status.json`, `news.md`, and `news.html` as generated local artifacts.
- Do not commit them unless explicitly asked.

## Troubleshooting
- If candidate export fails, inspect `digest-run-status.json` first.
- Check `digest-run-status.json.feed_errors` first for sample feed failures before looking elsewhere.

## Chinese Top 5 fork
- This fork targets `xudaniel/ai-news-agent`. Never publish to the upstream author's repository.
- Defaults: `DIGEST_FORMAT=top5-zh`, `DIGEST_TIMEZONE=Asia/Shanghai`.
- Read `docs/editorial-policy.md` before making daily editorial decisions. Each kept cluster
  must include Chinese `facts`, `why_it_matters`, `watchpoint`, `event_date` (or `未明确`),
  `relevance` (`投资`/`产品`/`监管`) and a source-supported Chinese `event_status`.
- Use `previous_report_date` with `what_changed` only when earlier coverage is supplied;
  never invent history. Keep `executive_summary` to one Chinese sentence.
- The Chinese renderer writes `news.md` and `news.html` with the same editorial content.
  Do not send the preview or publish a second edition without authorization.
- At most five independent events. The renderer omits the longer category list.
- Existing direct Gmail delivery is an external scheduled task. This repo's optional Actions
  path publishes public GitHub Issues; do not claim it sends through Gmail directly.
- Do not enable `ENABLE_GITHUB_DIGEST` while the external task is sending the same digest
  unless the user requests both. Never copy personal email addresses or credentials into Git.
