"""
Veri Hazırlama ve ML Model Eğitimi - v2

Senaryo bazlı etiketler:
    sabah_rutini, is_modu, dinlenme_modu,
    uyku_hazirlik, uyku_modu, ev_bos, misafir_modu

Çalıştırma:
    python train_model.py

Çıktı:
    models/decision_model.pkl
    models/label_encoder.pkl
    models/label_mapping.json
"""

import os
import json
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import SMOTE 
""" Oversample (SMOTE) — az olan etiketler için sentetik örnek üret."""

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
df = pd.read_csv(CSV_PATH)
print(f"   Satir: {len(df):,} | Kolon: {len(df.columns)}")

# ── 2. Zaman Ozellikleri ──────────────────────────────────────────────
print("\nZaman ozellikleri cıkarılıyor...")
df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
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

# ── 4. Dis Baglem (Placeholder) ───────────────────────────────────────
print("\nDis baglem simule ediliyor (placeholder)...")
np.random.seed(42)

df["weather"] = np.where(
    df["solar_kw"] > 1.0, 0,
    np.where(df["solar_kw"] > 0.1, 1, 2)
)
df["sentiment"]     = 0  # placeholder - Telegram entegrasyonu eklenince guncellenir
df["energy_price"]  = np.where(
    (df["hour"] >= 23) | (df["hour"] < 6), 0,
    np.where((df["hour"] >= 17) & (df["hour"] < 23), 2, 1)
)

# ── 5. Feature Set ────────────────────────────────────────────────────
features = [
    "hour", "minute", "day_of_week", "is_weekend", "day_type",
    "temperature", "humidity", "motion", "light",
    "weather", "sentiment", "energy_price"
]

df = df[features + ["use_kw"]].dropna()
print(f"   Temiz satir sayisi: {len(df):,}")

# ── 6. Etiket Olustur ─────────────────────────────────────────────────
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


# ── 7. Modeli Egit ────────────────────────────────────────────────────
print("Model egitiliyor...")
X  = df[features].values
le = LabelEncoder()
y  = le.fit_transform(df["label"].values)

# ── 6.5. SMOTE ile Dengeleme ──────────────────────────────────────────
print("\nSMOTE ile veri dengeleniyor...")
smote = SMOTE(random_state=42)
X_balanced, y_balanced = smote.fit_resample(X, y)
print(f"   Dengeli satir sayisi: {len(X_balanced):,}")
balanced_labels = le.inverse_transform(y_balanced)
import collections
print(f"   Yeni dagilim:\n{collections.Counter(balanced_labels)}")


X_train, X_test, y_train, y_test = train_test_split(
    X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
)

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_leaf=15,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# ── 8. Degerlendirme ──────────────────────────────────────────────────
print("\nModel Degerlendirmesi:")
y_pred = model.predict(X_test)
acc    = accuracy_score(y_test, y_pred)
print(f"   Dogruluk (Accuracy): {acc:.2%}")
print(f"\n{classification_report(y_test, y_pred, target_names=le.classes_)}")

print("\nFeature Onem Sirasi:")
importances = pd.Series(model.feature_importances_, index=features)
print(importances.sort_values(ascending=False).to_string())

# ── 9. Kaydet ─────────────────────────────────────────────────────────
joblib.dump(model, MODEL_PATH)
joblib.dump(le, ENCODER_PATH)
with open(MAPPING_PATH, "w", encoding="utf-8") as f:
    json.dump(LABEL_MAPPING, f, ensure_ascii=False, indent=2)

print(f"\nModel kaydedildi: {MODEL_PATH}")
print(f"Encoder kaydedildi: {ENCODER_PATH}")
print(f"Mapping kaydedildi: {MAPPING_PATH}")
print("\nEgitim tamamlandi!")
print("Sonraki adim: models/ klasorunu docker container'a kopyala")
