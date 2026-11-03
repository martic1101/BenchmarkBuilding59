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
    df = _load(sources["rtu_sa_t.csv"], "%Y-%m-%d %H:%M:%S")
    out = df[['rtu_002_sa_temp', 'rtu_003_sa_temp']].resample("30min", label="left", closed="left").mean()
    out = (out - 32) * 5 / 9
    out.columns = ['rtu_002_sa_temp_c', 'rtu_003_sa_temp_c']
    return _finish(out, ['rtu_002_sa_temp_c', 'rtu_003_sa_temp_c'])
