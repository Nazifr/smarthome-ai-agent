"""
Sistem Karşılaştırması: Statik vs Random Forest vs LightGBM

Çalıştırma:
    python compare.py

Çıktı:
    comparison_results.txt
    comparison_chart.png
"""

import os
import collections
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from imblearn.over_sampling import SMOTE

CSV_PATH     = "HomeC.csv"
MODEL_PATH   = "models/decision_model.pkl"    # LightGBM modeli
ENCODER_PATH = "models/label_encoder.pkl"
OUTPUT_TXT   = "comparison_results.txt"
OUTPUT_IMG   = "comparison_chart.png"

# ── 1. Veriyi Hazırla ─────────────────────────────────────────────────
print("Veri yukleniyor...")
df = pd.read_csv(CSV_PATH, low_memory=False)
# df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
df["time"] = pd.to_datetime(df["time"].astype(float), unit="s", errors="coerce")

df = df.dropna(subset=["time"])
df["hour"]        = df["time"].dt.hour
df["minute"]      = df["time"].dt.minute
df["day_of_week"] = df["time"].dt.dayofweek
df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)
df["day_type"]    = df["is_weekend"]
df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
df["humidity"]    = pd.to_numeric(df["humidity"], errors="coerce")
df["use_kw"]      = pd.to_numeric(df["use [kW]"], errors="coerce")
df["solar_kw"]    = pd.to_numeric(df["Solar [kW]"], errors="coerce").fillna(0)
df["light"]       = df["solar_kw"] * 500
df["motion"]      = (df["use_kw"] > 1.0).astype(int)

# Yeni feature'lar
df = df.sort_values("time")
df["temp_hour_interaction"] = df["temperature"] * df["hour"] / 24.0
df["use_kw_rolling"]        = df["use_kw"].rolling(window=120, min_periods=1).mean()
df["time_of_day"]           = pd.cut(df["hour"], bins=[-1,5,11,17,23], labels=[0,1,2,3]).astype(int)

df["weather"]      = np.where(df["solar_kw"] > 1.0, 0, np.where(df["solar_kw"] > 0.1, 1, 2))
df["sentiment"]    = 0
df["energy_price"] = np.where((df["hour"] >= 23) | (df["hour"] < 6), 0,
                    np.where((df["hour"] >= 17) & (df["hour"] < 23), 2, 1))

features_15 = [
    "hour", "minute", "day_of_week", "is_weekend", "day_type",
    "temperature", "humidity", "motion", "light",
    "weather", "sentiment", "energy_price",
    "temp_hour_interaction", "use_kw_rolling", "time_of_day"
]

features_12 = [
    "hour", "minute", "day_of_week", "is_weekend", "day_type",
    "temperature", "humidity", "motion", "light",
    "weather", "sentiment", "energy_price"
]

df = df[features_15 + ["use_kw"]].dropna()
print(f"   Temiz satir: {len(df):,}")

# ── 2. Etiketleri Oluştur ─────────────────────────────────────────────
low  = df["use_kw"].quantile(0.33)
high = df["use_kw"].quantile(0.66)

def assign_label(row):
    hour       = row["hour"]
    motion     = row["motion"]
    use        = row["use_kw"]
    is_weekend = row["is_weekend"]
    if (0 <= hour < 6) and use < low:        return "uyku_modu"
    if (22 <= hour < 24) and motion == 1:    return "uyku_hazirlik"
    if (6 <= hour < 9) and motion == 1:      return "sabah_rutini"
    if (9 <= hour < 17) and motion == 1 and is_weekend == 0: return "is_modu"
    if is_weekend == 1 and (10 <= hour < 22) and use >= high: return "misafir_modu"
    if (17 <= hour < 22) and motion == 1:    return "dinlenme_modu"
    if motion == 0 and use < low:            return "ev_bos"
    return "dinlenme_modu"

df["label"] = df.apply(assign_label, axis=1)

# Test seti — SMOTE uygulamadan önce gerçek dağılımdan al
df_test = df.sample(n=min(5000, len(df)), random_state=99).reset_index(drop=True)
print(f"   Test satiri: {len(df_test):,}")

# ── 3. STATİK SİSTEM ─────────────────────────────────────────────────
print("\nStatik sistem calistiriliyor...")

def static_decision(row):
    hour = row["hour"]
    temp = row["temperature"]
    if 0 <= hour < 6:      return "uyku_modu"
    if 6 <= hour < 9:      return "sabah_rutini"
    if 9 <= hour < 17:     return "is_modu" if row["is_weekend"] == 0 else "dinlenme_modu"
    if 17 <= hour < 22:    return "dinlenme_modu"
    if 22 <= hour < 24:    return "uyku_hazirlik"
    return "dinlenme_modu"

df_test["static_pred"] = df_test.apply(static_decision, axis=1)
static_acc = accuracy_score(df_test["label"], df_test["static_pred"])

# ── 4. RANDOM FOREST ─────────────────────────────────────────────────
print("Random Forest egitiliyor...")
le_rf = LabelEncoder()
y_all = le_rf.fit_transform(df["label"].values)
X_all_12 = df[features_12].values

smote = SMOTE(random_state=42)
X_bal, y_bal = smote.fit_resample(X_all_12, y_all)
X_tr, X_te, y_tr, y_te = train_test_split(X_bal, y_bal, test_size=0.2, random_state=42, stratify=y_bal)

rf = RandomForestClassifier(n_estimators=100, max_depth=10, min_samples_leaf=15, random_state=42, n_jobs=-1)
rf.fit(X_tr, y_tr)

X_test_12 = df_test[features_12].values
rf_preds  = le_rf.inverse_transform(rf.predict(X_test_12))
rf_acc    = accuracy_score(df_test["label"], rf_preds)

# ── 5. LightGBM (Mevcut Model) ────────────────────────────────────────
print("LightGBM modeli yukleniyor...")
lgbm_model = joblib.load(MODEL_PATH)
lgbm_le    = joblib.load(ENCODER_PATH)

X_test_15  = df_test[features_15].values
lgbm_preds = lgbm_le.inverse_transform(lgbm_model.predict(X_test_15))
lgbm_acc   = accuracy_score(df_test["label"], lgbm_preds)

# ── 6. ENERJİ İSRAFI ─────────────────────────────────────────────────
def energy_waste(pred, row):
    if pred in ["is_modu", "sabah_rutini"] and row["motion"] == 0:
        return row["use_kw"] * 0.3
    elif pred == "dinlenme_modu" and row["motion"] == 0:
        return row["use_kw"] * 0.2
    elif pred != "ev_bos" and row["motion"] == 0 and row["use_kw"] < low:
        return row["use_kw"] * 0.15
    return 0.0

df_test["static_waste"] = df_test.apply(lambda r: energy_waste(r["static_pred"], r), axis=1)
df_test["rf_waste"]     = df_test.apply(lambda r: energy_waste(rf_preds[r.name % len(rf_preds)], r), axis=1)
df_test["lgbm_waste"]   = df_test.apply(lambda r: energy_waste(lgbm_preds[r.name % len(lgbm_preds)], r), axis=1)

static_waste = df_test["static_waste"].sum()
rf_waste     = df_test["rf_waste"].sum()
lgbm_waste   = df_test["lgbm_waste"].sum()

# ── 7. SONUÇLAR ───────────────────────────────────────────────────────
results = f"""
╔══════════════════════════════════════════════════════════════════╗
║      STATİK vs RANDOM FOREST vs LightGBM KARŞILAŞTIRMASI        ║
╠══════════════════════════════════════════════════════════════════╣
║  Test Ornegi Sayisi: {len(df_test):>6,}                               ║
╠══════════════════════════════════════════════════════════════════╣
║                    STATİK    Random Forest    LightGBM          ║
║  Dogruluk        : {static_acc:>5.1%}        {rf_acc:>5.1%}          {lgbm_acc:>5.1%}     ║
║  Enerji Israfi   : {static_waste:>5.1f}        {rf_waste:>5.1f}          {lgbm_waste:>5.1f}     ║
╠══════════════════════════════════════════════════════════════════╣
║  LightGBM Avantaji:                                              ║
║  → Statik'e gore dogruluk artisi  : +{lgbm_acc - static_acc:.1%}                  ║
║  → RF'e gore dogruluk artisi      : +{lgbm_acc - rf_acc:.1%}                  ║
║  → Statik'e gore enerji tasarrufu : %{((static_waste-lgbm_waste)/static_waste*100) if static_waste>0 else 0:.1f}                ║
╚══════════════════════════════════════════════════════════════════╝
"""

print(results)
with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write(results)

# ── 8. GRAFİK ─────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Statik vs Random Forest vs LightGBM", fontsize=14, fontweight="bold")

labels  = ["Statik", "Random Forest", "LightGBM"]
colors  = ["#e74c3c", "#f39c12", "#2ecc71"]
acc_vals = [static_acc*100, rf_acc*100, lgbm_acc*100]
waste_vals = [static_waste, rf_waste, lgbm_waste]

bars1 = axes[0].bar(labels, acc_vals, color=colors, width=0.5)
axes[0].set_title("Karar Dogrulugu (%)")
axes[0].set_ylabel("Dogruluk (%)")
axes[0].set_ylim(0, 100)
for bar in bars1:
    h = bar.get_height()
    axes[0].text(bar.get_x() + bar.get_width()/2, h+1, f"{h:.1f}%", ha="center", fontweight="bold")

bars2 = axes[1].bar(labels, waste_vals, color=colors, width=0.5)
axes[1].set_title("Gereksiz Enerji Tuketimi (kWh)")
axes[1].set_ylabel("Enerji (kWh)")
for bar in bars2:
    h = bar.get_height()
    axes[1].text(bar.get_x() + bar.get_width()/2, h+0.3, f"{h:.1f}", ha="center", fontweight="bold")

plt.tight_layout()
plt.savefig(OUTPUT_IMG, dpi=150, bbox_inches="tight")
print(f"Grafik kaydedildi: {OUTPUT_IMG}")
print("Karsilastirma tamamlandi!")
