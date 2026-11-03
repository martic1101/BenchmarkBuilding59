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
    parts = []
    parts.append(_load(sources["uft_fan_spd.csv"], "%Y-%m-%d %H:%M:%S")[['zone_026_fan_spd']].resample("1h", label="left", closed="left").min())
    parts.append(_load(sources["uft_hw_valve.csv"], "%Y-%m-%d %H:%M:%S")[['zone_052_hw_valve', 'zone_055_hw_valve']].resample("1h", label="left", closed="left").min())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['zone_026_fan_spd', 'zone_052_hw_valve', 'zone_055_hw_valve'])
