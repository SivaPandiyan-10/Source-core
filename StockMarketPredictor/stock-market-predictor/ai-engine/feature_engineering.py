import pandas as pd
import ta

def generate_features(df: pd.DataFrame):
    df = df.copy()
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd()
    df['sma'] = ta.trend.SMAIndicator(df['close']).sma_indicator()
    df['ema'] = ta.trend.EMAIndicator(df['close']).ema_indicator()
    df['momentum'] = ta.momentum.ROCIndicator(df['close']).roc()
    df['volatility'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
    df['volume_change'] = df['volume'].pct_change()
    df = df.dropna()
    X = df[['rsi', 'macd', 'sma', 'ema', 'momentum', 'volatility', 'volume_change']]
    y = (df['close'].shift(-1) > df['close']).astype(int)[:-1]
    X = X[:-1]
    return X, y
