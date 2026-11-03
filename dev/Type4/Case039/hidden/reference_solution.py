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

GROUPS = {'Floor_G': ['cerc_templogger_1', 'cerc_templogger_2', 'cerc_templogger_3', 'cerc_templogger_4', 'cerc_templogger_5', 'cerc_templogger_6', 'cerc_templogger_7', 'cerc_templogger_8'], 'Floor_S': ['cerc_templogger_10', 'cerc_templogger_11', 'cerc_templogger_12', 'cerc_templogger_13', 'cerc_templogger_14', 'cerc_templogger_15', 'cerc_templogger_16', 'cerc_templogger_9']}

def transform(sources):
    df = _load(sources["zone_temp_interior.csv"], "%Y-%m-%d %H:%M:%S")
    binned = df.resample("30min", label="left", closed="left").max()
    out = pd.DataFrame({g: binned[cols].max(axis=1) for g, cols in GROUPS.items()})
    return _finish(out, ['Floor_G', 'Floor_S'])
