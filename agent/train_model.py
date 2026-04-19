"""
Veri Hazırlama ve ML Model Eğitimi - v5

Dataset: SmartHomeEnergyConsumptionOptimization.csv
Model: LightGBM
Feature sayısı: 18
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

CSV_PATH     = "SmartHomeEnergyConsumptionOptimization.csv"
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

def ac_need_score(temp_diff, heat_idx, light_level):
    score = 0.0
    if temp_diff > 3:     score += 0.4
    elif temp_diff < -3:  score -= 0.3
    if heat_idx > 35:     score += 0.4
    elif heat_idx > 30:   score += 0.2
    if light_level > 500: score += 0.2
    return max(0.0, min(1.0, score))

def time_of_day(hour):
    if 0 <= hour < 6:      return 0
    elif 6 <= hour < 12:   return 1
    elif 12 <= hour < 18:  return 2
    else:                  return 3

# ── 1. Veriyi Yükle ───────────────────────────────────────────────────
print("Veri yukleniyor...")
df = pd.read_csv(CSV_PATH, low_memory=False)
print(f"   Satir: {len(df):,} | Kolon: {len(df.columns)}")

# ── 2. Cihaz Bazlı → Ev Bazlı ────────────────────────────────────────
print("\nVeri pivot'laniyor...")
df_home = (df.drop_duplicates(subset=["home_id", "timestamp"])
             .copy()
             .reset_index(drop=True))
print(f"   Ev bazli satir: {len(df_home):,}")

# ── 3. Zaman Özellikleri ──────────────────────────────────────────────
print("\nZaman ozellikleri...")
df_home["timestamp"] = pd.to_datetime(df_home["timestamp"], errors="coerce")
df_home = df_home.dropna(subset=["timestamp"]).reset_index(drop=True)
df_home["hour"]       = df_home["hour_of_day"].astype(int)
df_home["minute"]     = df_home["timestamp"].dt.minute.astype(int)
df_home["is_weekend"] = ((df_home["day_of_week"] >= 5).astype(int))
df_home["day_type"]   = df_home["is_weekend"]

# ── 4. Sensör Verileri ────────────────────────────────────────────────
print("\nSensor verileri...")
df_home["temperature"]  = pd.to_numeric(df_home["indoor_temp"],   errors="coerce")
df_home["humidity"]     = pd.to_numeric(df_home["humidity"],      errors="coerce")
df_home["outdoor_temp"] = pd.to_numeric(df_home["outdoor_temp"],  errors="coerce")
df_home["light"]        = pd.to_numeric(df_home["light_level"],   errors="coerce")
df_home["motion"]       = df_home["user_present"].astype(int)
df_home["power_watt"]   = pd.to_numeric(df_home["power_watt"],    errors="coerce").fillna(0)

# ── 5. Dış Bağlam ─────────────────────────────────────────────────────
print("\nDis baglem...")
df_home["weather"]   = np.where(df_home["light"] > 500, 0,
                       np.where(df_home["light"] > 100, 1, 2))
df_home["sentiment"] = 0

energy_raw = pd.to_numeric(df_home["price_kWh"], errors="coerce").fillna(1500)
df_home["energy_price_norm"] = np.where(energy_raw < 1200, 0,
                               np.where(energy_raw <= 1700, 1, 2)).astype(int)

# ── 6. Türetilmiş Feature'lar ─────────────────────────────────────────
print("\nYeni feature'lar...")
df_home = df_home.sort_values(["home_id", "timestamp"]).reset_index(drop=True)

df_home["temp_diff"]             = (df_home["temperature"] - df_home["outdoor_temp"]).round(1)
df_home["use_kw_rolling"]        = (df_home.groupby("home_id")["power_watt"]
                                     .transform(lambda x: x.rolling(6, min_periods=1).mean())
                                     / 1000.0)
df_home["time_of_day"]           = df_home["hour"].apply(time_of_day)
df_home["temp_hour_interaction"] = df_home["temperature"] * df_home["hour"] / 24.0
df_home["heat_index"]            = [heat_index(t, h) for t, h in
                                     zip(df_home["temperature"], df_home["humidity"])]
df_home["ac_need_score"]         = [ac_need_score(d, hi, l) for d, hi, l in
                                     zip(df_home["temp_diff"], df_home["heat_index"], df_home["light"])]

# ── 7. Feature Set ────────────────────────────────────────────────────
features = [
    "hour", "minute", "day_of_week", "is_weekend", "day_type",
    "temperature", "humidity", "motion", "light",
    "weather", "sentiment", "energy_price_norm",
    "temp_hour_interaction", "use_kw_rolling", "time_of_day",
    "temp_diff", "heat_index", "ac_need_score"
]

# activity ayrı tut, features listesinde yok
df_clean = df_home[features + ["activity"]].dropna().reset_index(drop=True)
print(f"   Temiz satir: {len(df_clean):,}")
print(f"   Feature sayisi: {len(features)}")

# ── 8. Etiket Oluştur ─────────────────────────────────────────────────
print("\nEtiketler olusturuluyor...")

activity = df_clean["activity"]
hour     = df_clean["hour"]
is_wknd  = df_home.loc[df_clean.index, "is_weekend"] if len(df_clean) == len(df_home) else df_clean.get("is_weekend", pd.Series(0, index=df_clean.index))

# np.select ile vektörize etiketleme
conditions = [
    (activity == "sleeping") & ((hour >= 21) | (hour < 6)),
    (activity == "sleeping"),
    (activity == "away"),
    (activity == "cooking") & hour.between(6, 9),
    (activity == "cooking"),
    (activity == "watching_tv") & ((hour >= 21) | (hour < 6)),
    (activity == "watching_tv"),
    (activity == "idle") & (df_clean["is_weekend"] == 1),
    (activity == "idle"),
]
choices = [
    "uyku_modu", "uyku_hazirlik", "ev_bos",
    "sabah_rutini", "dinlenme_modu",
    "uyku_hazirlik", "dinlenme_modu",
    "misafir_modu", "dinlenme_modu",
]
df_clean["label"] = np.select(conditions, choices, default="dinlenme_modu")

print(f"\n   Activity dagilimi:\n{activity.value_counts()}")
print(f"\n   Etiket dagilimi:\n{df_clean['label'].value_counts()}\n")

# ── 9. SMOTE ile Dengeleme ────────────────────────────────────────────
print("SMOTE ile dengeleniyor...")
X  = df_clean[features].values
le = LabelEncoder()
y  = le.fit_transform(df_clean["label"].values)

smote = SMOTE(random_state=42)
X_bal, y_bal = smote.fit_resample(X, y)
print(f"   Dengeli satir: {len(X_bal):,}")
print(f"   Yeni dagilim: {collections.Counter(le.inverse_transform(y_bal))}")

X_tr, X_te, y_tr, y_te = train_test_split(
    X_bal, y_bal, test_size=0.2, random_state=42, stratify=y_bal
)

# ── 10. LightGBM ──────────────────────────────────────────────────────
print("\nLightGBM egitiliyor...")
model = LGBMClassifier(
    n_estimators=500, learning_rate=0.05, max_depth=8,
    num_leaves=63, min_child_samples=20,
    subsample=0.8, colsample_bytree=0.8,
    random_state=42, n_jobs=-1, verbose=-1
)
model.fit(X_tr, y_tr)

# ── 11. Değerlendirme ─────────────────────────────────────────────────
print("\nModel Degerlendirmesi:")
y_pred = model.predict(X_te)
acc    = accuracy_score(y_te, y_pred)
print(f"   Dogruluk: {acc:.2%}")
print(f"\n{classification_report(y_te, y_pred, target_names=le.classes_)}")
print("\nFeature Onem Sirasi:")
print(pd.Series(model.feature_importances_, index=features)
        .sort_values(ascending=False).to_string())

# ── 12. Kaydet ────────────────────────────────────────────────────────
joblib.dump(model, MODEL_PATH)
joblib.dump(le, ENCODER_PATH)
with open(MAPPING_PATH, "w", encoding="utf-8") as f:
    json.dump(LABEL_MAPPING, f, ensure_ascii=False, indent=2)

print(f"\nModel kaydedildi: {MODEL_PATH}")
print(f"Encoder kaydedildi: {ENCODER_PATH}")
print("\nEgitim tamamlandi!")
