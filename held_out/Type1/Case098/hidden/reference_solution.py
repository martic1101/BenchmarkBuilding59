import pandas as pd

def _load(path, fmt):
    df = pd.read_csv(path, dtype={0: str}, na_values=["NaN", "nan", ""])
    idx = pd.to_datetime(df.iloc[:, 0], format=fmt)
    df = df.drop(columns=df.columns[0]).apply(pd.to_numeric, errors="coerce")
    df.index = idx
    return df

def _finish(out, cols):
    out.index.name = "timestamp"
    out = out.reset_index()
    out["timestamp"] = out["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return out[["timestamp"] + cols]

def transform(sources):
    df = _load(sources["uft_fan_spd.csv"], "%Y-%m-%d %H:%M:%S")
    out = df[['zone_022_fan_spd', 'zone_046_fan_spd', 'zone_064_fan_spd']].resample("1h", label="left", closed="left").mean()
    out = out
    out.columns = ['zone_022_fan_spd', 'zone_046_fan_spd', 'zone_064_fan_spd']
    return _finish(out, ['zone_022_fan_spd', 'zone_046_fan_spd', 'zone_064_fan_spd'])
