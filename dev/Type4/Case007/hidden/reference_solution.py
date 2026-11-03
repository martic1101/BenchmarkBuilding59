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

GROUPS = {'Floor_G': ['zone_016_temp', 'zone_017_temp', 'zone_018_temp', 'zone_019_temp', 'zone_021_temp', 'zone_022_temp', 'zone_023_temp', 'zone_024_temp', 'zone_025_temp', 'zone_026_temp', 'zone_027_temp', 'zone_028_temp', 'zone_030_temp', 'zone_032_temp', 'zone_033_temp', 'zone_035_temp', 'zone_036_temp', 'zone_037_temp', 'zone_038_temp', 'zone_039_temp', 'zone_040_temp', 'zone_041_temp', 'zone_042_temp', 'zone_043_temp', 'zone_044_temp', 'zone_045_temp'], 'Floor_S': ['zone_046_temp', 'zone_047_temp', 'zone_048_temp', 'zone_049_temp', 'zone_051_temp', 'zone_052_temp', 'zone_053_temp', 'zone_054_temp', 'zone_055_temp', 'zone_056_temp', 'zone_057_temp', 'zone_058_temp', 'zone_059_temp', 'zone_061_temp', 'zone_062_temp', 'zone_063_temp', 'zone_064_temp', 'zone_065_temp', 'zone_066_temp', 'zone_067_temp', 'zone_068_temp', 'zone_069_temp', 'zone_070_temp', 'zone_071_temp', 'zone_072_temp']}

def transform(sources):
    df = _load(sources["zone_temp_exterior.csv"], "%Y-%m-%d %H:%M:%S")
    binned = df.resample("1h", label="left", closed="left").mean()
    out = pd.DataFrame({g: binned[cols].mean(axis=1) for g, cols in GROUPS.items()})
    return _finish(out, ['Floor_G', 'Floor_S'])
