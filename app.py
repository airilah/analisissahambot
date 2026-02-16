import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide")

st.title("📈 Trading Dashboard - Professional Mode")

ticker_input = st.text_input("Masukkan kode saham (contoh: BBCA):", "BBCA")

if ticker_input:

    ticker = ticker_input.upper() + ".JK"
    df = yf.download(ticker, period="6mo", auto_adjust=True)

    # Pastikan kolom jadi 1D
    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['Close'] = df['Close'].squeeze()
    df['High'] = df['High'].squeeze()
    df['Low'] = df['Low'].squeeze()
    df['Volume'] = df['Volume'].squeeze()


    if df.empty:
        st.error("Data tidak ditemukan.")
    else:

        # ======================
        # INDICATORS
        # ======================
        df['MA20'] = df['Close'].rolling(20).mean()
        df['MA50'] = df['Close'].rolling(50).mean()
        df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()

        macd = ta.trend.MACD(close=df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()


        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()

        df['ATR'] = ta.volatility.AverageTrueRange(
            df['High'], df['Low'], df['Close']
        ).average_true_range()

        df['Upper_ATR'] = df['Close'] + df['ATR']
        df['Lower_ATR'] = df['Close'] - df['ATR']

        # VWAP
        df['VWAP'] = (df['Close'] * df['Volume']).cumsum() / df['Volume'].cumsum()

        support = df['Low'][-30:].min()
        resistance = df['High'][-30:].max()

        # ======================
        # MULTI PANEL
        # ======================
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.5, 0.15, 0.2, 0.2]
        )

        # Panel 1 - Harga
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'],
                                 name='Harga', line=dict(color='cyan')), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'],
                                 name='MA20', line=dict(color='orange')), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['MA50'],
                                 name='MA50', line=dict(color='green')), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['VWAP'],
                                 name='VWAP', line=dict(color='yellow')), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['Upper_ATR'],
                                 name='Upper ATR', line=dict(color='gray', dash='dot')), row=1, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['Lower_ATR'],
                                 name='Lower ATR', line=dict(color='gray', dash='dot')), row=1, col=1)

        # Support & Resistance
        fig.add_hline(y=support, line_color="green", row=1, col=1)
        fig.add_hline(y=resistance, line_color="red", row=1, col=1)

        # Panel 2 - Volume
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'],
                             name='Volume', marker_color='gray'), row=2, col=1)

        # Panel 3 - MACD
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'],
                                 name='MACD', line=dict(color='blue')), row=3, col=1)

        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'],
                                 name='Signal', line=dict(color='orange')), row=3, col=1)

        # Panel 4 - RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'],
                                 name='RSI', line=dict(color='purple')), row=4, col=1)

        fig.add_hline(y=70, line_dash="dash", line_color="red", row=4, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=4, col=1)

        fig.update_layout(
            template="plotly_dark",
            height=900,
            title=f"{ticker} - TradingView Style Dashboard",
            showlegend=True
        )

        st.plotly_chart(fig, use_container_width=True)
