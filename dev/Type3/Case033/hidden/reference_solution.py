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
    parts.append(_load(sources["rtu_fan_spd.csv"], "%Y-%m-%d %H:%M:%S")[['rtu_002_rf_vfd_spd_fbk_tn']].resample("15min", label="left", closed="left").mean())
    parts.append(_load(sources["rtu_sa_t_sp.csv"], "%Y-%m-%d %H:%M:%S")[['rtu_003_sat_sp_tn']].resample("15min", label="left", closed="left").mean())
    parts.append(_load(sources["uft_hw_valve.csv"], "%Y-%m-%d %H:%M:%S")[['zone_038_hw_valve', 'zone_070_hw_valve']].resample("15min", label="left", closed="left").mean())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['rtu_002_rf_vfd_spd_fbk_tn', 'rtu_003_sat_sp_tn', 'zone_038_hw_valve', 'zone_070_hw_valve'])
