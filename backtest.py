# backtest.py

def simple_backtest(df):

    df['Signal'] = 0
    df.loc[df['MA20'] > df['MA50'], 'Signal'] = 1
    df['Position'] = df['Signal'].shift(1)

    df['Return'] = df['Close'].pct_change()
    df['Strategy_Return'] = df['Return'] * df['Position']

    cumulative_return = (1 + df['Strategy_Return']).cumprod()

    return cumulative_return.iloc[-1]
