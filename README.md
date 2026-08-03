# WTW Data Feed

Auto-updating multi-timeframe forex OHLC data, fetched hourly via GitHub Actions
and committed straight into this repo. Built to let Claude pull fresh data
directly from `raw.githubusercontent.com` instead of needing manual CSV uploads.

## Setup (one-time)

1. **Create a new GitHub repo** (public - the data here is just OHLC prices,
   nothing sensitive, and keeping it public avoids needing to hand any
   credentials to Claude).
2. **Add these files** to the repo, preserving the folder structure:
   - `pairs.txt`
   - `scripts/fetch_multi_tf.py`
   - `.github/workflows/fetch_data.yml`
3. **Push to GitHub.** The workflow needs no secrets - it uses the
   automatically-provided `GITHUB_TOKEN` to commit results back.
4. **Check the Actions tab** on GitHub - you should see "Fetch Forex Data"
   listed. Click "Run workflow" to trigger it manually the first time
   rather than waiting for the next scheduled hour, to confirm it works.
5. **Check the `data/` folder** after that first run - you should see
   `data/GBPCAD/GBPCAD_monthly.csv`, `_weekly.csv`, `_daily.csv`, `_1h.csv`.

## Adding more pairs

Edit `pairs.txt` - one pair per line, no `=X` suffix (e.g. `EURUSD`, `USDJPY`).
The next scheduled run (or a manual "Run workflow") will pick up the change.

## Adjusting the schedule

Edit the `cron` line in `.github/workflows/fetch_data.yml`. The current
setting (`0 * * * 1-5`) runs hourly, Monday-Friday, UTC.

## 4H data

Not fetched directly - yfinance has no native 4H interval. It's derived by
resampling the 1H CSV, which Claude's analysis toolkit (`wtw_analysis.py`)
already handles.

## Giving Claude access

Once data exists in the repo, just share the repo's raw base URL, e.g.:

```
https://raw.githubusercontent.com/<your-username>/<repo-name>/main/
```

Claude can fetch `data/GBPCAD/GBPCAD_daily.csv` etc. directly from that base
URL without any upload.
