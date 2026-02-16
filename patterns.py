# patterns.py

def support_resistance(df):
    support = df['Low'][-30:].min()
    resistance = df['High'][-30:].max()
    return support, resistance


def breakout_signal(df):
    resistance = df['High'][-20:].max()
    latest = df.iloc[-1]

    if latest['Close'] > resistance:
        return True
    return False
