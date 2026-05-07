import os
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd

from config import settings
from indicators.core import ema, atr, swing_low, classify_session

BACKTEST_REF_PATH = Path(os.getcwd()) / 'data' / 'backtest_ref' / 'reference.parquet'


def _normalize_candles(df: pd.DataFrame) -> pd.DataFrame:
    if 'datetime' in df.columns:
        df = df.rename(columns={'datetime': 'timestamp'})
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df = df.sort_values('timestamp').reset_index(drop=True)
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]


def _weekday_name(timestamp: pd.Timestamp) -> str:
    names = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
    return names[timestamp.weekday()]


def generate_reference_snapshot(
    candles_1h_path: Path,
    candles_m15_path: Path,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    if output_path is None:
        output_path = BACKTEST_REF_PATH

    if not Path(candles_1h_path).exists() or not Path(candles_m15_path).exists():
        raise FileNotFoundError('Required candle files are missing for parity bootstrap.')

    df_1h = _normalize_candles(pd.read_parquet(candles_1h_path))
    df_m15 = _normalize_candles(pd.read_parquet(candles_m15_path))

    df_1h['ema20_1h'] = ema(df_1h['close'], settings.E1_EMA_FAST)
    df_1h['ema50_1h'] = ema(df_1h['close'], settings.E1_EMA_MID)
    df_1h['ema200_1h'] = ema(df_1h['close'], settings.E1_EMA_SLOW)
    df_1h['atr_1h'] = atr(df_1h, 14)
    df_1h['swing_low_10'] = swing_low(df_1h, 10)
    df_1h['swing_high_10'] = df_1h['high'].rolling(10).max()
    df_1h['session'] = df_1h['timestamp'].apply(lambda ts: classify_session(ts.hour, ts.minute).value)
    df_1h['weekday'] = df_1h['timestamp'].apply(_weekday_name)

    df_m15['atr_m15'] = atr(df_m15, 14)
    df_m15 = df_m15[['timestamp', 'atr_m15']].sort_values('timestamp')

    df_1h = df_1h.sort_values('timestamp')
    reference = pd.merge_asof(
        df_1h,
        df_m15,
        on='timestamp',
        direction='backward',
        tolerance=pd.Timedelta('15m')
    )

    reference = reference[['timestamp', 'ema20_1h', 'ema50_1h', 'ema200_1h', 'atr_1h', 'atr_m15', 'swing_low_10', 'swing_high_10', 'session', 'weekday']]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    reference.to_parquet(output_path, index=False)
    return reference


def main():
    root = Path(os.getcwd())
    candles_1h = root / 'data' / 'candles' / 'xauusd_1h.parquet'
    candles_m15 = root / 'data' / 'candles' / 'xauusd_m15.parquet'
    output_path = root / 'data' / 'backtest_ref' / 'reference.parquet'

    reference = generate_reference_snapshot(candles_1h, candles_m15, output_path)
    print(f'Parity reference snapshot written to: {output_path}')
    print(f'Rows generated: {len(reference)}')


if __name__ == '__main__':
    main()
