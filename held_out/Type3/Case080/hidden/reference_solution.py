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
    parts.append(_load(sources["ashp_cw.csv"], "%Y-%m-%d %H:%M:%S")[['aru_001_cwr_temp', 'aru_001_cws_temp']].resample("1h", label="left", closed="left").min())
    parts.append(_load(sources["zone_temp_interior.csv"], "%Y-%m-%d %H:%M:%S")[['cerc_templogger_16', 'cerc_templogger_5']].resample("1h", label="left", closed="left").min())
    out = pd.concat(parts, axis=1, join="inner")
    out = out.rename(columns={})
    return _finish(out, ['aru_001_cwr_temp', 'aru_001_cws_temp', 'cerc_templogger_16', 'cerc_templogger_5'])
