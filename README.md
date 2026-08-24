# AI Daily Digest

Sends a 150-item daily email to slusarchuk.randy@gmail.com: ~50 real, web-searched
current AI news items + ~100 freshly brainstormed original AI concepts/ideas/protections/hacks.
Fully automated via GitHub Actions, same pattern as Lotto Oracle.

## Setup (one time)

1. Create repo `ranslu/ai-daily-digest`, push these files.
2. In repo Settings -> Secrets and variables -> Actions, add:
   - `ANTHROPIC_API_KEY` - your Anthropic API key
   - `GMAIL_ADDRESS` - slusarchuk.randy@gmail.com
   - `GMAIL_APP_PASSWORD` - Gmail App Password (Google Account -> Security -> App Passwords;
     same one used for Lotto Oracle if you want to reuse it)
   - `RECIPIENT_EMAIL` - slusarchuk.randy@gmail.com (optional, defaults to GMAIL_ADDRESS)
3. Done. Runs daily at 13:00 UTC (~7am Edmonton). Trigger a test run anytime from the
   Actions tab -> "AI Daily Digest" -> "Run workflow".

## Tuning

Edit env vars in the workflow file or repo Variables to change:
- `NEWS_COUNT` / `CONCEPT_COUNT` - split between real news and brainstormed items (default 50/100)
- `MODEL` - Anthropic model string (default `claude-sonnet-5`)

## Notes

- The script never generates exploit code or attack instructions. "Hacks" = clever
  legitimate techniques; "Security/Protections" = informational awareness, not attack tooling.
- Cron is fixed UTC, so the local Edmonton send time shifts by 1 hour across DST changes.
