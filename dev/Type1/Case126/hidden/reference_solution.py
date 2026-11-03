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
    df = _load(sources["zone_temp_sp_c.csv"], "%Y/%m/%d %H:%M")
    out = df[['zone_023_cooling_sp', 'zone_027_cooling_sp', 'zone_048_cooling_sp']].resample("30min", label="left", closed="left").mean()
    out = out
    out.columns = ['zone_023_cooling_sp', 'zone_027_cooling_sp', 'zone_048_cooling_sp']
    return _finish(out, ['zone_023_cooling_sp', 'zone_027_cooling_sp', 'zone_048_cooling_sp'])
