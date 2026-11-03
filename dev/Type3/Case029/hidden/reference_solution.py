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
    parts.append(_load(sources["ashp_cw.csv"], "%Y-%m-%d %H:%M:%S")[['aru_001_cws_fr_gpm']].resample("30min", label="left", closed="left").mean())
    parts.append(_load(sources["rtu_econ_sp.csv"], "%Y/%m/%d %H:%M")[['rtu_001_econ_stpt_tn', 'rtu_002_econ_stpt_tn']].resample("30min", label="left", closed="left").mean())
    parts.append(_load(sources["rtu_oa_damper.csv"], "%Y/%m/%d %H:%M")[['rtu_002_oadmpr_pct', 'rtu_004_oadmpr_pct']].resample("30min", label="left", closed="left").mean())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['aru_001_cws_fr_gpm', 'rtu_001_econ_stpt_tn', 'rtu_002_econ_stpt_tn', 'rtu_002_oadmpr_pct', 'rtu_004_oadmpr_pct'])
