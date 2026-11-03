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

GROUPS = {'RTU01': ['zone_016_fan_spd', 'zone_017_fan_spd', 'zone_021_fan_spd', 'zone_022_fan_spd', 'zone_023_fan_spd', 'zone_024_fan_spd', 'zone_046_fan_spd', 'zone_047_fan_spd', 'zone_051_fan_spd', 'zone_053_fan_spd', 'zone_054_fan_spd'], 'RTU02': ['zone_018_fan_spd', 'zone_019_fan_spd', 'zone_025_fan_spd', 'zone_026_fan_spd', 'zone_045_fan_spd', 'zone_048_fan_spd', 'zone_052_fan_spd', 'zone_055_fan_spd', 'zone_056_fan_spd', 'zone_061_fan_spd'], 'RTU03': ['zone_027_fan_spd', 'zone_028_fan_spd', 'zone_030_fan_spd', 'zone_032_fan_spd', 'zone_033_fan_spd', 'zone_035_fan_spd', 'zone_036_fan_spd', 'zone_043_fan_spd', 'zone_044_fan_spd', 'zone_049_fan_spd', 'zone_057_fan_spd', 'zone_058_fan_spd', 'zone_059_fan_spd', 'zone_062_fan_spd', 'zone_063_fan_spd', 'zone_064_fan_spd', 'zone_071_fan_spd', 'zone_072_fan_spd'], 'RTU04': ['zone_037_fan_spd', 'zone_038_fan_spd', 'zone_039_fan_spd', 'zone_040_fan_spd', 'zone_041_fan_spd', 'zone_042_fan_spd', 'zone_065_fan_spd', 'zone_066_fan_spd', 'zone_067_fan_spd', 'zone_068_fan_spd', 'zone_069_fan_spd', 'zone_070_fan_spd']}

def transform(sources):
    df = _load(sources["uft_fan_spd.csv"], "%Y-%m-%d %H:%M:%S")
    binned = df.resample("1h", label="left", closed="left").mean()
    out = pd.DataFrame({g: binned[cols].mean(axis=1) for g, cols in GROUPS.items()})
    return _finish(out, ['RTU01', 'RTU02', 'RTU03', 'RTU04'])
