# scanner.py
from __future__ import annotations

import os
import time
from dataclasses import dataclass

from data import get_all_idx_tickers, get_fundamental, get_stock_data
from indicators import add_indicators
from patterns import support_resistance
from strategy import calculate_score


# =========================
# Data Classes
# =========================
@dataclass
class FundamentalRank:
    ticker: str
    pe: float
    roe: float | None
    last_close: float


@dataclass
class TechnicalRank:
    ticker: str
    score: int
    probability: float
    last_close: float


@dataclass
class ComboRank:
    ticker: str
    total_score: int
    pe: float
    tech_score: int
    f_score: int


@dataclass
class UndervaluedRank:
    ticker: str
    pe: float
    tech_score: int
    last_close: float


@dataclass
class BreakoutRank:
    ticker: str
    probability: float
    tech_score: int
    last_close: float
    resistance: float


# =========================
# Helpers
# =========================
def _safe_float(x):
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _get_max_universe(default: int | None = None) -> int | None:
    env_lim = os.getenv("MAX_UNIVERSE")
    if env_lim and env_lim.isdigit():
        return int(env_lim)
    return default


def _split_meta_line(meta: dict) -> str:
    return (
        f"ℹ️ Universe: {meta.get('universe_scanned')}/{meta.get('universe_total')} | "
        f"OK: {meta.get('ok')} | "
        f"NoPrice: {meta.get('no_price')} | "
        f"NoPE: {meta.get('no_pe', 0)} | "
        f"ScoreFail: {meta.get('score_fail', meta.get('score_not_4', 0))} | "
        f"Other: {meta.get('errors')} | "
        f"Durasi: {meta.get('duration_s')}s"
    )


def _format_empty(title: str, meta: dict, hint: str) -> str:
    lines = [title, ""]
    lines.append("⚠️ Tidak ada saham yang lolos filter saat ini.")
    lines.append(hint)
    lines.append("")
    lines.append(_split_meta_line(meta))
    return "\n".join(lines)


# =========================
# SCAN: Fundamental Cheapest
# =========================
def scan_top10_fundamental_cheapest(
    *,
    period: str = "6mo",
    top_n: int = 10,
    max_universe: int | None = None,
) -> tuple[list[FundamentalRank], dict]:
    max_universe = _get_max_universe(max_universe)

    tickers = get_all_idx_tickers()
    total = len(tickers)
    if max_universe is not None:
        tickers = tickers[:max_universe]

    meta = {
        "universe_total": total,
        "universe_scanned": len(tickers),
        "ok": 0,
        "no_price": 0,
        "no_pe": 0,
        "errors": 0,
        "duration_s": None,
    }

    t0 = time.time()
    out: list[FundamentalRank] = []

    for t in tickers:
        try:
            df, _ = get_stock_data(t, period=period)
            if df is None or df.empty:
                meta["no_price"] += 1
                continue

            f = get_fundamental(t)
            pe = _safe_float(f.get("pe"))
            roe = _safe_float(f.get("roe"))

            if pe is None:
                meta["no_pe"] += 1
                continue

            last_close = float(df["Close"].iloc[-1])
            out.append(FundamentalRank(ticker=t, pe=pe, roe=roe, last_close=last_close))
            meta["ok"] += 1

        except Exception:
            meta["errors"] += 1
            continue

    meta["duration_s"] = round(time.time() - t0, 2)

    out.sort(key=lambda r: (r.pe, -(r.roe if r.roe is not None else -1e9)))
    return out[:top_n], meta


# =========================
# SCAN: Technical 4/4
# =========================
def scan_top10_technical_4of4(
    *,
    period: str = "6mo",
    top_n: int = 10,
    max_universe: int | None = None,
) -> tuple[list[TechnicalRank], dict]:
    max_universe = _get_max_universe(max_universe)

    tickers = get_all_idx_tickers()
    total = len(tickers)
    if max_universe is not None:
        tickers = tickers[:max_universe]

    meta = {
        "universe_total": total,
        "universe_scanned": len(tickers),
        "ok": 0,
        "no_price": 0,
        "score_not_4": 0,
        "errors": 0,
        "duration_s": None,
    }

    t0 = time.time()
    out: list[TechnicalRank] = []

    for t in tickers:
        try:
            df, _ = get_stock_data(t, period=period)
            if df is None or df.empty:
                meta["no_price"] += 1
                continue

            df = add_indicators(df)
            _, resistance = support_resistance(df)
            score, probability = calculate_score(df, resistance)

            if score != 4:
                meta["score_not_4"] += 1
                continue

            last_close = float(df["Close"].iloc[-1])
            out.append(TechnicalRank(ticker=t, score=int(score), probability=float(probability), last_close=last_close))
            meta["ok"] += 1

        except Exception:
            meta["errors"] += 1
            continue

    meta["duration_s"] = round(time.time() - t0, 2)

    out.sort(key=lambda r: (-r.probability, r.ticker))
    return out[:top_n], meta


# =========================
# SCAN: Combo Fundamental + Technical
# =========================
def scan_top10_combo(
    *,
    period: str = "6mo",
    top_n: int = 10,
    max_universe: int | None = None,
) -> tuple[list[ComboRank], dict]:
    max_universe = _get_max_universe(max_universe)

    tickers = get_all_idx_tickers()
    total = len(tickers)
    if max_universe is not None:
        tickers = tickers[:max_universe]

    meta = {
        "universe_total": total,
        "universe_scanned": len(tickers),
        "ok": 0,
        "no_price": 0,
        "no_pe": 0,
        "errors": 0,
        "duration_s": None,
    }

    t0 = time.time()
    out: list[ComboRank] = []

    for t in tickers:
        try:
            df, _ = get_stock_data(t, period=period)
            if df is None or df.empty:
                meta["no_price"] += 1
                continue

            df = add_indicators(df)
            _, resistance = support_resistance(df)
            tech_score, _prob = calculate_score(df, resistance)

            f = get_fundamental(t)
            pe = _safe_float(f.get("pe"))
            if pe is None:
                meta["no_pe"] += 1
                continue

            # Fundamental score (lebih realistis)
            if pe < 10:
                f_score = 4
            elif pe < 15:
                f_score = 3
            elif pe < 20:
                f_score = 2
            else:
                f_score = 1

            total_score = int(f_score + tech_score)

            out.append(
                ComboRank(
                    ticker=t,
                    total_score=total_score,
                    pe=float(pe),
                    tech_score=int(tech_score),
                    f_score=int(f_score),
                )
            )
            meta["ok"] += 1

        except Exception:
            meta["errors"] += 1
            continue

    meta["duration_s"] = round(time.time() - t0, 2)

    out.sort(key=lambda r: (-r.total_score, r.pe))
    return out[:top_n], meta


# =========================
# SCAN: Undervalued but Strong Trend
# (dilonggarkan agar lebih sering ada hasil)
# =========================
def scan_top10_undervalued_strong(
    *,
    period: str = "6mo",
    top_n: int = 10,
    pe_max: float = 20.0,     # sebelumnya 15 (ketat)
    min_score: int = 2,       # sebelumnya 3 (ketat)
    max_universe: int | None = None,
) -> tuple[list[UndervaluedRank], dict]:
    max_universe = _get_max_universe(max_universe)

    tickers = get_all_idx_tickers()
    total = len(tickers)
    if max_universe is not None:
        tickers = tickers[:max_universe]

    meta = {
        "universe_total": total,
        "universe_scanned": len(tickers),
        "ok": 0,
        "no_price": 0,
        "no_pe": 0,
        "score_fail": 0,
        "trend_fail": 0,
        "errors": 0,
        "duration_s": None,
    }

    t0 = time.time()
    out: list[UndervaluedRank] = []

    for t in tickers:
        try:
            df, _ = get_stock_data(t, period=period)
            if df is None or df.empty or len(df) < 60:
                meta["no_price"] += 1
                continue

            df = add_indicators(df)
            _, resistance = support_resistance(df)

            tech_score, _prob = calculate_score(df, resistance)
            if int(tech_score) < min_score:
                meta["score_fail"] += 1
                continue

            latest = df.iloc[-1]
            if not (latest["MA20"] > latest["MA50"] and latest["Close"] > latest["MA20"]):
                meta["trend_fail"] += 1
                continue

            f = get_fundamental(t)
            pe = _safe_float(f.get("pe"))
            if pe is None:
                meta["no_pe"] += 1
                continue

            if pe > pe_max:
                meta["no_pe"] += 1
                continue

            out.append(
                UndervaluedRank(
                    ticker=t,
                    pe=float(pe),
                    tech_score=int(tech_score),
                    last_close=float(latest["Close"]),
                )
            )
            meta["ok"] += 1

        except Exception:
            meta["errors"] += 1
            continue

    meta["duration_s"] = round(time.time() - t0, 2)

    out.sort(key=lambda r: (r.pe, -r.tech_score))
    return out[:top_n], meta


# =========================
# SCAN: Breakout Candidate
# (dilonggarkan + volume spike dibuat opsional)
# =========================
def scan_top10_breakout(
    *,
    period: str = "6mo",
    top_n: int = 10,
    near_resistance: float = 0.95,  # sebelumnya 0.98 (ketat)
    min_score: int = 2,             # sebelumnya 3 (ketat)
    max_universe: int | None = None,
) -> tuple[list[BreakoutRank], dict]:
    max_universe = _get_max_universe(max_universe)

    tickers = get_all_idx_tickers()
    total = len(tickers)
    if max_universe is not None:
        tickers = tickers[:max_universe]

    meta = {
        "universe_total": total,
        "universe_scanned": len(tickers),
        "ok": 0,
        "no_price": 0,
        "score_fail": 0,
        "near_res_fail": 0,
        "errors": 0,
        "duration_s": None,
    }

    t0 = time.time()
    out: list[BreakoutRank] = []

    for t in tickers:
        try:
            df, _ = get_stock_data(t, period=period)
            if df is None or df.empty or len(df) < 60:
                meta["no_price"] += 1
                continue

            df = add_indicators(df)
            _, resistance = support_resistance(df)

            latest = df.iloc[-1]
            tech_score, probability = calculate_score(df, resistance)
            if int(tech_score) < min_score:
                meta["score_fail"] += 1
                continue

            # dekat resistance
            if not (latest["Close"] >= resistance * near_resistance):
                meta["near_res_fail"] += 1
                continue

            out.append(
                BreakoutRank(
                    ticker=t,
                    probability=float(probability),
                    tech_score=int(tech_score),
                    last_close=float(latest["Close"]),
                    resistance=float(resistance),
                )
            )
            meta["ok"] += 1

        except Exception:
            meta["errors"] += 1
            continue

    meta["duration_s"] = round(time.time() - t0, 2)

    out.sort(key=lambda r: (-r.probability, -r.tech_score))
    return out[:top_n], meta


# =========================
# Formatters
# =========================
def format_fundamental_message(top: list[FundamentalRank], meta: dict) -> str:
    title = "🏷️ Top 10 Fundamental Termurah (PE terkecil)"
    if not top:
        return _format_empty(title, meta, "Coba naikkan MAX_UNIVERSE atau scan ulang beberapa menit lagi.")

    lines = [title, ""]
    for i, r in enumerate(top, 1):
        roe_txt = f"{(r.roe * 100):.1f}%" if r.roe is not None else "-"
        lines.append(f"{i}. {r.ticker} | PE: {r.pe:.2f} | ROE: {roe_txt} | Close: {r.last_close:.0f}")

    lines.append("")
    lines.append(_split_meta_line(meta))
    return "\n".join(lines)


def format_technical_message(top: list[TechnicalRank], meta: dict) -> str:
    title = "📊 Top 10 Technical (Score 4/4)"
    if not top:
        return _format_empty(
            title, meta,
            "Tidak ada yang score 4/4 saat ini. Coba /technical dengan MAX_UNIVERSE lebih besar."
        )

    lines = [title, ""]
    for i, r in enumerate(top, 1):
        lines.append(f"{i}. {r.ticker} | Score: {r.score}/4 | Prob: {r.probability:.0f}% | Close: {r.last_close:.0f}")

    lines.append("")
    lines.append(_split_meta_line(meta))
    return "\n".join(lines)


def format_combo_message(top: list[ComboRank], meta: dict) -> str:
    title = "🏆 Top 10 Combo (Fundamental + Technical)"
    if not top:
        return _format_empty(title, meta, "Tidak ada data cukup. Coba naikkan MAX_UNIVERSE.")

    lines = [title, ""]
    for i, r in enumerate(top, 1):
        lines.append(
            f"{i}. {r.ticker} | Total: {r.total_score} | F:{r.f_score}/4 | T:{r.tech_score}/4 | PE: {r.pe:.2f}"
        )

    lines.append("")
    lines.append(_split_meta_line(meta))
    return "\n".join(lines)


def format_undervalued_message(top: list[UndervaluedRank], meta: dict) -> str:
    title = "💎 Undervalued but Strong Trend"
    if not top:
        return _format_empty(
            title, meta,
            "Filter mungkin terlalu ketat / banyak PE kosong. Coba longgarkan: pe_max=25 atau min_score=1."
        )

    lines = [title, ""]
    for i, r in enumerate(top, 1):
        lines.append(f"{i}. {r.ticker} | PE: {r.pe:.2f} | Score: {r.tech_score}/4 | Close: {r.last_close:.0f}")

    lines.append("")
    lines.append(_split_meta_line(meta))
    return "\n".join(lines)


def format_breakout_message(top: list[BreakoutRank], meta: dict) -> str:
    title = "🚀 Breakout Candidates"
    if not top:
        return _format_empty(
            title, meta,
            "Filter mungkin terlalu ketat. Coba near_resistance=0.93 atau min_score=1."
        )

    lines = [title, ""]
    for i, r in enumerate(top, 1):
        lines.append(
            f"{i}. {r.ticker} | Prob: {r.probability:.0f}% | Score: {r.tech_score}/4 | Close: {r.last_close:.0f} | Res: {r.resistance:.0f}"
        )

    lines.append("")
    lines.append(_split_meta_line(meta))
    return "\n".join(lines)