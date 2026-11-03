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
    parts.append(_load(sources["ele.csv"], "%Y/%m/%d %H:%M")[['hvac_S', 'mels_S']].resample("15min", label="left", closed="left").min())
    parts.append(_load(sources["rtu_fan_spd.csv"], "%Y-%m-%d %H:%M:%S")[['rtu_001_rf_vfd_spd_fbk_tn', 'rtu_004_sf_vfd_spd_fbk_tn']].resample("15min", label="left", closed="left").min())
    parts.append(_load(sources["site_weather.csv"], "%Y-%m-%d %H:%M:%S")[['relative_humidity_set_1', 'solar_radiation_set_1']].resample("15min", label="left", closed="left").min())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['hvac_S', 'mels_S', 'rtu_001_rf_vfd_spd_fbk_tn', 'rtu_004_sf_vfd_spd_fbk_tn', 'relative_humidity_set_1', 'solar_radiation_set_1'])
