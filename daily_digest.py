#!/usr/bin/env python3
"""
AI Daily Digest
----------------
Generates a 150-item daily email: a mix of (1) real, current AI news/research
pulled via live web search, and (2) original AI-related concepts/ideas
brainstormed fresh each day. Sends the result as an HTML email via Gmail.

Runs unattended from GitHub Actions (see .github/workflows/daily-digest.yml).

Required environment variables / secrets:
    ANTHROPIC_API_KEY   - Anthropic API key
    GMAIL_ADDRESS       - sending Gmail address (e.g. slusarchuk.randy@gmail.com)
    GMAIL_APP_PASSWORD  - Gmail App Password for that address
    RECIPIENT_EMAIL     - where to send the digest (defaults to GMAIL_ADDRESS)

Config (optional env vars):
    NEWS_COUNT          - target count of real news items (default 50)
    CONCEPT_COUNT       - target count of brainstormed items (default 100)
    MODEL               - Anthropic model string (default claude-sonnet-5)
"""

import os
import json
import re
import smtplib
import sys
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import anthropic

MODEL = os.environ.get("MODEL", "claude-sonnet-5")
NEWS_COUNT = int(os.environ.get("NEWS_COUNT", "50"))
CONCEPT_COUNT = int(os.environ.get("CONCEPT_COUNT", "100"))

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_json_array(text: str):
    """Pull a JSON array out of a model response, tolerating code fences/preamble."""
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text.strip())
    text = re.sub(r"```$", "", text.strip())
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in model response")
    return json.loads(text[start:end + 1])


def get_final_text(response) -> str:
    """Concatenate all text blocks from a (possibly tool-using) response."""
    return "\n".join(block.text for block in response.content if block.type == "text")


# ---------------------------------------------------------------------------
# Part 1: Real, current AI news/research (web search grounded)
# ---------------------------------------------------------------------------

def fetch_real_news(count: int):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    system = (
        "You are a meticulous AI-industry news researcher. You use web search to find "
        "genuinely recent, real, verifiable items only. Never invent items. Never quote "
        "sources verbatim (15 words max per source, paraphrase everything else)."
    )
    prompt = f"""Today is {today}. Using web search, find {count} genuinely recent, real items
in the world of AI relevant to a technically engaged solo developer. Cover a mix of:
- New model/product releases and updates
- Notable research papers or breakthroughs
- AI security: newly disclosed vulnerabilities, defensive techniques, "protections"
  (informational/awareness only - never exploit code or attack instructions)
- Interesting new dev tools, libraries, or techniques
- Notable AI policy/industry developments

Search across several queries to cover different sub-topics before answering.

Respond with ONLY a JSON array (no preamble, no code fences) of exactly {count} objects,
each shaped like:
{{"category": "Model Release|Research|Security|Dev Tool|Industry", "title": "short title",
"summary": "1-2 sentence paraphrased summary in your own words", "source_url": "https://..."}}
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=8000,
        system=system,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        return extract_json_array(get_final_text(response))
    except Exception as e:
        print(f"[warn] Failed to parse real-news JSON: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Part 2: Original, freshly brainstormed AI concepts/ideas
# ---------------------------------------------------------------------------

def brainstorm_concepts(count: int):
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    system = (
        "You are a sharp, inventive AI concepts generator. You produce genuinely novel, "
        "specific, non-generic ideas - never vague platitudes. You never produce exploit "
        "code, malware, or attack instructions; 'hacks' means clever techniques/workarounds, "
        "not intrusion tools."
    )
    prompt = f"""Generate {count} original ideas for {today}, freshly brainstormed (not reused
from a known list). Spread across these buckets, roughly evenly:
- New AI app/product concepts
- Novel prompt-engineering or agent-workflow techniques
- Defensive security concepts / "protections" for AI systems and personal data
- Clever productivity "hacks" using AI (legitimate techniques, not intrusion tools)
- Speculative/future-facing AI concepts worth thinking about

Respond with ONLY a JSON array (no preamble, no code fences) of exactly {count} objects,
each shaped like:
{{"category": "App Concept|Technique|Protection|Hack|Speculative", "title": "short title",
"summary": "1-2 sentence description"}}
"""
    response = client.messages.create(
        model=MODEL,
        max_tokens=6000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        return extract_json_array(get_final_text(response))
    except Exception as e:
        print(f"[warn] Failed to parse brainstorm JSON: {e}", file=sys.stderr)
        return []


# ---------------------------------------------------------------------------
# Email rendering + sending
# ---------------------------------------------------------------------------

def render_html(news_items, concept_items):
    today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    total = len(news_items) + len(concept_items)

    def render_section(title, items, accent):
        rows = ""
        for i, item in enumerate(items, 1):
            cat = item.get("category", "")
            headline = item.get("title", "")
            summary = item.get("summary", "")
            link = item.get("source_url")
            link_html = f'<div style="margin-top:4px;"><a href="{link}" style="color:{accent};font-size:12px;">source</a></div>' if link else ""
            rows += f"""
            <tr>
              <td style="padding:14px 16px;border-bottom:1px solid #222;">
                <div style="font-size:11px;letter-spacing:1px;color:{accent};text-transform:uppercase;margin-bottom:4px;">{cat}</div>
                <div style="font-size:15px;color:#eaeaea;font-weight:600;">{i}. {headline}</div>
                <div style="font-size:13px;color:#aaa;margin-top:4px;line-height:1.4;">{summary}</div>
                {link_html}
              </td>
            </tr>"""
        return f"""
        <tr><td style="padding:20px 16px 8px;font-size:18px;color:{accent};font-weight:700;letter-spacing:1px;">{title} ({len(items)})</td></tr>
        {rows}
        """

    html = f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#0a0a0a;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;padding:20px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="background:#111214;border:1px solid #222;">
  <tr><td style="padding:24px 20px;border-bottom:2px solid #00e5ff;">
    <div style="font-size:22px;color:#00e5ff;font-weight:800;letter-spacing:1px;">AI DAILY DIGEST</div>
    <div style="font-size:13px;color:#888;margin-top:4px;">{today} &middot; {total} items</div>
  </td></tr>
  {render_section("REAL AI NEWS", news_items, "#00e5ff")}
  {render_section("NEW CONCEPTS & IDEAS", concept_items, "#ff8c00")}
  <tr><td style="padding:18px 20px;color:#555;font-size:11px;border-top:1px solid #222;">
    Generated automatically &middot; AI Daily Digest
  </td></tr>
</table>
</td></tr>
</table>
</body></html>"""
    return html


def send_email(html_body: str, item_count: int):
    sender = os.environ["GMAIL_ADDRESS"]
    recipient = os.environ.get("RECIPIENT_EMAIL", sender)
    app_password = os.environ["GMAIL_APP_PASSWORD"]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"AI Daily Digest - {datetime.now(timezone.utc).strftime('%b %d, %Y')} ({item_count} items)"
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender, app_password)
        server.sendmail(sender, recipient, msg.as_string())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Fetching {NEWS_COUNT} real news items...")
    news_items = fetch_real_news(NEWS_COUNT)
    print(f"  -> got {len(news_items)}")

    print(f"Brainstorming {CONCEPT_COUNT} original concepts...")
    concept_items = brainstorm_concepts(CONCEPT_COUNT)
    print(f"  -> got {len(concept_items)}")

    total = len(news_items) + len(concept_items)
    if total == 0:
        print("No content generated - aborting send.", file=sys.stderr)
        sys.exit(1)

    html = render_html(news_items, concept_items)
    send_email(html, total)
    print(f"Sent digest with {total} items.")


if __name__ == "__main__":
    main()
