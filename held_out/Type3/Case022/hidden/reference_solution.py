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
    parts.append(_load(sources["rtu_oa_t.csv"], "%Y/%m/%d %H:%M")[['rtu_002_oa_temp', 'rtu_004_oa_temp']].resample("1h", label="left", closed="left").max())
    parts.append(_load(sources["site_weather.csv"], "%Y-%m-%d %H:%M:%S")[['solar_radiation_set_1']].resample("1h", label="left", closed="left").max())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['rtu_002_oa_temp', 'rtu_004_oa_temp', 'solar_radiation_set_1'])
