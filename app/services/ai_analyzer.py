import os
import json
import google.genai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator
from ..config import settings
import logging

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or settings.gemini_api_key
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

class AnalysisResult(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    reason: str = Field(default="N/A", max_length=400)

    @field_validator("score", mode="before")
    def _coerce_score(cls, v):
        try:
            num = int(float(v))
        except (TypeError, ValueError):
            return 0
        return max(0, min(100, num))

    @field_validator("reason", mode="before")
    def _sanitize_reason(cls, v):
        return (str(v or "N/A")).strip()[:400]

def _parse_ai_json(raw_text: str) -> AnalysisResult:
    cleaned = (raw_text or "").replace("```json", "").replace("```", "").strip()
    data = json.loads(cleaned)
    return AnalysisResult.model_validate(data)

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
            model=settings.gemini_model,
            contents=prompt,
        )
        text_resp = getattr(response, "text", "") or ""
        parsed = _parse_ai_json(text_resp)
        return parsed.model_dump()
    except (ValidationError, json.JSONDecodeError) as e:
        logger.error("AI Parse Error: %s", e)
        return {"score": 0, "reason": "AI returned invalid JSON"}
    except Exception as e:
        logger.error("AI Lib Error: %s", e)
        return {"score": 0, "reason": "AI Error"}
