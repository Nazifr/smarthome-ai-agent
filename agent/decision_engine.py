"""
DecisionEngine — Hibrit Karar Motoru

Basit/rutin kararlar → Random Forest (hızlı, deterministik)
Karmaşık/çok faktörlü kararlar → Gemini LLM (esnek, açıklanabilir)
Feedback öğrenme → Kullanıcı override'larından öğren
"""

import os
import json
import joblib
import numpy as np
try:
    from spotify_controller import SpotifyController
    _spotify = SpotifyController()
except Exception:
    _spotify = None

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("[DecisionEngine] ⚠️ google-generativeai yüklü değil, sadece ML kullanılacak")

GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY", "")
MODEL_PATH           = os.path.join(os.path.dirname(__file__), "models", "decision_model.pkl")
ENCODER_PATH         = os.path.join(os.path.dirname(__file__), "models", "label_encoder.pkl")
MAPPING_PATH         = os.path.join(os.path.dirname(__file__), "models", "label_mapping.json")
MIN_SAMPLES_FOR_ML   = int(os.getenv("MIN_SAMPLES_FOR_ML", "0"))
CONFIDENCE_THRESHOLD = 0.60
RETRAIN_THRESHOLD    = int(os.getenv("RETRAIN_THRESHOLD", "20"))  # kaç feedback'te yeniden eğit


class DecisionEngine:
    def __init__(self):
        self.model   = None
        self.encoder = None
        self.samples = []       # feedback örnekleri
        self.gemini  = None
        self._load_model()
        self._init_gemini()

    def _load_model(self):
        try:
            self.model   = joblib.load(MODEL_PATH)
            self.encoder = joblib.load(ENCODER_PATH)
            print("[DecisionEngine] ✓ Kayıtlı model yüklendi")
            print(f"[DecisionEngine] Model tipi: {type(self.model)}")
        except FileNotFoundError:
            print("[DecisionEngine] Model bulunamadı, heuristic modda başlıyor")

    def _init_gemini(self):
        if not GEMINI_AVAILABLE:
            return
        if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_KEY":
            print("[DecisionEngine] Gemini API key ayarlanmamış, LLM devre dışı")
            return
        try:
            self.gemini = genai.Client(api_key=GEMINI_API_KEY)
            print("[DecisionEngine] ✓ Gemini LLM bağlandı")
        except Exception as e:
            print(f"[DecisionEngine] Gemini bağlantı hatası: {e}")

    def decide(self, context: dict, features: list) -> list:
        if self.model and len(self.samples) >= MIN_SAMPLES_FOR_ML:
            ml_actions, confidence = self._ml_decide(context, features)
            if confidence >= CONFIDENCE_THRESHOLD:
                print(f"[DecisionEngine] ML kararı (güven: {confidence:.0%})")
                return ml_actions
            if self.gemini and self._is_complex(context):
                print(f"[DecisionEngine] Karmaşık bağlam, Gemini devreye giriyor...")
                llm_actions = self._llm_decide(context, confidence)
                if llm_actions:
                    return llm_actions
            return ml_actions
        if self.gemini:
            print("[DecisionEngine] ML yok, Gemini kullanılıyor...")
            llm_actions = self._llm_decide(context, confidence=None)
            if llm_actions:
                return llm_actions
        print("[DecisionEngine] Heuristic karar veriliyor...")
        return self._heuristic_decide(context)

    def _ml_decide(self, context: dict, features: list):
        try:
            X          = np.array(features).reshape(1, -1)
            proba      = self.model.predict_proba(X)[0]
            idx        = np.argmax(proba)
            confidence = proba[idx]
            label      = self.encoder.inverse_transform([idx])[0]
            actions    = self._label_to_actions(label, context, confidence, method="ml")
            return actions, confidence
        except Exception as e:
            print(f"[DecisionEngine] ML hatası: {e}")
            return self._heuristic_decide(context), 0.0

    def _llm_decide(self, context: dict, confidence) -> list:
        try:
            prompt   = self._build_prompt(context, confidence)
            response = self.gemini.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            data = json.loads(text)
            if isinstance(data, dict):
                data = [data]
            actions = []
            for item in data:
                actions.append({
                    "device":     item.get("device", "lights"),
                    "command":    item.get("command", "OFF"),
                    "reason":     item.get("reason", "LLM kararı"),
                    "confidence": None,
                    "method":     "llm"
                })
            return actions
        except Exception as e:
            print(f"[DecisionEngine] Gemini hatası: {e}")
            return []

    def _build_prompt(self, context: dict, confidence) -> str:
        hour          = context.get("hour", 12)
        temp          = context.get("temperature", 22)
        humidity      = context.get("humidity", 50)
        occupancy     = context.get("occupancy", "unknown")
        context_label = context.get("context_label", "genel")
        weather       = context.get("weather_str", "bilinmiyor")
        sentiment     = context.get("sentiment_str", "nötr")
        day_type      = context.get("day_type", 0)
        energy_mode   = context.get("energy_mode", "normal")
        room          = context.get("room", "living_room")
        conf_str      = f"{confidence:.0%}" if confidence else "belirsiz"
        day_str       = "hafta sonu" if day_type == 1 else "hafta içi"

        return f"""Sen bir akıllı ev yönetim sistemisin. Aşağıdaki bağlam bilgilerine göre en uygun cihaz kararını ver.

MEVCUT DURUM:
- Oda: {room}
- Saat: {hour:02d}:00
- Sıcaklık: {temp}°C
- Nem: {humidity}%
- Ev durumu: {occupancy}
- Bağlam: {context_label}
- Hava durumu: {weather}
- Kullanıcı duygu durumu: {sentiment}
- Gün tipi: {day_str}
- Enerji modu: {energy_mode}
- ML model güveni: {conf_str}

KURALLAR:
- Ev boşsa gereksiz cihazları kapat
- Kullanıcı yorgunsa ışıkları kıs, sıcaklığı rahat tut
- Yağmurlu havada iç ışıkları artır
- Enerji modu tasarrufsa AC kullanımını minimize et
- Gece 23:00-07:00 arası sessiz mod

Yanıtını SADECE aşağıdaki JSON formatında ver, başka hiçbir şey yazma:
[
  {{"device": "ac", "command": "COOL_LOW", "reason": "kısa gerekçe"}},
  {{"device": "lights", "command": "DIM", "reason": "kısa gerekçe"}}
]

Geçerli cihazlar: ac, lights, fan, heater
Geçerli komutlar: ON, OFF, COOL_LOW, COOL_HIGH, HEAT, DIM"""

    def _is_complex(self, context: dict) -> bool:
        if context.get("sentiment_str") in ["stresli", "yorgun"]:
            return True
        if context.get("weather_str") in ["yağmurlu", "fırtınalı", "karlı"]:
            return True
        hour = context.get("hour", 12)
        if context.get("day_type") == 1 and 9 <= hour <= 12:
            return True
        return False

    def _heuristic_decide(self, context: dict) -> list:
        hour      = context.get("hour", 12)
        temp      = context.get("temperature", 22)
        occupancy = context.get("occupancy", "unknown")
        actions   = []
        if occupancy == "bos_ev":
            actions.append({"device": "ac",     "command": "OFF",      "reason": "Ev boş — klima kapatılıyor",   "confidence": None, "method": "heuristic"})
            actions.append({"device": "lights",  "command": "OFF",      "reason": "Ev boş — ışıklar kapatılıyor", "confidence": None, "method": "heuristic"})
            actions.append({"device": "fan",     "command": "OFF",      "reason": "Ev boş — fan kapatılıyor",     "confidence": None, "method": "heuristic"})
        elif temp > 28:
            actions.append({"device": "ac",     "command": "COOL_HIGH", "reason": f"Sıcaklık yüksek ({temp}°C)", "confidence": None, "method": "heuristic"})
        elif temp > 24:
            actions.append({"device": "ac",     "command": "COOL_LOW",  "reason": f"Sıcaklık biraz yüksek ({temp}°C)", "confidence": None, "method": "heuristic"})
        elif temp < 16:
            actions.append({"device": "heater", "command": "ON",        "reason": f"Sıcaklık düşük ({temp}°C)",  "confidence": None, "method": "heuristic"})
        elif 23 <= hour or hour < 7:
            actions.append({"device": "lights", "command": "OFF",       "reason": "Gece modu",                   "confidence": None, "method": "heuristic"})
        else:
            actions.append({"device": "lights", "command": "ON",        "reason": "Normal mod",                  "confidence": None, "method": "heuristic"})
        return actions

    def _label_to_actions(self, label: str, context: dict, confidence: float, method: str) -> list:
        try:
            with open(MAPPING_PATH, "r", encoding="utf-8") as f:
                label_mapping = json.load(f)
            commands = label_mapping.get(label, {"lights": "ON"})
        except Exception:
            commands = {"lights": "ON"}

        actions = []
        for device, command in commands.items():
            if device == "music":
                if _spotify:
                    _spotify.play(command)
                else:
                     print(f"[DecisionEngine] Müzik modu: {command} (Spotify devre dışı)")
                continue
            actions.append({
                "device":     device,
                "command":    command,
                "reason":     f"ML kararı: {label}",
                "confidence": confidence,
                "method":     method,
                "scenario":   label,
            })
        return actions

    # ── Feedback Öğrenme ──────────────────────────────────────────────

    def record_feedback(self, features: list, device: str, command: str):
        """
        Kullanıcı manuel override yaptığında çağrılır.
        Cihaz + komut kombinasyonundan senaryo etiketi türetilir.
        """
        label = self._infer_label_from_feedback(device, command)
        if label:
            self.samples.append((features, label))
            print(f"[DecisionEngine] Feedback kaydedildi: {device}→{command} = {label} ({len(self.samples)}/{RETRAIN_THRESHOLD})")

            if len(self.samples) >= RETRAIN_THRESHOLD:
                self._retrain()

    def _infer_label_from_feedback(self, device: str, command: str) -> str:
        """
        Kullanıcının yaptığı override'dan senaryo etiketi çıkar.
        Örneğin: lights=DIM → dinlenme_modu, lights=OFF → uyku_modu
        """
        mapping = {
            ("lights", "OFF"):      "uyku_modu",
            ("lights", "DIM"):      "dinlenme_modu",
            ("lights", "ON"):       "sabah_rutini",
            ("ac", "OFF"):          "ev_bos",
            ("ac", "COOL_LOW"):     "dinlenme_modu",
            ("ac", "COOL_HIGH"):    "misafir_modu",
            ("fan", "ON"):          "dinlenme_modu",
            ("fan", "OFF"):         "uyku_modu",
            ("heater", "ON"):       "dinlenme_modu",
        }
        return mapping.get((device, command), None)

    def add_sample(self, features: list, label: str):
        """Direkt etiketle örnek ekle."""
        self.samples.append((features, label))
        if len(self.samples) >= RETRAIN_THRESHOLD:
            self._retrain()

    def _retrain(self):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import LabelEncoder

        print(f"[DecisionEngine] {len(self.samples)} feedback örneğiyle yeniden eğitiliyor...")

        # Mevcut model varsa onun verisiyle birleştir (weighted)
        X_new = np.array([s[0] for s in self.samples])
        y_labels = [s[1] for s in self.samples]

        le_new = LabelEncoder()
        y_new  = le_new.fit_transform(y_labels)

        new_model = RandomForestClassifier(n_estimators=50, random_state=42)
        new_model.fit(X_new, y_new)

        self.model   = new_model
        self.encoder = le_new
        self.samples = []

        # Güncellenmiş modeli kaydet
        try:
            joblib.dump(self.model,   MODEL_PATH)
            joblib.dump(self.encoder, ENCODER_PATH)
            print("[DecisionEngine] ✓ Model güncellendi ve kaydedildi")
        except Exception as e:
            print(f"[DecisionEngine] Model kaydetme hatası: {e}")
