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
    df = _load(sources["site_weather.csv"], "%Y-%m-%d %H:%M:%S")
    out = df[['air_temp_set_1', 'air_temp_set_2']].resample("30min", label="left", closed="left").mean()
    out = out * 9 / 5 + 32
    out.columns = ['air_temp_set_1_f', 'air_temp_set_2_f']
    return _finish(out, ['air_temp_set_1_f', 'air_temp_set_2_f'])
