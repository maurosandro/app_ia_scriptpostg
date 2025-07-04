import streamlit as st
import time
import pandas as pd
from datetime import datetime, timedelta

from config import (
    STREAMLIT_APP_NAME, DB_TYPE, TABLE_SIZE_LIMIT_GB,
    USE_LANGCHAIN, MAX_PROMPT_LENGTH_CHARS, RECORD_LIMIT_FOR_LARGE_TABLES
)
from db import conectar_banco, get_table_schema, get_table_size_and_row_count
from models import verifica_comando_perigoso
from utils import log_event, validar_prompt, truncate_string_by_chars

# Importa o cliente LLM apropriado
if USE_LANGCHAIN:
    from langchain_client import gerar_sql_com_langchain as gerar_sql_llm
else:
    # Note: This will be the direct requests client
    from llm_client import gerar_sql as gerar_sql_llm

st.set_page_config(page_title=STREAMLIT_APP_NAME, layout="wide")
st.title(STREAMLIT_APP_NAME)

log_event("Aplicação Streamlit iniciada.")

# Inicializa o estado da sessão
if "sql_gerado" not in st.session_state:
    st.session_state.sql_gerado = ""
if "last_interaction_time" not in st.session_state:
    st.session_state.last_interaction_time = datetime.now()
if "db_schema_info" not in st.session_state:
    st.session_state.db_schema_info = "Carregando esquema do banco de dados..."
if "db_table_sizes" not in st.session_state:
    st.session_state.db_table_sizes = {}
if "execution_log" not in st.session_state:
    st.session_state.execution_log = []

# --- Funções de UI e Lógica de Negócios ---


def display_table_info(table_sizes: dict):
    """Exibe informações sobre o tamanho das tabelas."""
    if not table_sizes:
        st.info(
            "Não foi possível obter informações de tamanho das tabelas ou o banco de dados está vazio.")
        return

    st.subheader("Informações de Volume de Dados das Tabelas")
    table_data = []
    for table, info in table_sizes.items():
        size_gb = info['size_bytes'] / (1024**3) if info['size_bytes'] else 0
        table_data.append({
            "Tabela": table,
            "Tamanho (GB)": f"{size_gb:.2f}",
            "Linhas": f"{info['row_count']:,}",
            "Status": "Grande" if size_gb > TABLE_SIZE_LIMIT_GB else "Normal"
        })
    df_table_info = pd.DataFrame(table_data)
    st.dataframe(df_table_info, use_container_width=True)
    st.info(
        f"Tabelas com mais de {TABLE_SIZE_LIMIT_GB} GB terão um LIMIT/TOP {RECORD_LIMIT_FOR_LARGE_TABLES} adicionado automaticamente em consultas SELECT.")


def update_db_info():
    """Conecta ao banco e atualiza o esquema e tamanhos das tabelas."""
    conn = conectar_banco()
    if conn:
        try:
            st.session_state.db_schema_info = get_table_schema(conn)
            st.session_state.db_table_sizes = get_table_size_and_row_count(
                conn)
            log_event(
                "Informações do banco de dados atualizadas no estado da sessão.")
        except Exception as e:
            st.error(f"Erro ao carregar informações do banco de dados: {e}")
            log_event(f"Erro ao carregar informações do banco de dados: {e}")
        finally:
            if conn:
                conn.close()
    else:
        st.error(
            "Não foi possível conectar ao banco de dados para obter informações. Verifique as configurações.")
        log_event("Falha na conexão ao banco de dados ao tentar obter informações.")


# --- Sidebar para Configurações e Logs ---
with st.sidebar:
    st.header("Configurações e Status")
    st.write(f"**Tipo de Banco de Dados:** `{DB_TYPE.upper()}`")
    st.write(
        f"**LLM Local:** `{'LangChain' if USE_LANGCHAIN else 'API Direta'}`")
    st.write(
        f"**Modelo LLM:** `{st.session_state.get('llm_model', 'Não configurado')}`")
    st.write(f"**Limite de Prompt (chars):** `{MAX_PROMPT_LENGTH_CHARS}`")
    st.write(f"**Limite de Tabela (GB):** `{TABLE_SIZE_LIMIT_GB}`")

    st.subheader("Log de Execução")
    # Exibe os últimos 5 logs de execução para feedback rápido
    for entry in reversed(st.session_state.execution_log[-5:]):
        st.text(entry)

    st.subheader("Privacidade e Segurança")
    st.info("""
        Todos os modelos de linguagem são executados **localmente** em sua máquina.
        Seus dados e prompts **não são enviados para serviços de nuvem externos**,
        garantindo a máxima privacidade. Sempre revise o SQL gerado antes de executar!
    """)

# --- Carregar informações do banco de dados na primeira execução ou se não estiverem carregadas ---
if st.session_state.db_schema_info == "Carregando esquema do banco de dados...":
    with st.spinner("Carregando informações do banco de dados..."):
        update_db_info()
        # Atualiza o modelo LLM exibido na sidebar
        from config import LLM_MODEL
        st.session_state.llm_model = LLM_MODEL

# --- Interface Principal ---

prompt = st.text_area(
    "Digite a instrução em linguagem natural (ex: 'Me mostre os 10 clientes mais recentes'):",
    height=150,
    key="user_prompt"
)

# Botão para converter para SQL
if st.button("Converter para SQL", key="convert_button"):
    st.session_state.last_interaction_time = datetime.now()
    st.session_state.execution_log.append(
        f"{datetime.now().strftime('%H:%M:%S')} - Conversão iniciada.")
    log_event("Botão 'Converter para SQL' clicado.")

    valido, mensagem = validar_prompt(prompt)
    if not valido:
        st.warning(mensagem)
        st.session_state.sql_gerado = ""
        st.session_state.execution_log.append(
            f"{datetime.now().strftime('%H:%M:%S')} - Validação do prompt falhou.")
    else:
        with st.spinner("Gerando SQL... Isso pode levar alguns segundos dependendo do seu LLM local."):
            start_time_llm = time.time()
            generated_sql = gerar_sql_llm(
                prompt,
                st.session_state.db_schema_info,
                "\n".join([
                    f"Tabela: {table_name}, Tamanho: {info['size_bytes'] / (1024**3):.2f} GB, Linhas: {info['row_count']}"
                    for table_name, info in st.session_state.db_table_sizes.items()
                ])
            )
            end_time_llm = time.time()
            llm_duration = end_time_llm - start_time_llm
            st.session_state.execution_log.append(
                f"{datetime.now().strftime('%H:%M:%S')} - LLM gerou SQL em {llm_duration:.2f}s.")

            if generated_sql:
                st.session_state.sql_gerado = generated_sql
                st.success("SQL gerado com sucesso!")
            else:
                st.error(
                    "Falha ao gerar SQL. Verifique os logs para mais detalhes.")
                st.session_state.sql_gerado = ""
                st.session_state.execution_log.append(
                    f"{datetime.now().strftime('%H:%M:%S')} - Falha ao gerar SQL.")

# Exibir informações do banco de dados
display_table_info(st.session_state.db_table_sizes)

# 2. Mostrar o SQL gerado (se existir)
if st.session_state.sql_gerado:
    st.subheader("Instrução SQL Gerada")
    # Adiciona a verificação de comando perigoso antes de exibir
    permitido, aviso = verifica_comando_perigoso(st.session_state.sql_gerado)

    # Adiciona o aviso como comentário no SQL se for um comando perigoso
    sql_to_display = st.session_state.sql_gerado
    if not permitido:
        st.error(aviso)
        st.session_state.execution_log.append(
            f"{datetime.now().strftime('%H:%M:%S')} - SQL perigoso detectado e bloqueado.")
    elif aviso:  # Se for permitido mas com aviso (ex: UPDATE/DELETE com WHERE)
        sql_to_display = aviso + "\n" + st.session_state.sql_gerado
        st.warning("Aviso de segurança adicionado ao SQL. Revise cuidadosamente.")
        st.session_state.execution_log.append(
            f"{datetime.now().strftime('%H:%M:%S')} - Aviso de segurança adicionado ao SQL.")

    st.code(sql_to_display, language='sql', line_numbers=True)

    # 3. Executar o SQL
    if st.button("Executar Script", key="execute_button"):
        st.session_state.last_interaction_time = datetime.now()
        st.session_state.execution_log.append(
            f"{datetime.now().strftime('%H:%M:%S')} - Execução do script solicitada.")
        log_event("Botão 'Executar Script' clicado.")

        # Re-verifica a segurança antes da execução
        permitido, aviso = verifica_comando_perigoso(
            st.session_state.sql_gerado)
        if not permitido:
            st.error(f"Execução bloqueada: {aviso}")
            st.session_state.execution_log.append(
                f"{datetime.now().strftime('%H:%M:%S')} - Execução bloqueada por segurança.")
        else:
            conn = conectar_banco()
            if conn:
                start_time_execution = time.time()
                try:
                    cur = conn.cursor()
                    cur.execute(st.session_state.sql_gerado)

                    # Tenta buscar resultados apenas para SELECT
                    if st.session_state.sql_gerado.strip().upper().startswith("SELECT"):
                        resultado = cur.fetchall()
                        column_names = [desc[0] for desc in cur.description]
                        df_resultado = pd.DataFrame(
                            resultado, columns=column_names)
                        st.success("Consulta executada com sucesso!")
                        st.subheader("Resultado da Consulta")
                        st.dataframe(df_resultado, use_container_width=True)
                        log_event(
                            f"Consulta SELECT executada. {len(resultado)} linhas retornadas.")
                        st.session_state.execution_log.append(
                            f"{datetime.now().strftime('%H:%M:%S')} - Consulta SELECT executada.")
                    else:
                        conn.commit()  # Commit para DML/DDL
                        st.success(
                            "Comando executado com sucesso (sem retorno de dados).")
                        log_event(
                            f"Comando DML/DDL executado: {st.session_state.sql_gerado}")
                        st.session_state.execution_log.append(
                            f"{datetime.now().strftime('%H:%M:%S')} - Comando DML/DDL executado.")

                except Exception as e:
                    st.error(f"Erro na execução do SQL: {e}")
                    log_event(f"Erro na execução do SQL: {e}")
                    st.session_state.execution_log.append(
                        f"{datetime.now().strftime('%H:%M:%S')} - Erro na execução do SQL: {e}")
                finally:
                    end_time_execution = time.time()
                    total_duration = end_time_execution - start_time_execution
                    st.info(
                        f"Tempo total de processamento da execução: {total_duration:.4f} segundos.")
                    log_event(
                        f"Tempo total de processamento da execução: {total_duration:.4f} segundos.")
                    conn.close()
                    log_event("Conexão com o banco de dados fechada.")
                    st.session_state.execution_log.append(
                        f"{datetime.now().strftime('%H:%M:%S')} - Conexão DB fechada.")

            else:
                st.error(
                    "Não foi possível conectar ao banco de dados para executar o script.")
                st.session_state.execution_log.append(
                    f"{datetime.now().strftime('%H:%M:%S')} - Falha na conexão DB para execução.")

    st.markdown("---")
    st.write(
        "A consulta atendeu às suas necessidades? Posso ajudar em mais alguma coisa?")

# --- Lógica de Timeout (simulada) ---
# A cada interação, atualiza o tempo da última interação.
# Se a diferença for maior que 5 minutos, exibe uma mensagem de despedida.
# Nota: Streamlit não encerra a aplicação automaticamente por inatividade.
# Esta é uma mensagem de UI para o usuário.
timeout_minutes = 5
if (datetime.now() - st.session_state.last_interaction_time) > timedelta(minutes=timeout_minutes):
    st.info(
        f"Parece que não houve interação por {timeout_minutes} minutos. Encerrando a sessão de forma amigável. As conexões com o banco de dados são fechadas após cada operação.")
    log_event(
        f"Sessão inativa por {timeout_minutes} minutos. Mensagem de despedida exibida.")
    # Resetar o estado para uma "nova sessão" se o usuário interagir novamente
    st.session_state.sql_gerado = ""
    # Reseta para não mostrar a mensagem repetidamente
    st.session_state.last_interaction_time = datetime.now()
    st.stop()  # Tenta parar a execução do script Streamlit (pode não ser um "fechamento" completo)
