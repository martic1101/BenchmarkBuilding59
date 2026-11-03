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
    df = _load(sources["occ.csv"], "%Y-%m-%d %H:%M:%S")
    out = df[['occ_fourth_south', 'occ_third_south']].resample("1h", label="left", closed="left").max()
    out = out
    out.columns = ['occ_fourth_south', 'occ_third_south']
    return _finish(out, ['occ_fourth_south', 'occ_third_south'])
