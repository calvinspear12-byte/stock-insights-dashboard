# Running this dashboard on ChatGPT (no Claude)

This dashboard is a plain website. It needs no Claude to run or to update its data.
It works on any device, including your Mac and iPhone (open the link in Safari and
tap Share > Add to Home Screen for an app-like icon).

## What updates by itself, free, in the cloud (no PC, no Claude, no AI)

Two GitHub Actions do this for free:

- **Update live prices** (`.github/workflows/prices.yml`): fetches current quotes a few
  times each trading day and writes `prices.json`. The page reads it live.
- **Daily data refresh** (`.github/workflows/daily-data.yml`): rebuilds the Kronos
  forecasts and the 2-year price history each weekday morning, straight into `index.html`.

Neither uses AI. They run on GitHub's servers whether your computer is on or off.

## What still needs a human (or, later, the ChatGPT API): the written analysis

The words, the stock picks, the theses, the "what's moving the market" list, and the
"Entry view" lines, are the only parts that need reasoning. Today you refresh those by
hand with ChatGPT. It takes about five minutes and can be done from your phone.

### Manual refresh with ChatGPT (free)

1. Open ChatGPT and paste the prompt in `chatgpt-refresh-prompt.txt` (also below).
2. ChatGPT returns three JavaScript snippets: `CANDS`, `UPCOMING`, and `ENTRY`.
3. On github.com, open `index.html`, click the pencil (Edit).
4. Find `const CANDS = [` ... `];` and replace it with ChatGPT's new `CANDS` block.
   Do the same for `const UPCOMING = [ ... ];` and `const ENTRY = { ... };`.
5. Also update the three "what is moving the market" bullet lines near the top if you like.
6. Commit. GitHub Pages redeploys in about a minute. Done.

Keep the shape of each object identical (same field names). The data pipelines and the
whole UI depend on those names.

## Later: let ChatGPT do the writing automatically (a few cents a day)

When you want the analysis to refresh with no copy-paste, add a third Action that calls
the OpenAI API to produce those same `CANDS` / `UPCOMING` / `ENTRY` blocks and commit them.
Skeleton lives in `ai-refresh.yml.example`. To turn it on:

1. Get an OpenAI API key (platform.openai.com). It is pay-as-you-go, roughly a few cents
   per run for this size of task.
2. In your repo: Settings > Secrets and variables > Actions > New repository secret,
   name it `OPENAI_API_KEY`.
3. Rename `ai-refresh.yml.example` to `.github/workflows/ai-refresh.yml`.

That is the full "ChatGPT takes over" switch. Until you flip it, the manual route above
keeps everything current for free.

## If you lose Claude access

Nothing breaks. The site keeps running and the two data Actions keep updating it. You use
ChatGPT for the written analysis, manually now or automatically via the API later. No step
in this document requires Claude.
