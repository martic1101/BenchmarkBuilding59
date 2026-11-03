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

GROUPS = {'Floor_G': ['zone_022_co2', 'zone_028_co2', 'zone_033_co2', 'zone_040_co2', 'zone_044_co2', 'zone_045_co2'], 'Floor_S': ['zone_052_co2', 'zone_058_co2', 'zone_062_co2', 'zone_068_co2', 'zone_072_co2']}

def transform(sources):
    df = _load(sources["zone_co2.csv"], "%Y/%m/%d %H:%M")
    binned = df.resample("1h", label="left", closed="left").mean()
    out = pd.DataFrame({g: binned[cols].mean(axis=1) for g, cols in GROUPS.items()})
    return _finish(out, ['Floor_G', 'Floor_S'])
