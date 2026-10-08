# CLAUDE.md

## Priority #1: save tokens
- Do the least work that finishes the task. Don't re-read files already read, re-derive settled facts, or explore beyond what the task needs.
- Prefer targeted reads (`grep`, line ranges) over whole-file dumps; never dump large data files whole.
- Batch independent tool calls in one turn. No subagents unless asked.
- Keep replies short: result first, no narration of options not taken.
- Keep this file short — it is loaded into every session.

## Project
AI Daily Digest: GitHub Actions job that emails a daily digest (~50 web-searched AI news items + ~100 brainstormed AI concepts) generated with the Anthropic API.
- `daily_digest.py`: generates and sends the email (Gmail SMTP). Deps: `requirements.txt` (`anthropic`).
- `.github/workflows/daily-digest.yml`: runs daily 13:00 UTC (~7am Edmonton) and on manual dispatch. Secrets: `ANTHROPIC_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, optional `RECIPIENT_EMAIL`. Tunables: `NEWS_COUNT`, `CONCEPT_COUNT`, `MODEL`.
- Any change to the Anthropic calls: use the `token-caching` skill.

## Reference
- LLM token/prompt-caching cost notes: `.claude/skills/token-caching/SKILL.md` (loaded on demand via the `token-caching` skill).
