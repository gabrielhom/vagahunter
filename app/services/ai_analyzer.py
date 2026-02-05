import os
import json
import google.genai as genai
from dotenv import load_dotenv
from ..config import settings

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def analyze_job(description: str, query: str) -> dict:
    if not client:
        return {"score": 0, "reason": "API Key not configured"}

    try:
        prompt = f"""
        Analise a vaga abaixo para um perfil: "Desenvolvedor/Profissional focado em {query} (Júnior/Pleno)".
        
        Critérios:
        - Tecnologia principal deve ser {query}.
        - Se for vaga Sênior/Especialista: nota baixa (sou Júnior/Pleno).
        - Se for presencial (e não remoto): nota baixa.
        
        Responda APENAS um JSON: {{"score": 0-100, "reason": "motivo curto"}}
        
        Vaga:
        {description[:4000]}
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text_resp = (getattr(response, "text", "") or "").replace("```json", "").replace("```", "").strip()

        return json.loads(text_resp)

    except Exception as e:
        print(f"AI Lib Error: {e}")
        return {"score": 0, "reason": "AI Error"}
