import os
import logging
from config import LOG_PATH

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def log_event(message):
    logging.info(message)

def validar_prompt(prompt: str) -> tuple[bool, str]:
    if not prompt or len(prompt.strip()) < 10:
        return False, "Entrada muito curta. Forneça uma instrução mais detalhada."
    palavras_proibidas = ["truncate", "drop database", "grant", "revoke"]
    for palavra in palavras_proibidas:
        if palavra in prompt.lower():
            return False, f"Instrução contém comando proibido: {palavra}"
    return True, ""