"""
fetch_multi_tf.py

Pulls monthly / weekly / daily / 1H OHLC data for every pair listed in
pairs.txt, via yfinance, and saves clean CSVs under data/<PAIR>/.

Designed to run inside GitHub Actions (which has full internet access),
not in a sandboxed environment - yfinance needs to reach Yahoo Finance's
query endpoints directly.

4H is intentionally NOT fetched here - it's derived by resampling the 1H
data (yfinance doesn't offer a native 4H interval, and this matches the
same approach already validated on GBPCAD earlier in this project).
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
    ("5y", "1wk", "weekly"),
    ("2y", "1d", "daily"),
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


def fetch_pair(pair: str):
    """pair should be a plain currency-pair string like 'GBPCAD' - the
    yfinance ticker suffix ('=X') is added automatically here so pairs.txt
    stays readable."""
    ticker = f"{pair}=X"
    pair_dir = os.path.join(DATA_DIR, pair)
    os.makedirs(pair_dir, exist_ok=True)

    for period, interval, suffix in FETCH_SPECS:
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            df = flatten_columns(df)
            if df.empty:
                print(f"  [{pair}] {suffix}: no data returned, skipping")
                continue
            out_path = os.path.join(pair_dir, f"{pair}_{suffix}.csv")
            df.to_csv(out_path)
            print(f"  [{pair}] {suffix}: {len(df)} rows -> {out_path}")
        except Exception as e:
            print(f"  [{pair}] {suffix}: FAILED - {e}")
        time.sleep(1)  # be polite to the endpoint between calls


def main():
    pairs = read_pairs()
    if not pairs:
        sys.exit(0)
    print(f"Fetching {len(pairs)} pair(s): {', '.join(pairs)}")
    for pair in pairs:
        print(f"Fetching {pair}...")
        fetch_pair(pair)
    print("Done.")


if __name__ == "__main__":
    main()
