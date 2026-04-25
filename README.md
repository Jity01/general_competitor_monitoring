# Competitor Intel Skill Generator

Generate a personalized **competitor-intelligence Claude skill** for your product. Point it at your website, run one command, and you get a `SKILL.md` you can drop into Claude Cowork as a scheduled task — it'll email you a weekly digest of what your competitors, adjacent players, and likely customers are doing.

It's the generic version of [the skill that ships Starsling's weekly intel](https://ci.starsling.dev) — same structure, but the Tier 1 competitors, ICP watchlist, space queries, and product context are researched fresh for whatever URL you feed in.

## How it works

1. You put your product URL + an Anthropic API key in `.env`.
2. `python generate.py` runs Claude with web search + web fetch enabled. It reads your site, infers the space, finds direct and adjacent competitors, builds an ICP watchlist, and writes `SKILL.md`.
3. You upload that `SKILL.md` to Cowork and wire up a scheduled task that emails the digest via Resend (instructions below).

One-time generation. The skill itself is what runs on the recurring schedule — you don't need to re-run `generate.py` unless your product or space changes meaningfully.

---

## Step 1 — Generate your skill

```bash
git clone <repo-url>
cd general_competitor_monitoring
cp .env.example .env
# edit .env: paste your ANTHROPIC_API_KEY (https://console.anthropic.com/settings/keys)
#           and WEBSITE_URL (your product's homepage)
pip install -r requirements.txt
python generate.py
```

Takes 1–3 minutes. Costs roughly **$0.30–$1.00** in Anthropic credits per generation (Opus 4.7 + web search). If you'd rather go cheaper, swap `MODEL = "claude-opus-4-7"` for `MODEL = "claude-sonnet-4-6"` in `generate.py` — Sonnet is ~5x cheaper and still good at this kind of research.

When it finishes, you'll have a `SKILL.md` in the repo root. **Open it and skim it** — read the Product Context, Tier 1 list, and ICP watchlist. The model gets it ~90% right; the last 10% is your judgment. Edit anything that's wrong.

---

## Step 2 — Set up Resend (for sending the email)

1. Sign up for [Resend](https://resend.com). **Remember which email you sign up with** — that's the only address the digest can deliver to (unless you verify a custom domain later).
2. Create an API key at [resend.com/api-keys](https://resend.com/api-keys).

---

## Step 3 — Upload the skill to Cowork

1. In Cowork's skills area, upload the `SKILL.md` you just generated. It'll appear in your skills list as `competitor-intel-digest`.

2. **Allowlist `api.resend.com`.** Cowork's sandbox blocks outbound HTTP by default. Without this step, the digest will research and write `digest.md` fine, but the email-send will fail with `X-Proxy-Error: blocked-by-allowlist`. Go to **Settings → Capabilities → Allow network egress** and add `api.resend.com`.

---

## Step 4 — Schedule the task

In Cowork, click **+ New task** (top left) or type `/schedule`.

**Name:**
```
{Your Product} Intel Digest
```

**Prompt:** (swap in your real key + email — the email must match the Resend signup email)
```
Before doing anything else, set these two environment variables for this session (use `export` in a bash step):

  RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
  EMAIL_TO=you@example.com

Then run the competitor-intel-digest skill. Produce today's intelligence digest following the format defined in the skill — deep-research the Tier 1 entities, lightly scan Tier 2, check current customers + ICP watchlist for signals, and actively surface emerging players. Save the final digest to a file named digest.md in the current working directory. Finally, run the Python email-send snippet at the bottom of the skill to deliver it via Resend.
```

**Schedule:** weekly, whatever time you like. Click **Schedule**.

**Trigger a manual run** from the Scheduled tasks page to verify. You should get an email within ~30 seconds of the final step.

---

## Tuning your skill

Open `SKILL.md` and edit it whenever the picture changes — new competitor, new customer, new sub-space worth watching. Re-upload to Cowork (it replaces the old version). The scheduled task re-reads the skill on every run, so changes take effect immediately.

---

## Troubleshooting

- **`X-Proxy-Error: blocked-by-allowlist`** — Cowork's sandbox refused the call to Resend because `api.resend.com` isn't on the network allowlist. Go to **Settings → Capabilities → Allow network egress** and add it.
- **`You can only send testing emails to your own email address`** — `EMAIL_TO` doesn't match the email you used to sign up for Resend. Line them up. Or verify a domain at [resend.com/domains](https://resend.com/domains) and change the `"from"` field in the Send the Report block of `SKILL.md`.
- **`HTTP 403 ... error code: 1010`** — Cloudflare bot-challenged the outbound request. The skill sets a `User-Agent` header to avoid this; if it's still happening, something stripped the header.
- **Digest produced but no email arrived** — Claude may have skipped the final Python snippet. Check that `RESEND_API_KEY` and `EMAIL_TO` were exported before the snippet ran, and that the snippet printed a response with an `"id"` field. Proxy errors → see the first item.
- **`generate.py` says "could not find <SKILL>...</SKILL>"** — the model didn't wrap its output in markers. Run again; if it persists, check that your Anthropic account has web tools enabled.
- **Tool-name errors from `generate.py`** — Anthropic occasionally bumps the version date on `web_search`/`web_fetch`. Update the names in `generate.py` to match the [current docs](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/web-search-tool).

---

## Why a generated skill instead of a generic one?

A generic "monitor my competitors" skill burns tokens on noise — it doesn't know what you care about. The generated `SKILL.md` is hand-customized: it knows which 2–3 things would make you sit up vs which are FYI, who your closest threats are, who's on your ICP, what hiring signals to watch. That's what makes the digest a **one-page read** instead of a 5-page wall of text.

You can — and should — keep editing it.

---

Open source — issues + PRs welcome at `<repo-url>`.
