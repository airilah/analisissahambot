# grafik.py

import matplotlib.pyplot as plt


def tampilkan_grafik(df, ticker_full, support, resistance):

    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        figsize=(16,10),
        sharex=True
    )

    # =====================================================
    # PANEL 1 (KIRI ATAS) - HARGA
    # =====================================================
    axes[0,0].plot(df['Close'], label='Harga', color='blue')
    axes[0,0].plot(df['MA20'], label='MA20', color='orange')
    axes[0,0].plot(df['MA50'], label='MA50', color='green')

    upper_atr = df['Close'] + df['ATR']
    lower_atr = df['Close'] - df['ATR']

    axes[0,0].plot(upper_atr, linestyle='--', color='gray', alpha=0.6, label='Upper ATR')
    axes[0,0].plot(lower_atr, linestyle='--', color='gray', alpha=0.6, label='Lower ATR')

    axes[0,0].axhline(support, linestyle='--', color='lime', label='Support')
    axes[0,0].axhline(resistance, linestyle='--', color='red', label='Resistance')

    axes[0,0].set_title(f"{ticker_full} - Harga")
    axes[0,0].legend()
    axes[0,0].grid(True)

    # =====================================================
    # PANEL 2 (KANAN ATAS) - VOLUME
    # =====================================================
    axes[0,1].bar(df.index, df['Volume'], color='gray')
    axes[0,1].set_title("Volume")
    axes[0,1].grid(True)

    # =====================================================
    # PANEL 3 (KIRI BAWAH) - MACD
    # =====================================================
    axes[1,0].plot(df['MACD'], label='MACD', color='blue')
    axes[1,0].plot(df['MACD_signal'], label='Signal Line', color='orange')
    axes[1,0].axhline(0, linestyle='--', color='black', alpha=0.5)
    axes[1,0].set_title("MACD")
    axes[1,0].legend()
    axes[1,0].grid(True)

    # =====================================================
    # PANEL 4 (KANAN BAWAH) - RSI
    # =====================================================
    axes[1,1].plot(df['RSI'], label='RSI', color='purple')
    axes[1,1].axhline(70, linestyle='--', color='red')
    axes[1,1].axhline(30, linestyle='--', color='green')
    axes[1,1].set_title("RSI")
    axes[1,1].legend()
    axes[1,1].grid(True)

    plt.tight_layout()
    plt.savefig("chart.png", dpi=150)
    plt.close()

