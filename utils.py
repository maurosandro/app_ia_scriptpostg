import os
import logging
from config import LOG_PATH, MAX_PROMPT_LENGTH_CHARS

# Garante que o diretório de logs exista
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Configuração básica de logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding='utf-8' # Garante que caracteres especiais sejam logados corretamente
)

def log_event(message: str):
    """
    Registra uma mensagem no arquivo de log.
    """
    logging.info(message)

def validar_prompt(prompt: str) -> tuple[bool, str]:
    """
    Valida o prompt do usuário quanto ao tamanho e comandos proibidos.

    Args:
        prompt (str): A instrução em linguagem natural fornecida pelo usuário.

    Returns:
        tuple[bool, str]: Uma tupla onde o primeiro elemento indica se o prompt é válido (True/False)
                          e o segundo elemento é uma mensagem de feedback.
    """
    if not prompt or len(prompt.strip()) < 10:
        log_event("Validação de prompt falhou: Entrada muito curta.")
        return False, "Entrada muito curta. Por favor, forneça uma instrução mais detalhada (mínimo 10 caracteres)."

    if len(prompt) > MAX_PROMPT_LENGTH_CHARS:
        log_event(f"Validação de prompt falhou: Prompt excede o limite de caracteres ({MAX_PROMPT_LENGTH_CHARS}).")
        return False, f"Seu prompt é muito longo. Por favor, limite-o a {MAX_PROMPT_LENGTH_CHARS} caracteres."

    # Comandos SQL perigosos que não devem ser gerados diretamente pelo LLM
    # ou que exigem revisão rigorosa.
    # Adicione mais conforme necessário para a segurança do seu ambiente.
    palavras_proibidas = [
        "truncate", "drop database", "grant", "revoke", "alter table",
        "drop table", "delete from", "update", "insert into", "create table"
    ]
    # Verifica se o prompt contém palavras proibidas, ignorando o caso.
    # Para UPDATE/DELETE/DROP, a validação mais rigorosa é feita em models.py
    # após a geração do SQL. Aqui é uma validação inicial do prompt.
    for palavra in palavras_proibidas:
        if palavra in prompt.lower():
            log_event(f"Validação de prompt falhou: Contém comando proibido '{palavra}'.")
            return False, f"Sua instrução contém um comando potencialmente perigoso ou proibido: '{palavra}'. Por favor, reformule sua solicitação."

    log_event("Prompt validado com sucesso.")
    return True, "Prompt válido."

def truncate_string_by_chars(text: str, max_chars: int) -> str:
    """
    Trunca uma string para um número máximo de caracteres.

    Args:
        text (str): A string a ser truncada.
        max_chars (int): O número máximo de caracteres permitidos.

    Returns:
        str: A string truncada.
    """
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text

def get_approx_token_count(text: str) -> int:
    """
    Retorna uma contagem aproximada de tokens com base no número de caracteres.
    Esta é uma heurística simples e não uma contagem de tokens real de um tokenizer de LLM.
    Geralmente, 1 token ~ 4 caracteres.
    """
    return len(text) // 4
