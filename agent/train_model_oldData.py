"""
Veri Hazırlama ve ML Model Eğitimi - v4

Model: LightGBM
Feature sayısı: 18 (iç/dış sıcaklık farkı, heat index, AC ihtiyaç skoru eklendi)

Çalıştırma:
    python train_model.py
"""

import os
import json
import collections
import math
import pandas as pd
import numpy as np
import joblib
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import SMOTE

CSV_PATH     = "HomeC.csv"
MODEL_DIR    = "models"
MODEL_PATH   = os.path.join(MODEL_DIR, "decision_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
MAPPING_PATH = os.path.join(MODEL_DIR, "label_mapping.json")

os.makedirs(MODEL_DIR, exist_ok=True)

LABEL_MAPPING = {
    "sabah_rutini":   {"ac": "COOL_LOW",  "lights": "ON",  "fan": "OFF", "music": "enerjik"},
    "is_modu":        {"ac": "COOL_LOW",  "lights": "ON",  "fan": "OFF", "music": "odak"},
    "dinlenme_modu":  {"ac": "COOL_LOW",  "lights": "DIM", "fan": "ON",  "music": "sakin"},
    "uyku_hazirlik":  {"ac": "COOL_LOW",  "lights": "DIM", "fan": "OFF", "music": "fisiltı"},
    "uyku_modu":      {"ac": "COOL_LOW",  "lights": "OFF", "fan": "OFF", "music": "kapali"},
    "ev_bos":         {"ac": "OFF",       "lights": "OFF", "fan": "OFF", "music": "kapali"},
    "misafir_modu":   {"ac": "COOL_LOW",  "lights": "ON",  "fan": "OFF", "music": "keyifli"},
}

# ── Yardımcı Fonksiyonlar ─────────────────────────────────────────────

def heat_index(temp_c, humidity):
    if temp_c < 27:
        return temp_c
    T, R = temp_c, humidity
    hi = (-8.78469475556 + 1.61139411*T + 2.33854883889*R
          - 0.14611605*T*R - 0.012308094*T**2
          - 0.0164248277778*R**2 + 0.002211732*T**2*R
          + 0.00072546*T*R**2 - 0.000003582*T**2*R**2)
    return round(hi, 1)

def ac_need_score(temp_diff, heat_idx, solar_kw):
    score = 0.0
    if temp_diff > 3:    score += 0.4
    elif temp_diff < -3: score -= 0.3
    if heat_idx > 35:    score += 0.4
    elif heat_idx > 30:  score += 0.2
    if solar_kw > 2.0:   score += 0.2
    return max(0.0, min(1.0, score))

def time_of_day(hour):
    if 0 <= hour < 6:    return 0
    elif 6 <= hour < 12: return 1
    elif 12 <= hour < 18: return 2
    else:                return 3

# ── 1. Veriyi Yükle ───────────────────────────────────────────────────
print("Veri yukleniyor...")
df = pd.read_csv(CSV_PATH, low_memory=False)
print(f"   Satir: {len(df):,} | Kolon: {len(df.columns)}")

# ── 2. Zaman Ozellikleri ──────────────────────────────────────────────
print("\nZaman ozellikleri...")
# df["time"]        = pd.to_datetime(df["time"].astype(float), unit="s", errors="coerce")
df["time"] = pd.to_datetime(pd.to_numeric(df["time"], errors="coerce"), unit="s", errors="coerce")

df                = df.dropna(subset=["time"])
df["hour"]        = df["time"].dt.hour
df["minute"]      = df["time"].dt.minute
df["day_of_week"] = df["time"].dt.dayofweek
df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)
df["day_type"]    = df["is_weekend"]

# ── 3. Sensor Verileri ────────────────────────────────────────────────
print("\nSensor verileri...")
df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
df["humidity"]    = pd.to_numeric(df["humidity"], errors="coerce")
df["use_kw"]      = pd.to_numeric(df["use [kW]"], errors="coerce")
df["solar_kw"]    = pd.to_numeric(df["Solar [kW]"], errors="coerce").fillna(0)
df["light"]       = df["solar_kw"] * 500
df["motion"]      = (df["use_kw"] > 1.0).astype(int)

# ── 4. Dis Baglem (Placeholder) ───────────────────────────────────────
print("\nDis baglem...")
np.random.seed(42)
df["weather"]      = np.where(df["solar_kw"] > 1.0, 0, np.where(df["solar_kw"] > 0.1, 1, 2))
df["sentiment"]    = 0
df["energy_price"] = np.where((df["hour"] >= 23) | (df["hour"] < 6), 0,
                    np.where((df["hour"] >= 17) & (df["hour"] < 23), 2, 1))

# ── 5. Yeni Feature'lar ───────────────────────────────────────────────
print("\nYeni feature'lar hesaplaniyor...")
df = df.sort_values("time")

# Enerji tüketim trendi
df["use_kw_rolling"] = df["use_kw"].rolling(window=120, min_periods=1).mean()

# Zaman dilimleri
df["time_of_day"]    = df["hour"].apply(time_of_day)

# Sıcaklık × saat etkileşimi
df["temp_hour_interaction"] = df["temperature"] * df["hour"] / 24.0

# İç/dış sıcaklık farkı — outdoor_temp yok, temperature proxy olarak kullan
# Gündüz solar yüksekse ev dışarıdan sıcak, gece ise soğuk varsayımı
df["outdoor_temp_est"] = df["temperature"] - (df["solar_kw"] * 2.0)
df["temp_diff"]        = df["temperature"] - df["outdoor_temp_est"]

# Hissedilen sıcaklık (Heat Index)
df["heat_index"]    = df.apply(lambda r: heat_index(r["temperature"], r["humidity"]), axis=1)

# AC ihtiyaç skoru
df["ac_need_score"] = df.apply(
    lambda r: ac_need_score(r["temp_diff"], r["heat_index"], r["solar_kw"]), axis=1
)

# ── 6. Feature Set ────────────────────────────────────────────────────
features = [
    "hour", "minute", "day_of_week", "is_weekend", "day_type",
    "temperature", "humidity", "motion", "light",
    "weather", "sentiment", "energy_price",
    "temp_hour_interaction", "use_kw_rolling", "time_of_day",
    "temp_diff", "heat_index", "ac_need_score"
]

df = df[features + ["use_kw"]].dropna()
print(f"   Temiz satir sayisi: {len(df):,}")
print(f"   Feature sayisi: {len(features)}")

# ── 7. Etiket Olustur ─────────────────────────────────────────────────
print("\nEtiketler olusturuluyor...")
low  = df["use_kw"].quantile(0.33)
high = df["use_kw"].quantile(0.66)

def assign_label(row):
    hour       = row["hour"]
    motion     = row["motion"]
    use        = row["use_kw"]
    is_weekend = row["is_weekend"]
    if (0 <= hour < 6) and use < low:                              return "uyku_modu"
    if (22 <= hour < 24) and motion == 1:                          return "uyku_hazirlik"
    if (6 <= hour < 9) and motion == 1:                            return "sabah_rutini"
    if (9 <= hour < 17) and motion == 1 and is_weekend == 0:      return "is_modu"
    if is_weekend == 1 and (10 <= hour < 22) and use >= high:     return "misafir_modu"
    if (17 <= hour < 22) and motion == 1:                          return "dinlenme_modu"
    if is_weekend == 1 and (9 <= hour < 12) and motion == 1:      return "dinlenme_modu"
    if motion == 0 and use < low:                                  return "ev_bos"
    return "dinlenme_modu"

df["label"] = df.apply(assign_label, axis=1)
print(f"\n   Etiket dagilimi:\n{df['label'].value_counts()}\n")

# ── 8. SMOTE ile Dengeleme ────────────────────────────────────────────
print("SMOTE ile dengeleniyor...")
X  = df[features].values
le = LabelEncoder()
y  = le.fit_transform(df["label"].values)

smote = SMOTE(random_state=42)
X_balanced, y_balanced = smote.fit_resample(X, y)
print(f"   Dengeli satir: {len(X_balanced):,}")

X_train, X_test, y_train, y_test = train_test_split(
    X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
)

# ── 9. LightGBM ───────────────────────────────────────────────────────
print("\nLightGBM egitiliyor...")
model = LGBMClassifier(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=8,
    num_leaves=63,
    min_child_samples=20,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    verbose=-1
)
model.fit(X_train, y_train)

# ── 10. Degerlendirme ─────────────────────────────────────────────────
print("\nModel Degerlendirmesi:")
y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"   Dogruluk: {acc:.2%}")
print(f"\n{classification_report(y_test, y_pred, target_names=le.classes_)}")

print("\nFeature Onem Sirasi:")
importances = pd.Series(model.feature_importances_, index=features)
print(importances.sort_values(ascending=False).to_string())

# ── 11. Kaydet ────────────────────────────────────────────────────────
joblib.dump(model, MODEL_PATH)
joblib.dump(le, ENCODER_PATH)
with open(MAPPING_PATH, "w", encoding="utf-8") as f:
    json.dump(LABEL_MAPPING, f, ensure_ascii=False, indent=2)

print(f"\nModel kaydedildi: {MODEL_PATH}")
print(f"Encoder kaydedildi: {ENCODER_PATH}")
print("\nEgitim tamamlandi!")
