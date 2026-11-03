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
    parts.append(_load(sources["site_weather.csv"], "%Y-%m-%d %H:%M:%S")[['air_temp_set_1', 'air_temp_set_2']].resample("1h", label="left", closed="left").mean())
    parts.append(_load(sources["zone_temp_exterior.csv"], "%Y-%m-%d %H:%M:%S")[['zone_027_temp']].resample("1h", label="left", closed="left").mean())
    parts.append(_load(sources["zone_temp_sp_h.csv"], "%Y/%m/%d %H:%M")[['zone_017_heating_sp', 'zone_059_heating_sp']].resample("1h", label="left", closed="left").mean())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['air_temp_set_1', 'air_temp_set_2', 'zone_027_temp', 'zone_017_heating_sp', 'zone_059_heating_sp'])
