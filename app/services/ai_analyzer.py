import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def analyze_job(description: str, query: str) -> dict:
    if not GEMINI_API_KEY:
        return {"score": 0, "reason": "API Key not configured"}

    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
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
        
        response = model.generate_content(prompt)
        text_resp = response.text
        
        # Cleanup markdown
        text_resp = text_resp.replace("```json", "").replace("```", "").strip()
        
        return json.loads(text_resp)
    
    except Exception as e:
        print(f"AI Lib Error: {e}")
        return {"score": 0, "reason": "AI Error"}
