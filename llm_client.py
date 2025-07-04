import requests
from config import LLM_API_URL, LLM_MODEL
from utils import log_event
from functools import lru_cache

@lru_cache(maxsize=100)
def gerar_sql_cached(prompt: str) -> str:
    return gerar_sql(prompt)  # gerar_sql deve estar definida acima



def gerar_sql(prompt):
    payload = {
        "model": LLM_MODEL,
        "prompt": f"Converta esta solicitação em SQL PostgreSQL seguro: {prompt}",
        "stream": False
    }
    try:
        response = requests.post(LLM_API_URL, json=payload)
        response.raise_for_status()
        result = response.json()
        sql = result.get("response", "").strip()
        log_event(f"SQL gerado: {sql}")
        return sql
    except Exception as e:
        log_event(f"Erro ao gerar SQL: {e}")
        return None
