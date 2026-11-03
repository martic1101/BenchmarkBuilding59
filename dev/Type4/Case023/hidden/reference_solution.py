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

GROUPS = {'RTU01': ['zone_016_cooling_sp', 'zone_017_cooling_sp', 'zone_021_cooling_sp', 'zone_023_cooling_sp', 'zone_024_cooling_sp', 'zone_046_cooling_sp', 'zone_047_cooling_sp', 'zone_051_cooling_sp', 'zone_053_cooling_sp', 'zone_054_cooling_sp'], 'RTU02': ['zone_018_cooling_sp', 'zone_019_cooling_sp', 'zone_025_cooling_sp', 'zone_026_cooling_sp', 'zone_048_cooling_sp', 'zone_055_cooling_sp', 'zone_056_cooling_sp', 'zone_061_cooling_sp'], 'RTU03': ['zone_027_cooling_sp', 'zone_030_cooling_sp', 'zone_032_cooling_sp', 'zone_035_cooling_sp', 'zone_036_cooling_sp', 'zone_043_cooling_sp', 'zone_049_cooling_sp', 'zone_057_cooling_sp', 'zone_059_cooling_sp', 'zone_062_cooling_sp', 'zone_063_cooling_sp', 'zone_064_cooling_sp', 'zone_071_cooling_sp'], 'RTU04': ['zone_037_cooling_sp', 'zone_038_cooling_sp', 'zone_039_cooling_sp', 'zone_041_cooling_sp', 'zone_042_cooling_sp', 'zone_065_cooling_sp', 'zone_066_cooling_sp', 'zone_067_cooling_sp', 'zone_069_cooling_sp', 'zone_070_cooling_sp']}

def transform(sources):
    df = _load(sources["zone_temp_sp_c.csv"], "%Y/%m/%d %H:%M")
    binned = df.resample("30min", label="left", closed="left").mean()
    out = pd.DataFrame({g: binned[cols].mean(axis=1) for g, cols in GROUPS.items()})
    return _finish(out, ['RTU01', 'RTU02', 'RTU03', 'RTU04'])
