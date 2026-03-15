from google import genai

GEMINI_API_KEY = input("Gemini API key'ini gir: ").strip()
client = genai.Client(api_key=GEMINI_API_KEY)

print("\nMevcut modeller:")
for model in client.models.list():
    print(f"  {model.name}")
