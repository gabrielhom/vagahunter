import google.genai as genai
import os
from dotenv import load_dotenv
from app.config import settings

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
if not api_key:
    raise SystemExit("GEMINI_API_KEY não configurada no .env")

client = genai.Client(api_key=api_key)

print("Available Models:")
for m in client.models.list():
    name = getattr(m, "name", str(m))
    print(f"- {name}")
