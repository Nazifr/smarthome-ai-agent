"""
Veri Hazırlama ve ML Model Eğitimi - v3 (LightGBM)

Senaryo bazlı etiketler:
    sabah_rutini, is_modu, dinlenme_modu,
    uyku_hazirlik, uyku_modu, ev_bos, misafir_modu

Model: LightGBM (Random Forest'tan daha yüksek doğruluk)

Çalıştırma:
    pip install lightgbm
    python train_model.py
"""

import os
import json
import collections
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

# ── Etiket → Cihaz Komutları Mapping ─────────────────────────────────
LABEL_MAPPING = {
    "sabah_rutini":   {"ac": "COOL_LOW",  "lights": "ON",  "fan": "OFF", "music": "enerjik"},
    "is_modu":        {"ac": "COOL_LOW",  "lights": "ON",  "fan": "OFF", "music": "odak"},
    "dinlenme_modu":  {"ac": "COOL_LOW",  "lights": "DIM", "fan": "ON",  "music": "sakin"},
    "uyku_hazirlik":  {"ac": "COOL_LOW",  "lights": "DIM", "fan": "OFF", "music": "fisiltı"},
    "uyku_modu":      {"ac": "COOL_LOW",  "lights": "OFF", "fan": "OFF", "music": "kapali"},
    "ev_bos":         {"ac": "OFF",       "lights": "OFF", "fan": "OFF", "music": "kapali"},
    "misafir_modu":   {"ac": "COOL_LOW",  "lights": "ON",  "fan": "OFF", "music": "keyifli"},
}

# ── 1. Veriyi Yükle ───────────────────────────────────────────────────
print("Veri yukleniyor...")
df = pd.read_csv(CSV_PATH, low_memory=False)
print(f"   Satir: {len(df):,} | Kolon: {len(df.columns)}")

# ── 2. Zaman Ozellikleri ──────────────────────────────────────────────
print("\nZaman ozellikleri cıkarılıyor...")
# df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
df["time"] = pd.to_datetime(df["time"].astype(float), unit="s", errors="coerce")

df = df.dropna(subset=["time"])
df["hour"]        = df["time"].dt.hour
df["minute"]      = df["time"].dt.minute
df["day_of_week"] = df["time"].dt.dayofweek
df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)
df["day_type"]    = df["is_weekend"]

# ── 3. Sensor Verileri ────────────────────────────────────────────────
print("\nSensor verileri hazirlaniyor...")
df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
df["humidity"]    = pd.to_numeric(df["humidity"], errors="coerce")
df["use_kw"]      = pd.to_numeric(df["use [kW]"], errors="coerce")
df["solar_kw"]    = pd.to_numeric(df["Solar [kW]"], errors="coerce").fillna(0)
df["light"]       = df["solar_kw"] * 500
df["motion"]      = (df["use_kw"] > 1.0).astype(int)

# ── 4. Yeni Feature'lar ───────────────────────────────────────────────
print("\nYeni feature'lar hesaplaniyor...")

# İç/dış sıcaklık farkı (dış sıcaklık yoksa temperature'u kullan)
df["temp_hour_interaction"] = df["temperature"] * df["hour"] / 24.0

# Saatlik enerji tüketim trendi (son 1 saatteki ortalama)
df = df.sort_values("time")
df["use_kw_rolling"] = df["use_kw"].rolling(window=120, min_periods=1).mean()

# Sabah mı akşam mı? (0=gece, 1=sabah, 2=öğlen, 3=akşam)
def time_of_day(hour):
    if 0 <= hour < 6:   return 0
    elif 6 <= hour < 12: return 1
    elif 12 <= hour < 18: return 2
    else: return 3

df["time_of_day"] = df["hour"].apply(time_of_day)

# ── 5. Dis Baglem (Placeholder) ───────────────────────────────────────
print("\nDis baglem simule ediliyor...")
np.random.seed(42)

df["weather"] = np.where(
    df["solar_kw"] > 1.0, 0,
    np.where(df["solar_kw"] > 0.1, 1, 2)
)
df["sentiment"]    = 0
df["energy_price"] = np.where(
    (df["hour"] >= 23) | (df["hour"] < 6), 0,
    np.where((df["hour"] >= 17) & (df["hour"] < 23), 2, 1)
)

# ── 6. Feature Set ────────────────────────────────────────────────────
features = [
    "hour", "minute", "day_of_week", "is_weekend", "day_type",
    "temperature", "humidity", "motion", "light",
    "weather", "sentiment", "energy_price",
    "temp_hour_interaction", "use_kw_rolling", "time_of_day"
]

df = df[features + ["use_kw"]].dropna()
print(f"   Temiz satir sayisi: {len(df):,}")
print(f"   Feature sayisi: {len(features)}")

# ── 7. Etiket Olustur ─────────────────────────────────────────────────
print("\nSenaryo bazli etiketler olusturuluyor...")

low  = df["use_kw"].quantile(0.33)
high = df["use_kw"].quantile(0.66)

def assign_label(row):
    hour       = row["hour"]
    motion     = row["motion"]
    use        = row["use_kw"]
    is_weekend = row["is_weekend"]

    if (0 <= hour < 6) and use < low:
        return "uyku_modu"
    if (22 <= hour < 24) and motion == 1:
        return "uyku_hazirlik"
    if (6 <= hour < 9) and motion == 1:
        return "sabah_rutini"
    if (9 <= hour < 17) and motion == 1 and is_weekend == 0:
        return "is_modu"
    if is_weekend == 1 and (10 <= hour < 22) and use >= high:
        return "misafir_modu"
    if (17 <= hour < 22) and motion == 1:
        return "dinlenme_modu"
    if is_weekend == 1 and (9 <= hour < 12) and motion == 1:
        return "dinlenme_modu"
    if motion == 0 and use < low:
        return "ev_bos"
    return "dinlenme_modu"

df["label"] = df.apply(assign_label, axis=1)
print(f"\n   Etiket dagilimi:\n{df['label'].value_counts()}\n")

# ── 8. SMOTE ile Dengeleme ────────────────────────────────────────────
print("SMOTE ile veri dengeleniyor...")
X  = df[features].values
le = LabelEncoder()
y  = le.fit_transform(df["label"].values)

smote = SMOTE(random_state=42)
X_balanced, y_balanced = smote.fit_resample(X, y)
print(f"   Dengeli satir sayisi: {len(X_balanced):,}")
print(f"   Yeni dagilim:\n{collections.Counter(le.inverse_transform(y_balanced))}")

X_train, X_test, y_train, y_test = train_test_split(
    X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
)

# ── 9. LightGBM Modeli Egit ───────────────────────────────────────────
print("\nLightGBM modeli egitiliyor...")
model = LGBMClassifier(
    n_estimators=500,        # daha fazla ağaç
    learning_rate=0.05,      # yavaş ama dikkatli öğren
    max_depth=8,
    num_leaves=63,           # LightGBM'in temel parametresi
    min_child_samples=20,
    subsample=0.8,           # her ağaçta verinin %80'ini kullan
    colsample_bytree=0.8,    # her ağaçta feature'ların %80'ini kullan
    random_state=42,
    n_jobs=-1,
    verbose=-1               # gereksiz log basma
)
model.fit(X_train, y_train)

# ── 10. Degerlendirme ─────────────────────────────────────────────────
print("\nModel Degerlendirmesi:")
y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"   Dogruluk (Accuracy): {acc:.2%}")
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
print(f"Mapping kaydedildi: {MAPPING_PATH}")
print("\nEgitim tamamlandi!")
