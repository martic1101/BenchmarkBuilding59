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
    parts.append(_load(sources["rtu_oa_damper.csv"], "%Y/%m/%d %H:%M")[['rtu_002_oadmpr_pct']].resample("1h", label="left", closed="left").min())
    parts.append(_load(sources["rtu_sa_t_sp.csv"], "%Y-%m-%d %H:%M:%S")[['rtu_001_sat_sp_tn', 'rtu_004_sat_sp_tn']].resample("1h", label="left", closed="left").min())
    parts.append(_load(sources["wifi.csv"], "%Y/%m/%d %H:%M")[['wifi_second_south', 'wifi_third_south']].resample("1h", label="left", closed="left").min())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['rtu_002_oadmpr_pct', 'rtu_001_sat_sp_tn', 'rtu_004_sat_sp_tn', 'wifi_second_south', 'wifi_third_south'])
