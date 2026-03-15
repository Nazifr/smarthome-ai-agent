import pandas as pd
import numpy as np

df = pd.read_csv('HomeC.csv')
df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
df = df.dropna(subset=['time'])
df['hour'] = df['time'].dt.hour
df['use_kw'] = pd.to_numeric(df['use [kW]'], errors='coerce')
df['solar_kw'] = pd.to_numeric(df['Solar [kW]'], errors='coerce').fillna(0)
df['motion'] = (df['use_kw'] > 1.0).astype(int)
df['is_weekend'] = (df['time'].dt.dayofweek >= 5).astype(int)

low  = df['use_kw'].quantile(0.33)
high = df['use_kw'].quantile(0.66)

print(f'low: {low:.2f} kW')
print(f'high: {high:.2f} kW')
print(f'motion=1: {df["motion"].sum():,} / {len(df):,} ({df["motion"].mean():.1%})')
print(f'is_weekend=1: {df["is_weekend"].sum():,} / {len(df):,} ({df["is_weekend"].mean():.1%})')
print(f'\nhour dagilimi:')
print(df['hour'].value_counts().sort_index().to_string())
