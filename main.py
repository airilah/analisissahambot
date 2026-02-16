# main.py

import io
import sys
import time
import numpy as np
import ta
import matplotlib.pyplot as plt
import mplfinance as mpf  # kalau tidak dipakai boleh dihapus

from data import get_stock_data, get_fundamental
from indicators import add_indicators
from patterns import support_resistance
from strategy import (
    valuation_status,
    calculate_score,
    market_regime,
    breakout_pullback_probability,
    analisa_panel,
)
from backtest import simple_backtest
from ai_model import ai_signal
from grafik import tampilkan_grafik

# ✅ Import scanner yang benar (sesuai versi terbaru)
from scanner import (
    scan_top10_fundamental_cheapest,
    scan_top10_technical_4of4,
    format_fundamental_message,
    format_technical_message,
)


def run_analysis(ticker: str) -> str:
    """
    Analisa 1 emiten dan return hasil dalam bentuk text.
    (dipakai oleh Telegram bot)
    """

    # ✅ buffer harus dibuat per pemanggilan, biar tidak numpuk output lama
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    try:
        df, ticker_full = get_stock_data(ticker)

        if df is None:
            print("Data tidak ditemukan.")
            return buffer.getvalue()

        df = add_indicators(df)
        support, resistance = support_resistance(df)
        regime = market_regime(df)
        breakout_prob, pullback_prob = breakout_pullback_probability(df, resistance)

        fundamental = get_fundamental(ticker)
        valuation = valuation_status(fundamental.get("pe"))

        latest = df.iloc[-1]

        # =========
        # ATR
        # =========
        df["ATR"] = ta.volatility.AverageTrueRange(
            df["High"], df["Low"], df["Close"]
        ).average_true_range()
        atr = df["ATR"].iloc[-1]

        # =========
        # SCORE & CONFIDENCE
        # =========
        score, probability = calculate_score(df, resistance)
        signal = ai_signal(score)

        trend_score = 1 if latest["MA20"] > latest["MA50"] else 0

        momentum_score = 0
        if latest["MACD"] > latest["MACD_signal"]:
            momentum_score += 1
        if 45 < latest["RSI"] < 65:
            momentum_score += 1

        structure_score = 1 if latest["Close"] > resistance * 0.98 else 0

        confidence = (
            trend_score * 0.4 +
            (momentum_score / 2) * 0.35 +
            structure_score * 0.25
        ) * 100
        confidence = round(confidence, 2)

        expected_move_percent = round((atr / latest["Close"]) * 100, 2)

        distance_from_ma = ((latest["Close"] - latest["MA20"]) / latest["MA20"]) * 100
        warning = None
        if distance_from_ma > 8:
            warning = "Harga sudah terlalu jauh di atas MA20 (overextended). Risiko koreksi meningkat."

        if confidence >= 70 and valuation == "Mahal":
            rating = "Bullish tapi Mahal"
        elif confidence >= 70 and valuation != "Mahal":
            rating = "Bullish dan Wajar"
        elif confidence < 50:
            rating = "Sideways"
        elif distance_from_ma > 8:
            rating = "Overextended"
        else:
            rating = "Netral"

        entry_breakout = resistance * 1.02
        entry_pullback = df["MA20"].iloc[-1]
        stop_loss = latest["Close"] - (1.5 * atr)
        take_profit = latest["Close"] + (3 * atr)
        rr = round((take_profit - latest["Close"]) / (latest["Close"] - stop_loss), 2)

        backtest_result = simple_backtest(df)
        return_percent = round((backtest_result - 1) * 100, 2)

        # =====
        # OUTPUT DETAIL
        # =====
        print("\n========")
        print("ANALISA LENGKAP SAHAM:", ticker_full)
        print("Harga Terakhir:", round(latest["Close"], 2))
        print("========\n")

        # ==== MARKET CONDITION ====
        print("==== KONDISI PASAR ====\n")
        print("Market Regime:", regime)
        print("Confidence Score:", confidence, "%")
        print("Expected Move Harian (berdasarkan ATR): ±", expected_move_percent, "%")
        print("Rating Akhir Sistem:", rating)
        print("")

        print("Probabilitas Breakout:", breakout_prob, "%")
        print("Probabilitas Pullback:", pullback_prob, "%")
        print("")

        # ==== FUNDAMENTAL ====
        print("==== ANALISA FUNDAMENTAL ====\n")
        print("Valuasi:", valuation)

        if valuation == "Mahal":
            print("Saham dihargai tinggi dibandingkan kemampuan laba saat ini.")
            print("Artinya investor membayar premium dan margin of safety lebih kecil.")
            print("Jika momentum berhenti, risiko koreksi relatif lebih besar.")
        elif valuation == "Murah":
            print("Saham relatif undervalued dibanding laba.")
            print("Risiko jangka panjang lebih terkontrol.")
        else:
            print("Valuasi berada dalam kisaran wajar.")
        print("")

        # ==== TEKNIKAL ====
        print("==== ANALISA TEKNIKAL ====\n")
        print("Score Teknikal:", score, "dari 4")
        print("Probabilitas Kenaikan:", probability, "%")
        print("Sinyal Sistem:", signal)
        print("")

        print("Struktur Harga:")
        print("Support terdekat:", round(support, 2))
        print("Resistance terdekat:", round(resistance, 2))
        print("")

        # ==== STRATEGI SWING ====
        print("==== STRATEGI SWING 3–10 HARI ====\n")
        print("Skenario Breakout:")
        print("Entry ideal di atas:", round(entry_breakout, 2))
        print("Breakout harus disertai volume tinggi untuk valid.")
        print("")

        print("Skenario Pullback:")
        print("Entry ideal di area MA20:", round(entry_pullback, 2))
        print("Pullback sehat biasanya terjadi sebelum kenaikan lanjutan.")
        print("")

        print("Target & Manajemen Risiko:")
        print("Take Profit estimasi:", round(take_profit, 2))
        print("Stop Loss estimasi:", round(stop_loss, 2))
        print("Risk Reward Ratio:", rr)
        print("")

        if warning:
            print("PERINGATAN:")
            print(warning)
            print("")

        # ==== PROYEKSI ====
        print("==== PROYEKSI KEDEPAN ====\n")
        if latest["Close"] >= resistance:
            print("Harga berada di area resistance.")
            print("Kemungkinan terjadi breakout atau koreksi sehat terlebih dahulu.")
        elif latest["Close"] > df["MA20"].iloc[-1]:
            print("Harga masih di atas MA20, tren jangka pendek masih terjaga.")
        else:
            print("Harga melemah di bawah MA20, potensi koreksi meningkat.")

        print("\nBacktest MA Strategy Return:", return_percent, "%")
        print("Jika nilai ini positif, strategi tren historis cukup mendukung.\n")

        # ==== ENTRY 1–2 HARI ====
        print("==== EVALUASI ENTRY 1–2 HARI ====\n")

        entry_now = latest["Close"]
        short_tp = entry_now + (2 * atr)
        short_sl = entry_now - (1 * atr)
        short_rr = round((short_tp - entry_now) / (entry_now - short_sl), 2)

        if breakout_prob > 60 and confidence > 60:
            print("Potensi kenaikan jangka sangat pendek cukup baik.")
            print("Entry di harga sekarang masih dapat dipertimbangkan.")
        elif pullback_prob > breakout_prob:
            print("Probabilitas pullback lebih tinggi dibanding breakout.")
            print("Lebih bijak menunggu koreksi sebelum masuk.")
        else:
            print("Momentum belum cukup kuat untuk entry agresif.")
            print("Sebaiknya menunggu konfirmasi tambahan.")

        print("")
        print("Jika tetap masuk di harga sekarang:")
        print("Take Profit (1–2 hari):", round(short_tp, 2))
        print("Stop Loss (1–2 hari):", round(short_sl, 2))
        print("Risk Reward Ratio:", short_rr)
        print("")

        print("Alternatif lebih aman:")
        print("Tunggu breakout valid di atas:", round(entry_breakout, 2))
        print("Dengan konfirmasi volume.")

        print("\n==== GRAFIK ANALISA ====\n")
        tampilkan_grafik(df, ticker_full, support, resistance)

        panel_text = analisa_panel(df, support, resistance, valuation)
        print(panel_text)

        return buffer.getvalue()

    finally:
        # ✅ selalu balikin stdout meskipun error
        sys.stdout = old_stdout


if __name__ == "__main__":
    print("1 = Analisa 1 saham")
    print("2 = Top 10 Valuasi Termurah (PE)")
    print("3 = Top 10 Teknikal Score 4/4")

    pilihan = input("Pilih menu: ").strip()

    if pilihan == "1":
        kode = input("Masukkan kode emiten saham: ").strip().upper()
        print(run_analysis(kode))

    elif pilihan == "2":
        print("\nScanning fundamental termurah...\n")
        top, meta = scan_top10_fundamental_cheapest()
        print(format_fundamental_message(top, meta))

    elif pilihan == "3":
        print("\nScanning teknikal score 4/4...\n")
        top, meta = scan_top10_technical_4of4()
        print(format_technical_message(top, meta))

    else:
        print("Pilihan tidak valid.")