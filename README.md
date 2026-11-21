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

The ticker reads `daily-proverb.json` from the public GitHub repository, with the deployed copy as a fallback. It selects the current Louisville date from today and the next two days in the cache. The day of the month selects the Proverbs chapter.

The workflow is scheduled for 1:37 a.m. Louisville time and can also be run manually from Actions. It fills all missing dates in one request. A same-day run with a full cache makes zero requests. Failed requests leave the previous file intact. Daily cache updates don't require a website redeployment. When a matching verse is unavailable, the ticker still links to today's NLT chapter.

Tyndale has announced the current API will close January 1, 2027. Continued automatic NLT text after that date requires another authorized source.

Tyndale's anonymous API is free for noncommercial use (https://api.nlt.to/). Caching does not change its license conditions; commercial use needs permission. Attribution is displayed on the page. No API key, paid storage, or new backend service is required.


## Latest Moments

GitHub Actions checks the channel's dedicated YouTube Shorts feed every six hours. The site reads `latest-moments.json` directly from the repository. Each successful source updates its own card, and unavailable sources retain their last good clip or profile link.

- YouTube requires no secret.
- Instagram requires an Instagram Login token for the podcast's professional account with the `instagram_business_basic` scope. Store it as the GitHub Actions secret `INSTAGRAM_ACCESS_TOKEN`.
- TikTok requires a Display API token with the `video.list` scope for `@whataboutitpod`. Supply the current token via the GitHub Actions secret `TIKTOK_ACCESS_TOKEN`. The account's OAuth integration must manage token refresh and update this secret. Do not commit tokens.

Use Actions → Refresh Latest Moments → Run workflow to verify a newly authorized source.
