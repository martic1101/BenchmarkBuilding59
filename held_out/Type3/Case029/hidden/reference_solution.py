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
    parts.append(_load(sources["rtu_sa_t_sp.csv"], "%Y-%m-%d %H:%M:%S")[['rtu_002_sat_sp_tn', 'rtu_003_sat_sp_tn']].resample("15min", label="left", closed="left").max())
    parts.append(_load(sources["site_weather.csv"], "%Y-%m-%d %H:%M:%S")[['air_temp_set_2', 'dew_point_temperature_set_1d']].resample("15min", label="left", closed="left").max())
    parts.append(_load(sources["zone_temp_sp_c.csv"], "%Y/%m/%d %H:%M")[['zone_032_cooling_sp', 'zone_061_cooling_sp']].resample("15min", label="left", closed="left").max())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['rtu_002_sat_sp_tn', 'rtu_003_sat_sp_tn', 'air_temp_set_2', 'dew_point_temperature_set_1d', 'zone_032_cooling_sp', 'zone_061_cooling_sp'])
