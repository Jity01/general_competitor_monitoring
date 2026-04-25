#!/usr/bin/env python3
"""Generate a customized competitor-intel-digest SKILL.md from a product website URL.

Reads ANTHROPIC_API_KEY and WEBSITE_URL from .env, calls the Anthropic API with
web_search + web_fetch enabled, and writes the resulting skill to ./SKILL.md.
"""
import os
import re
import sys
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    sys.exit("error: `anthropic` package not installed. Run `pip install -r requirements.txt`.")

MODEL = "claude-opus-4-7"  # swap to "claude-sonnet-4-6" if you want cheaper runs
ROOT = Path(__file__).resolve().parent


def load_env():
    env_path = ROOT / ".env"
    if not env_path.exists():
        sys.exit("error: .env not found. Run `cp .env.example .env` and fill it in.")
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


SYSTEM = """You are a skill generator. Your job: given a product website, research the product and the space it competes in, then output a single Claude skill (SKILL.md) that — when run as a scheduled task in Claude Cowork — produces a weekly competitor-intelligence digest tailored to that product and emails it via Resend.

You have web_search and web_fetch tools. Use them aggressively:
1. Fetch the homepage, /about, /pricing, /blog (or equivalents) to understand the product, its wedge, target customer, public customer logos.
2. Web-search the space to identify Tier 1 direct competitors (companies solving the exact same problem) and Tier 2 adjacent players (neighbors that could become competitors, integrators, or acquirers).
3. Find named customers if any are public.
4. Build an ICP watchlist of likely buyers based on stack / stage / segment.
5. Generate space-search queries the operator can use to scan for new entrants each run.

Then write SKILL.md by replicating the structural reference below. Replace ALL Starsling-specific content with content for the user's product. Keep the Process / Report Format / Send the Report / Rules sections intact (they're product-agnostic), with these substitutions:
- Frontmatter `description:` — describe the user's product, not Starsling's
- The skill title (e.g. `# {Product} Competitor Intelligence Digest`)
- The Product Context block — based on what you researched
- Tier 1, Tier 2, Customers (current + ICP), Space queries — replace wholesale
- The "Special for X" notes in Process step 1 — adapt to whatever the category leaders / unique-wedge calls are for this product
- The synthesize prompts in Process step 5 — adapt to what counts as a "Top Signal" for this product
- The example summary line and the Top Signals fallback example in Report Format
- In the Send the Report Python block: change the email subject `"Starsling Intel Digest"` to `"{Product} Intel Digest"` and the User-Agent `"starsling-intel-digest/1.0"` to a kebab-case version of the product name. Leave the rest of the Python block byte-identical.

STRUCTURAL REFERENCE (this is the format — replicate the structure exactly, with content substituted):

<TEMPLATE>
{template}
</TEMPLATE>

Output ONLY the final SKILL.md content, wrapped in <SKILL>...</SKILL> tags. Nothing before or after. No commentary, no preamble, no postamble."""


def main():
    load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    url = os.environ.get("WEBSITE_URL", "").strip()

    if not api_key or "..." in api_key:
        sys.exit("error: set ANTHROPIC_API_KEY in .env to a real key (sk-ant-...).")
    if not url or "example.com" in url:
        sys.exit("error: set WEBSITE_URL in .env to your product's URL.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    template = (ROOT / "template.md").read_text()
    system_prompt = SYSTEM.replace("{template}", template)
    user_msg = (
        f"Generate the SKILL.md for the product at: {url}\n\n"
        "Research thoroughly using web_search and web_fetch (start by fetching the homepage), "
        "then emit only <SKILL>...</SKILL>."
    )

    client = Anthropic(api_key=api_key)
    print(f"Researching {url} and generating SKILL.md — takes 1–3 minutes...", flush=True)

    response = client.messages.create(
        model=MODEL,
        max_tokens=32000,
        system=system_prompt,
        tools=[
            {"type": "web_search_20250305", "name": "web_search", "max_uses": 30},
            {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 20},
        ],
        extra_headers={"anthropic-beta": "web-fetch-2025-09-10"},
        messages=[{"role": "user", "content": user_msg}],
    )

    text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
    m = re.search(r"<SKILL>(.*?)</SKILL>", text, re.DOTALL)
    if not m:
        sys.exit(
            f"error: could not find <SKILL>...</SKILL> markers in response.\n"
            f"stop_reason={response.stop_reason}\n\nRaw text:\n{text[:2000]}"
        )

    skill = m.group(1).strip() + "\n"
    out = ROOT / "SKILL.md"
    out.write_text(skill)
    print(f"\nSKILL.md written ({len(skill):,} bytes). Next: follow README.md to set up Resend and Cowork.")


if __name__ == "__main__":
    main()
