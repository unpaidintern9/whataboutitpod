# What About It?

Responsive podcast website for What About It? with Morgan McGaughey.

Live site: https://whataboutitpod.vercel.app/

## Source

`index.html` is the complete standalone website. Photography, branding, and social icons are embedded, so no asset folder, framework, or package installation is required. Episode players and social links require internet access.

## Deployment

Vercel project: `whataboutitpod`

Owner workspace: `unpaidintern9s-projects`

The Vercel Git integration deploys production from `main`. Push website changes to `main` to publish them. A GitHub Actions workflow refreshes the shared Daily Proverb cache.

## Local preview

Run `python3 -m http.server 8000` in this folder, then open http://localhost:8000/ in a browser.

## Daily Proverb cache

The ticker reads `daily-proverb.json` from this website, never directly from the Bible API. The daily workflow fetches one NLT verse from Tyndale at approximately 12:07 AM Louisville time, then commits the shared cache to `main`; the Vercel Git integration publishes it. The day of the month selects the Proverbs chapter. GitHub scheduling and deployment can be delayed, so the ticker offers the NLT chapter link until the current cache is ready.

`scripts/cache_daily_proverb.py` skips the API request when that date is already cached, including manual reruns. A failed request leaves the last good file untouched. There is normally one provider request per day for the entire website; failed runs can be retried manually from Actions → Cache daily NLT proverb → Run workflow. Visitor page loads only request the shared JSON file. The workflow needs GitHub Actions enabled and permission to commit to `main`.

Tyndale's anonymous API is free for noncommercial use (https://api.nlt.to/). Caching does not change its license conditions; commercial use needs permission. Attribution is displayed on the page. No API key, paid storage, or new backend service is required.
