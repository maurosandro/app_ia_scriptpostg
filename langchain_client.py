from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from config import LLM_MODEL, LLM_API_URL, MAX_SQL_RESPONSE_LENGTH_CHARS, RECORD_LIMIT_FOR_LARGE_TABLES, TABLE_SIZE_LIMIT_GB
from utils import log_event, truncate_string_by_chars, get_approx_token_count
import re


def gerar_sql_com_langchain(prompt: str, schema_info: str, table_sizes_info: str) -> str | None:
    """
    Gera uma instrução SQL a partir de um prompt em linguagem natural usando LangChain
    e um modelo Ollama local, considerando o esquema do banco de dados e o tamanho das tabelas.

    Args:
        prompt (str): A instrução em linguagem natural.
        schema_info (str): Informações do esquema do banco de dados (tabelas e colunas).
        table_sizes_info (str): Informações sobre o tamanho e contagem de linhas das tabelas.

    Returns:
        str | None: A instrução SQL gerada ou None em caso de erro.
    """
    try:
        # Conecte ao modelo local via Ollama
        # A base_url para ChatOllama deve ser apenas o host:port do Ollama
        # Se LLM_API_URL for "http://localhost:11434/api/generate", a base_url é "http://localhost:11434"
        ollama_base_url = LLM_API_URL.replace(
            "/api/generate", "").replace("/v1/completions", "")
        # Temperatura baixa para respostas mais determinísticas
        llm = ChatOllama(
            model=LLM_MODEL, base_url=ollama_base_url, temperature=0.1)

        # Prompt template para o LLM
        template = ChatPromptTemplate.from_messages(
            [
                ("system",
                 f"""
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
                 """),
                ("human",
                 f"""
                 **Solicitação do Usuário:**
                 {prompt}

                 **Instrução SQL Gerada (comentada e otimizada):**
                 ```sql
                 """)
            ]
        )

        log_event(
            f"Enviando prompt ao LLM via LangChain (aproximadamente {get_approx_token_count(prompt)} tokens).")

        # Invoca o modelo
        response = llm.invoke(template.format_messages())

        sql = response.content.strip()

        # Tenta extrair o bloco de código SQL se o LLM o envolveu em ```sql ... ```
        sql_match = re.search(r"```sql\s*(.*?)\s*```",
                              sql, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
        else:
            # Se não encontrou o bloco, assume que a resposta é o SQL direto
            log_event(
                "Bloco ```sql``` não encontrado na resposta do LLM via LangChain. Usando a resposta bruta.")

        # Trunca a resposta SQL para o limite de caracteres configurado
        sql = truncate_string_by_chars(sql, MAX_SQL_RESPONSE_LENGTH_CHARS)

        log_event(f"SQL gerado via LangChain (truncado): {sql}")
        return sql
    except Exception as e:
        log_event(f"Erro ao gerar SQL com LangChain: {e}")
        return f"Erro ao gerar SQL com LangChain. Verifique se o Ollama está em execução e o modelo '{LLM_MODEL}' carregado. Detalhes: {e}"
