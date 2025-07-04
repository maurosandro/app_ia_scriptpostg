import requests
import json
from functools import lru_cache
from config import LLM_API_URL, LLM_MODEL, MAX_SQL_RESPONSE_LENGTH_CHARS, RECORD_LIMIT_FOR_LARGE_TABLES, TABLE_SIZE_LIMIT_GB
from utils import log_event, truncate_string_by_chars, get_approx_token_count

@lru_cache(maxsize=100)
def gerar_sql_cached(prompt: str, schema_info: str, table_sizes_info: str) -> str:
    """
    Função de cache para gerar SQL.
    """
    return gerar_sql(prompt, schema_info, table_sizes_info)

def gerar_sql(prompt: str, schema_info: str, table_sizes_info: str) -> str | None:
    """
    Gera uma instrução SQL a partir de um prompt em linguagem natural,
    considerando o esquema do banco de dados e o tamanho das tabelas.
    Utiliza a API local do Ollama ou LM Studio.

    Args:
        prompt (str): A instrução em linguagem natural.
        schema_info (str): Informações do esquema do banco de dados (tabelas e colunas).
        table_sizes_info (str): Informações sobre o tamanho e contagem de linhas das tabelas.

    Returns:
        str | None: A instrução SQL gerada ou None em caso de erro.
    """
    full_prompt = f"""
    Você é um DBA experiente e um especialista em SQL. Sua tarefa é converter a solicitação do usuário em uma instrução SQL otimizada e segura, com comentários claros.

    **Contexto do Banco de Dados:**
    {schema_info}

    **Informações de Volume de Dados das Tabelas:**
    {table_sizes_info}

    **Regras para Geração de SQL:**
    1.  Sempre adicione comentários explicativos nas linhas do SQL.
    2.  Para consultas SELECT, se a tabela principal envolvida tiver um volume de dados superior a {TABLE_SIZE_LIMIT_GB} GB (conforme 'Informações de Volume de Dados das Tabelas'), adicione uma cláusula LIMIT {RECORD_LIMIT_FOR_LARGE_TABLES} (ou TOP {RECORD_LIMIT_FOR_LARGE_TABLES} para SQL Server) para evitar sobrecarga no banco.
    3.  Garanta que todos os comandos DML (UPDATE, DELETE) e DDL (DROP) contenham uma cláusula WHERE explícita. Se a solicitação do usuário implicar em um comando DML/DDL sem WHERE, você DEVE adicionar um comentário alertando sobre o perigo e, se possível, sugerir uma condição WHERE.
    4.  Evite comandos como TRUNCATE, DROP DATABASE, GRANT, REVOKE. Se a solicitação do usuário sugerir algo similar, retorne um erro ou um SQL seguro com um comentário de aviso.
    5.  Formate o SQL de maneira legível, como um DBA faria.

    **Solicitação do Usuário:**
    {prompt}

    **Instrução SQL Gerada (comentada e otimizada):**
    ```sql
    """

    log_event(f"Enviando prompt ao LLM (aproximadamente {get_approx_token_count(full_prompt)} tokens).")

    # A API do LM Studio para completions (v1) usa 'prompt' e 'max_tokens'
    # A API do Ollama para generate usa 'prompt' e 'options': {'num_predict'}
    # Vamos usar uma estrutura que tenta ser compatível ou pode ser adaptada.
    # Para LM Studio, a URL é tipicamente http://localhost:1234/v1/completions
    # Para Ollama, a URL é http://localhost:11434/api/generate

    payload = {
        "model": LLM_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "max_tokens": get_approx_token_count(MAX_SQL_RESPONSE_LENGTH_CHARS) # Limita a resposta do LLM
    }

    # Se for API do Ollama, o parâmetro para max_tokens é diferente
    if "ollama" in LLM_API_URL.lower():
        payload = {
            "model": LLM_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_predict": get_approx_token_count(MAX_SQL_RESPONSE_LENGTH_CHARS)
            }
        }
    elif "v1/completions" in LLM_API_URL.lower(): # LM Studio (OpenAI compatible API)
        payload = {
            "model": LLM_MODEL, # Pode ser ignorado pelo LM Studio se o modelo já estiver carregado
            "prompt": full_prompt,
            "max_tokens": get_approx_token_count(MAX_SQL_RESPONSE_LENGTH_CHARS)
        }

    try:
        response = requests.post(LLM_API_URL, json=payload, timeout=120) # Aumentar timeout para LLM local
        response.raise_for_status() # Lança exceção para códigos de status HTTP de erro (4xx ou 5xx)

        result = response.json()
        log_event(f"Resposta bruta do LLM: {json.dumps(result)}")

        # Lógica para extrair a resposta dependendo da API (Ollama vs. LM Studio v1 completions)
        sql = ""
        if "ollama" in LLM_API_URL.lower():
            sql = result.get("response", "").strip()
        elif "v1/completions" in LLM_API_URL.lower():
            # LM Studio v1 completions API response structure
            if result and "choices" in result and len(result["choices"]) > 0:
                sql = result["choices"][0].get("text", "").strip()
        else:
            # Fallback para outras estruturas, ou se a URL não indicar claramente
            sql = result.get("response", "").strip()

        # Tenta extrair o bloco de código SQL se o LLM o envolveu em ```sql ... ```
        sql_match = re.search(r"```sql\s*(.*?)\s*```", sql, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            # Se não encontrou o bloco, assume que a resposta é o SQL direto
            log_event("Bloco ```sql``` não encontrado na resposta do LLM. Usando a resposta bruta.")

        # Trunca a resposta SQL para o limite de caracteres configurado
        sql = truncate_string_by_chars(sql, MAX_SQL_RESPONSE_LENGTH_CHARS)

        log_event(f"SQL gerado (truncado): {sql}")
        return sql
    except requests.exceptions.RequestException as e:
        log_event(f"Erro de conexão ou HTTP ao gerar SQL: {e}")
        return f"Erro ao conectar ao serviço LLM local. Verifique se o LM Studio/Ollama está em execução e o modelo carregado. Detalhes: {e}"
    except json.JSONDecodeError as e:
        log_event(f"Erro ao decodificar JSON da resposta do LLM: {e}. Resposta: {response.text}")
        return f"Erro ao processar a resposta do LLM. Detalhes: {e}"
    except Exception as e:
        log_event(f"Erro inesperado ao gerar SQL: {e}")
        return f"Ocorreu um erro inesperado ao gerar o SQL. Detalhes: {e}"

