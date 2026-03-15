"""
Gemini LLM Test Scripti
Çalıştırma: python test_gemini.py
"""

import os
import json
from google import genai

GEMINI_API_KEY = input("Gemini API key'ini gir: ").strip()

client = genai.Client(api_key=GEMINI_API_KEY)

prompt = """Sen bir akıllı ev yönetim sistemisin. Aşağıdaki bağlam bilgilerine göre en uygun cihaz kararını ver.

MEVCUT DURUM:
- Oda: living_room
- Saat: 19:00
- Sıcaklık: 28°C
- Nem: 70%
- Ev durumu: dolu
- Hava durumu: yağmurlu
- Kullanıcı duygu durumu: yorgun
- Gün tipi: hafta içi
- Enerji modu: normal

Yanıtını SADECE aşağıdaki JSON formatında ver, başka hiçbir şey yazma:
[
  {"device": "ac", "command": "COOL_LOW", "reason": "kısa gerekçe"},
  {"device": "lights", "command": "DIM", "reason": "kısa gerekçe"}
]

Geçerli cihazlar: ac, lights, fan, heater
Geçerli komutlar: ON, OFF, COOL_LOW, COOL_HIGH, HEAT, DIM"""

print("\n🤖 Gemini'ye istek gönderiliyor...\n")

try:
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt
    )
    text = response.text.strip()
    print("📥 Ham cevap:")
    print(text)

    # JSON parse et
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    print("\n✅ JSON parse başarılı!")
    print("\n🏠 Kararlar:")
    for item in data:
        print(f"  {item['device']} → {item['command']} | {item['reason']}")

except Exception as e:
    print(f"\n❌ Hata: {e}")
