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

GROUPS = {'RTU01': ['zone_016_heating_sp', 'zone_017_heating_sp', 'zone_021_heating_sp', 'zone_023_heating_sp', 'zone_024_heating_sp', 'zone_046_heating_sp', 'zone_047_heating_sp', 'zone_051_heating_sp', 'zone_053_heating_sp', 'zone_054_heating_sp'], 'RTU02': ['zone_018_heating_sp', 'zone_019_heating_sp', 'zone_025_heating_sp', 'zone_026_heating_sp', 'zone_048_heating_sp', 'zone_055_heating_sp', 'zone_056_heating_sp', 'zone_061_heating_sp'], 'RTU03': ['zone_027_heating_sp', 'zone_030_heating_sp', 'zone_032_heating_sp', 'zone_035_heating_sp', 'zone_036_heating_sp', 'zone_043_heating_sp', 'zone_049_heating_sp', 'zone_057_heating_sp', 'zone_059_heating_sp', 'zone_062_heating_sp', 'zone_063_heating_sp', 'zone_064_heating_sp', 'zone_071_heating_sp'], 'RTU04': ['zone_037_heating_sp', 'zone_038_heating_sp', 'zone_039_heating_sp', 'zone_041_heating_sp', 'zone_042_heating_sp', 'zone_065_heating_sp', 'zone_066_heating_sp', 'zone_067_heating_sp', 'zone_069_heating_sp', 'zone_070_heating_sp']}

def transform(sources):
    df = _load(sources["zone_temp_sp_h.csv"], "%Y/%m/%d %H:%M")
    binned = df.resample("1h", label="left", closed="left").mean()
    out = pd.DataFrame({g: binned[cols].min(axis=1) for g, cols in GROUPS.items()})
    return _finish(out, ['RTU01', 'RTU02', 'RTU03', 'RTU04'])
