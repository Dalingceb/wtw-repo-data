"""
fetch_multi_tf.py

Pulls monthly / weekly / daily / 1H OHLC data for every symbol listed in
pairs.txt, via yfinance, and saves clean CSVs under data/<SYMBOL>/.

Designed to run inside GitHub Actions (which has full internet access),
not in a sandboxed environment - yfinance needs to reach Yahoo Finance's
query endpoints directly.

Supports two kinds of entries in pairs.txt:
  - Plain forex pairs (e.g. "GBPCAD") - the "=X" suffix is added automatically.
  - Raw yfinance tickers (e.g. "CL=F" for WTI crude futures, "GC=F" for gold) -
    used as-is, since they already have their own suffix/format.

4H is intentionally NOT fetched here - it's derived by resampling the 1H
data (yfinance doesn't offer a native 4H interval, and this matches the
same approach already validated on GBPCAD earlier in this project).

NOTE on daily history depth: set to "max" rather than a fixed lookback,
since some instruments (e.g. USOIL/CL=F, needed back to April 2020 for
the negative-price event) need deeper history than a recent forex pair
typically does. This costs nothing extra - yfinance returns what's
available either way - but keep in mind 1H data is still capped at
yfinance's ~730-day maximum regardless of this setting.
"""

import os
import sys
import time
import pandas as pd
import yfinance as yf

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS_FILE = os.path.join(REPO_ROOT, "pairs.txt")
DATA_DIR = os.path.join(REPO_ROOT, "data")

# (period, interval, output suffix)
FETCH_SPECS = [
    ("max", "1mo", "monthly"),
    ("max", "1wk", "weekly"),
    ("max", "1d", "daily"),
    ("730d", "1h", "1h"),  # yfinance's max lookback for 1h interval
]


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """yfinance sometimes returns MultiIndex columns - flatten them."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def read_pairs() -> list:
    if not os.path.exists(PAIRS_FILE):
        print(f"No pairs.txt found at {PAIRS_FILE} - nothing to fetch.")
        return []
    with open(PAIRS_FILE) as f:
        pairs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return pairs


def to_ticker(symbol: str) -> str:
    """Plain forex codes get '=X' appended. Anything already containing '='
    (e.g. 'CL=F') is assumed to already be a valid yfinance ticker."""
    return symbol if "=" in symbol else f"{symbol}=X"


def fetch_pair(symbol: str):
    """symbol can be a plain currency-pair string like 'GBPCAD' (gets '=X'
    appended automatically) or a raw yfinance ticker like 'CL=F' (used as-is).
    Output folder is named after the plain symbol either way, with '='
    replaced so it's filesystem-safe."""
    ticker = to_ticker(symbol)
    folder_name = symbol.replace("=", "_")
    pair_dir = os.path.join(DATA_DIR, folder_name)
    os.makedirs(pair_dir, exist_ok=True)

    for period, interval, suffix in FETCH_SPECS:
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            df = flatten_columns(df)
            if df.empty:
                print(f"  [{symbol}] {suffix}: no data returned, skipping")
                continue
            out_path = os.path.join(pair_dir, f"{folder_name}_{suffix}.csv")
            df.to_csv(out_path)
            print(f"  [{symbol}] {suffix}: {len(df)} rows -> {out_path}")
        except Exception as e:
            print(f"  [{symbol}] {suffix}: FAILED - {e}")
        time.sleep(1)  # be polite to the endpoint between calls


def main():
    pairs = read_pairs()
    if not pairs:
        sys.exit(0)
    print(f"Fetching {len(pairs)} symbol(s): {', '.join(pairs)}")
    for pair in pairs:
        print(f"Fetching {pair}...")
        fetch_pair(pair)
    print("Done.")


if __name__ == "__main__":
    main()
