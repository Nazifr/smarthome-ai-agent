"""
Statik vs Adaptif Sistem Karşılaştırması

Aynı HomeC.csv verisi üzerinde:
1. Statik sistem (sabit if-then kuralları)
2. Adaptif sistem (ML modeli)

...çalıştırıp sonuçları karşılaştırır.

Çalıştırma:
    python compare.py

Çıktı:
    comparison_results.txt
    comparison_chart.png
"""

import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.metrics import accuracy_score

CSV_PATH     = "HomeC.csv"
MODEL_PATH   = "models/decision_model.pkl"
ENCODER_PATH = "models/label_encoder.pkl"
OUTPUT_TXT   = "comparison_results.txt"
OUTPUT_IMG   = "comparison_chart.png"

# ── 1. Veriyi Yükle ───────────────────────────────────────────────────
print("📂 Veri yükleniyor...")
df = pd.read_csv(CSV_PATH)
df["time"] = pd.to_datetime(df["time"], infer_datetime_format=True, errors="coerce")
df = df.dropna(subset=["time"])
df["hour"]        = df["time"].dt.hour
df["minute"]      = df["time"].dt.minute
df["day_of_week"] = df["time"].dt.dayofweek
df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)
df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")
df["humidity"]    = pd.to_numeric(df["humidity"], errors="coerce")
df["use_kw"]      = pd.to_numeric(df["use [kW]"], errors="coerce")
df["solar_kw"]    = pd.to_numeric(df["Solar [kW]"], errors="coerce").fillna(0)
df["light"]       = df["solar_kw"] * 1000
df["motion"]      = (df["use_kw"] > 1.0).astype(int)

features = ["hour", "minute", "day_of_week", "is_weekend",
            "temperature", "humidity", "motion", "light"]

df = df[features + ["use_kw"]].dropna()

# Test için 2000 satır al (hızlı çalışsın)
df_test = df.sample(n=min(2000, len(df)), random_state=42).reset_index(drop=True)
print(f"   Test satırı: {len(df_test):,}")

# ── 2. Gerçek Etiketleri Üret ─────────────────────────────────────────
low  = df["use_kw"].quantile(0.33)
high = df["use_kw"].quantile(0.66)

def ground_truth(row):
    hour   = row["hour"]
    motion = row["motion"]
    temp   = row["temperature"]
    use    = row["use_kw"]
    if use >= high and temp > 24:
        return "ac_COOL_HIGH"
    elif use >= high and temp < 18:
        return "heater_ON"
    elif (0 <= hour < 7) and motion == 0 and use < low:
        return "ac_OFF"
    elif 7 <= hour < 9 and motion == 1:
        return "lights_ON"
    elif 9 <= hour < 17 and motion == 0:
        return "ac_OFF"
    elif 17 <= hour < 23 and motion == 1:
        return "ac_COOL_LOW" if temp > 22 else "lights_DIM"
    elif hour >= 23:
        return "lights_OFF"
    else:
        return "lights_ON"

df_test["ground_truth"] = df_test.apply(ground_truth, axis=1)

# ── 3. STATİK SİSTEM ─────────────────────────────────────────────────
print("\n⚙️  Statik sistem çalıştırılıyor...")

def static_decision(row):
    """
    Sabit if-then kuralları — kullanıcı tarafından önceden tanımlanmış.
    Sadece sıcaklık ve saate bakıyor, enerji tüketimini görmüyor.
    """
    hour = row["hour"]
    temp = row["temperature"]

    if temp > 28:
        return "ac_COOL_HIGH"
    elif temp < 16:
        return "heater_ON"
    elif 23 <= hour or hour < 7:
        return "lights_OFF"
    elif 7 <= hour < 9:
        return "lights_ON"
    elif 9 <= hour < 17:
        return "ac_OFF"
    elif 17 <= hour < 23:
        return "ac_COOL_LOW"
    else:
        return "lights_ON"

df_test["static_pred"] = df_test.apply(static_decision, axis=1)

# ── 4. ADAPTİF SİSTEM (ML) ────────────────────────────────────────────
print("🤖 Adaptif sistem (ML modeli) çalıştırılıyor...")
model = joblib.load(MODEL_PATH)
le    = joblib.load(ENCODER_PATH)

X = df_test[features].values
y_pred_encoded = model.predict(X)
df_test["adaptive_pred"] = le.inverse_transform(y_pred_encoded)

# ── 5. DOĞRULUK KARŞILAŞTIRMASI ───────────────────────────────────────
print("\n📊 Sonuçlar hesaplanıyor...")

static_acc   = accuracy_score(df_test["ground_truth"], df_test["static_pred"])
adaptive_acc = accuracy_score(df_test["ground_truth"], df_test["adaptive_pred"])

# ── 6. ENERJİ VERİMLİLİĞİ KARŞILAŞTIRMASI ────────────────────────────
# AC kararı gereksiz verildiğinde enerji israfı sayılır
def energy_waste(pred, row):
    """
    Gereksiz AC veya ısıtıcı açılması enerji israfı.
    Ev boşken cihaz açılması = israf.
    """
    if pred in ["ac_COOL_HIGH", "ac_COOL_LOW"] and row["motion"] == 0:
        return row["use_kw"] * 0.3   # %30 israf tahmini
    elif pred == "heater_ON" and row["motion"] == 0:
        return row["use_kw"] * 0.25
    elif pred == "lights_ON" and row["hour"] >= 9 and row["motion"] == 0:
        return row["use_kw"] * 0.1
    return 0.0

df_test["static_waste"]   = df_test.apply(lambda r: energy_waste(r["static_pred"], r), axis=1)
df_test["adaptive_waste"] = df_test.apply(lambda r: energy_waste(r["adaptive_pred"], r), axis=1)

static_total_waste   = df_test["static_waste"].sum()
adaptive_total_waste = df_test["adaptive_waste"].sum()
energy_saving_pct    = ((static_total_waste - adaptive_total_waste) / static_total_waste * 100) if static_total_waste > 0 else 0

# ── 7. YANLIŞ KARAR SAYISI ────────────────────────────────────────────
static_wrong   = (df_test["static_pred"]   != df_test["ground_truth"]).sum()
adaptive_wrong = (df_test["adaptive_pred"] != df_test["ground_truth"]).sum()

# ── 8. SONUÇLARI YAZDIR ───────────────────────────────────────────────
results = f"""
╔══════════════════════════════════════════════════════════════╗
║         STATİK vs ADAPTİF SİSTEM KARŞILAŞTIRMASI            ║
╠══════════════════════════════════════════════════════════════╣
║  Test Örneği Sayısı    : {len(df_test):>6,}                        ║
╠══════════════════════════════════════════════════════════════╣
║                         STATİK      ADAPTİF                 ║
║  Karar Doğruluğu      : {static_acc:>6.1%}      {adaptive_acc:>6.1%}               ║
║  Yanlış Karar Sayısı  : {static_wrong:>6,}      {adaptive_wrong:>6,}               ║
║  Enerji İsrafı (kWh)  : {static_total_waste:>6.1f}      {adaptive_total_waste:>6.1f}               ║
╠══════════════════════════════════════════════════════════════╣
║  Adaptif Sistem Avantajı:                                    ║
║  → Doğruluk artışı    : +{adaptive_acc - static_acc:.1%}                        ║
║  → Enerji tasarrufu   : %{energy_saving_pct:.1f}                           ║
╚══════════════════════════════════════════════════════════════╝
"""

print(results)

with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
    f.write(results)
print(f"✅ Sonuçlar kaydedildi: {OUTPUT_TXT}")

# ── 9. GRAFİK ─────────────────────────────────────────────────────────
print("\n📈 Grafik oluşturuluyor...")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle("Statik vs Adaptif Sistem Karşılaştırması", fontsize=14, fontweight="bold")

# Grafik 1: Doğruluk
bars1 = axes[0].bar(["Statik Sistem", "Adaptif Sistem (ML)"],
                     [static_acc * 100, adaptive_acc * 100],
                     color=["#e74c3c", "#2ecc71"], width=0.5)
axes[0].set_title("Karar Doğruluğu (%)")
axes[0].set_ylabel("Doğruluk (%)")
axes[0].set_ylim(0, 100)
for bar in bars1:
    h = bar.get_height()
    axes[0].text(bar.get_x() + bar.get_width()/2, h + 1,
                 f"{h:.1f}%", ha="center", fontsize=12, fontweight="bold")

# Grafik 2: Enerji İsrafı
bars2 = axes[1].bar(["Statik Sistem", "Adaptif Sistem (ML)"],
                     [static_total_waste, adaptive_total_waste],
                     color=["#e74c3c", "#2ecc71"], width=0.5)
axes[1].set_title("Gereksiz Enerji Tüketimi (kWh)")
axes[1].set_ylabel("Enerji (kWh)")
for bar in bars2:
    h = bar.get_height()
    axes[1].text(bar.get_x() + bar.get_width()/2, h + 0.5,
                 f"{h:.1f}", ha="center", fontsize=12, fontweight="bold")

plt.tight_layout()
plt.savefig(OUTPUT_IMG, dpi=150, bbox_inches="tight")
print(f"✅ Grafik kaydedildi: {OUTPUT_IMG}")
print("\n🎉 Karşılaştırma tamamlandı!")
