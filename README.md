# What About It?

Responsive podcast website for What About It? with Morgan McGaughey.

Live site: https://whataboutitpod.com/

## Source

`index.html` is the complete standalone website. Photography, branding, and social icons are embedded, so no asset folder, framework, or package installation is required. Episode players and social links require internet access.

## Deployment

Vercel project: `whataboutitpod`

Production owner workspace: `morg5` (project `prj_p7VJShHv6X4Qei4WniRO5Y157JTd`).

Production is deployed separately from the repository. Website code changes must be deployed to the existing `morg5` project; a push to `main` alone does not publish them to whataboutitpod.com. A GitHub Actions workflow refreshes the shared Daily Proverb cache, which the browser reads directly from the public repository.

## Local preview

Run `python3 -m http.server 8000` in this folder, then open http://localhost:8000/ in a browser.

## Daily Proverb cache

The ticker reads `daily-proverb.json` from the public GitHub repository, with the deployed local copy as a fallback, never directly from the Bible API. The daily workflow fetches one NLT verse from Tyndale at approximately 12:07 AM Louisville time, then commits the shared cache to `main`; visitors receive it without a website redeployment. The day of the month selects the Proverbs chapter. GitHub scheduling and deployment can be delayed, so the ticker offers the NLT chapter link until the current cache is ready.

`scripts/cache_daily_proverb.py` skips the API request when that date is already cached, including manual reruns. A failed request leaves the last good file untouched. There is normally one provider request per day for the entire website; failed runs can be retried manually from Actions → Cache daily NLT proverb → Run workflow. Visitor page loads only request the shared JSON file. The workflow needs GitHub Actions enabled and permission to commit to `main`.

Tyndale's anonymous API is free for noncommercial use (https://api.nlt.to/). Caching does not change its license conditions; commercial use needs permission. Attribution is displayed on the page. No API key, paid storage, or new backend service is required.
