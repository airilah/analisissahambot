# data.py
from __future__ import annotations

import time
import re
from io import StringIO

import pandas as pd
import requests
import yfinance as yf


# =========================
# PRICE DATA (yfinance)
# =========================
def get_stock_data(ticker: str, period: str = "6mo"):
    """
    Return (df, ticker_full)
    df: OHLCV dataframe
    ticker_full: e.g. "BBCA.JK"
    """
    ticker_full = ticker.strip().upper() + ".JK"
    stock = yf.Ticker(ticker_full)
    df = stock.history(period=period)

    if df is None or df.empty:
        return None, ticker_full

    return df, ticker_full


def get_fundamental(ticker: str) -> dict:
    """
    Fundamental via yfinance info.
    """
    stock = yf.Ticker(ticker.strip().upper() + ".JK")
    info = stock.info or {}
    return {
        "pe": info.get("trailingPE"),
        "roe": info.get("returnOnEquity"),
    }


# =========================
# UNIVERSE TICKERS (Realtime-ish)
# Source: StockAnalysis (IDX list)
# =========================
STOCKANALYSIS_IDX_LIST_URL = "https://stockanalysis.com/list/indonesia-stock-exchange/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

_UNIVERSE_CACHE = {"ts": 0.0, "tickers": []}


def _normalize_ticker(raw: str) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if not s:
        return None

    s = s.replace(".JK", "")
    s = re.sub(r"\[.*?\]", "", s).strip()
    s = "".join(ch for ch in s if ch.isalnum())

    if 1 <= len(s) <= 6:
        return s
    return None


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for it in items:
        if it not in seen:
            seen.add(it)
            out.append(it)
    return out


def _get_universe_from_stockanalysis() -> list[str]:
    r = requests.get(STOCKANALYSIS_IDX_LIST_URL, headers=_HEADERS, timeout=30)
    r.raise_for_status()

    # pandas.read_html butuh lxml; pakai StringIO biar warning FutureWarning hilang
    tables = pd.read_html(StringIO(r.text))

    if not tables:
        raise RuntimeError("Tidak menemukan tabel di halaman StockAnalysis.")

    target = None
    for df in tables:
        cols = [str(c).lower() for c in df.columns]
        if any(("symbol" in c) or ("ticker" in c) for c in cols):
            target = df
            break

    if target is None:
        raise RuntimeError("Tidak menemukan tabel dengan kolom Symbol/Ticker.")

    sym_col = None
    for c in target.columns:
        lc = str(c).lower()
        if "symbol" in lc or "ticker" in lc:
            sym_col = c
            break

    if sym_col is None:
        raise RuntimeError(f"Kolom Symbol tidak ditemukan. Kolom tersedia: {list(target.columns)}")

    tickers = []
    for v in target[sym_col].astype(str).tolist():
        t = _normalize_ticker(v)
        if t:
            tickers.append(t)

    tickers = _unique_preserve_order(tickers)

    # IDX harus ratusan; kalau terlalu sedikit berarti format berubah / diblok
    if len(tickers) < 300:
        raise RuntimeError(f"Hasil ticker terlalu sedikit ({len(tickers)}).")

    return tickers


def get_all_idx_tickers(cache_seconds: int = 600) -> list[str]:
    """
    Ambil seluruh ticker IDX (update otomatis), cache default 10 menit.
    """
    now = time.time()
    if _UNIVERSE_CACHE["tickers"] and (now - _UNIVERSE_CACHE["ts"] < cache_seconds):
        return _UNIVERSE_CACHE["tickers"]

    tickers = _get_universe_from_stockanalysis()
    _UNIVERSE_CACHE["ts"] = now
    _UNIVERSE_CACHE["tickers"] = tickers
    return tickers