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
    parts.append(_load(sources["ashp_hw.csv"], "%Y-%m-%d %H:%M:%S")[['aru_001_hwr_temp', 'aru_001_hws_temp']].resample("30min", label="left", closed="left").min())
    parts.append(_load(sources["rtu_ra_t.csv"], "%Y/%m/%d %H:%M")[['rtu_002_ra_temp']].resample("30min", label="left", closed="left").min())
    parts.append(_load(sources["rtu_sa_t_sp.csv"], "%Y-%m-%d %H:%M:%S")[['rtu_004_sat_sp_tn']].resample("30min", label="left", closed="left").min())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['aru_001_hwr_temp', 'aru_001_hws_temp', 'rtu_002_ra_temp', 'rtu_004_sat_sp_tn'])
