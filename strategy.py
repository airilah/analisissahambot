# strategy.py

def valuation_status(pe):
    if pe is None:
        return "Data tidak tersedia"
    if pe < 15:
        return "Murah"
    elif pe < 25:
        return "Wajar"
    else:
        return "Mahal"


def calculate_score(df, resistance):

    latest = df.iloc[-1]
    score = 0

    if latest['MA20'] > latest['MA50']:
        score += 1

    if latest['MACD'] > latest['MACD_signal']:
        score += 1

    if 40 < latest['RSI'] < 65:
        score += 1

    if latest['Close'] > resistance * 0.98:
        score += 1

    probability = (score / 4) * 100

    return score, probability


def market_regime(df):

    df['MA200'] = df['Close'].rolling(200).mean()

    latest = df.iloc[-1]

    if latest['MA50'] > latest['MA200'] and latest['RSI'] > 50:
        return "Bull Market"
    elif latest['MA50'] < latest['MA200'] and latest['RSI'] < 50:
        return "Bear Market"
    else:
        return "Sideways Market"


def breakout_pullback_probability(df, resistance):

    latest = df.iloc[-1]

    breakout_score = 0
    pullback_score = 0

    # Breakout logic
    if latest['Close'] > resistance * 0.98:
        breakout_score += 1
    if latest['Volume'] > df['Volume'][-20:].mean():
        breakout_score += 1
    if latest['RSI'] > 55:
        breakout_score += 1

    # Pullback logic
    distance = abs(latest['Close'] - latest['MA20']) / latest['MA20']
    if distance < 0.02:
        pullback_score += 1
    if 40 < latest['RSI'] < 55:
        pullback_score += 1
    if latest['MACD'] > latest['MACD_signal']:
        pullback_score += 1

    breakout_prob = round((breakout_score / 3) * 100, 2)
    pullback_prob = round((pullback_score / 3) * 100, 2)

    return breakout_prob, pullback_prob


def analisa_panel(df, support, resistance, valuation):

    latest = df.iloc[-1]
    hasil = "\n================= ANALISA PER PANEL =================\n\n"

    # =========================================
    # PANEL 1 - HARGA & TREND
    # =========================================
    hasil += "Panel 1 - Struktur Harga & Tren:\n"

    distance_to_res = (resistance - latest['Close']) / latest['Close'] * 100
    distance_to_sup = (latest['Close'] - support) / latest['Close'] * 100

    if latest['Close'] > latest['MA20'] and latest['MA20'] > latest['MA50']:
        hasil += "- Harga berada di atas MA20 dan MA50 → Struktur tren naik sehat.\n"
        hasil += "- Buyer masih mengendalikan pergerakan harga.\n"
        kesimpulan_harga = "Bullish"

    elif latest['Close'] < latest['MA20']:
        hasil += "- Harga berada di bawah MA20 → Momentum jangka pendek melemah.\n"
        hasil += "- Potensi koreksi atau pullback lebih besar.\n"
        kesimpulan_harga = "Bearish"

    else:
        hasil += "- Harga berada di area konsolidasi antara MA20 dan MA50.\n"
        kesimpulan_harga = "Sideways"

    hasil += f"- Jarak ke resistance: {round(distance_to_res,2)} %\n"
    hasil += f"- Jarak ke support: {round(distance_to_sup,2)} %\n"

    hasil += f"Kesimpulan Panel Harga: {kesimpulan_harga}\n\n"

    # =========================================
    # PANEL 2 - VOLUME
    # =========================================
    hasil += "Panel 2 - Volume:\n"

    avg_vol = df['Volume'][-20:].mean()

    if latest['Volume'] > avg_vol and latest['Close'] > df['Close'].iloc[-2]:
        hasil += "- Volume tinggi disertai kenaikan harga → Akumulasi kuat.\n"
        kesimpulan_vol = "Bullish Confirmation"

    elif latest['Volume'] > avg_vol and latest['Close'] < df['Close'].iloc[-2]:
        hasil += "- Volume tinggi saat harga turun → Potensi distribusi.\n"
        kesimpulan_vol = "Bearish Pressure"

    else:
        hasil += "- Volume normal → Tidak ada tekanan signifikan.\n"
        kesimpulan_vol = "Netral"

    hasil += f"Kesimpulan Panel Volume: {kesimpulan_vol}\n\n"

    # =========================================
    # PANEL 3 - MACD
    # =========================================
    hasil += "Panel 3 - MACD (Momentum):\n"

    if latest['MACD'] > latest['MACD_signal'] and latest['MACD'] > 0:
        hasil += "- MACD di atas signal dan di atas nol → Momentum bullish kuat.\n"
        kesimpulan_macd = "Bullish Strong"

    elif latest['MACD'] > latest['MACD_signal']:
        hasil += "- MACD cross up namun masih di bawah nol → Awal pembalikan.\n"
        kesimpulan_macd = "Bullish Weak"

    else:
        hasil += "- MACD di bawah signal → Momentum melemah.\n"
        kesimpulan_macd = "Bearish"

    hasil += f"Kesimpulan Panel MACD: {kesimpulan_macd}\n\n"

    # =========================================
    # PANEL 4 - RSI
    # =========================================
    hasil += "Panel 4 - RSI (Kekuatan Relatif):\n"

    if latest['RSI'] > 70:
        hasil += "- RSI > 70 → Overbought, rawan koreksi jangka pendek.\n"
        kesimpulan_rsi = "Overbought"

    elif latest['RSI'] < 30:
        hasil += "- RSI < 30 → Oversold, potensi rebound.\n"
        kesimpulan_rsi = "Oversold"

    elif latest['RSI'] > 55:
        hasil += "- RSI di atas 55 → Zona bullish sehat.\n"
        kesimpulan_rsi = "Bullish"

    else:
        hasil += "- RSI netral → Tidak ada tekanan ekstrem.\n"
        kesimpulan_rsi = "Netral"

    hasil += f"Kesimpulan Panel RSI: {kesimpulan_rsi}\n\n"

    # =========================================
    # FUNDAMENTAL CHECK
    # =========================================
    hasil += "Panel Fundamental:\n"

    if valuation == "Mahal":
        hasil += "- Valuasi mahal → Risiko koreksi lebih tinggi jika momentum berhenti.\n"
        fund_status = "Risky"

    elif valuation == "Murah":
        hasil += "- Valuasi murah → Potensi kenaikan jangka panjang lebih sehat.\n"
        fund_status = "Supportive"

    else:
        hasil += "- Valuasi wajar → Tidak menjadi penghambat utama.\n"
        fund_status = "Neutral"

    hasil += "\n"

    # =========================================
    # KESIMPULAN GABUNGAN
    # =========================================
    hasil += "================= KESIMPULAN GABUNGAN =================\n"

    if kesimpulan_harga == "Bullish" and kesimpulan_macd.startswith("Bullish"):
        if fund_status == "Risky":
            hasil += "Teknikal kuat namun valuasi mahal → Cocok untuk swing, hati-hati jangka panjang.\n"
        else:
            hasil += "Teknikal dan fundamental mendukung → Potensi kenaikan relatif sehat.\n"

    elif kesimpulan_harga == "Bearish":
        hasil += "Struktur harga melemah → Risiko penurunan lebih besar.\n"

    else:
        hasil += "Sinyal campuran → Sebaiknya tunggu konfirmasi tambahan.\n"

    return hasil
