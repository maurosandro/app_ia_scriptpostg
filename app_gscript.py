import streamlit as st
from config import STREAMLIT_APP_NAME
from db import conectar_banco
from llm_client import gerar_sql
from llm_client import gerar_sql_cached
from models import verifica_comando_perigoso
from utils import log_event, validar_prompt

st.set_page_config(page_title=STREAMLIT_APP_NAME)
st.title(STREAMLIT_APP_NAME)

prompt = st.text_area("Digite a instrução em linguagem natural:")

USE_LANGCHAIN = True

if USE_LANGCHAIN:
    from langchain_client import gerar_sql_com_langchain
    sql = gerar_sql_com_langchain(prompt)
else:
    sql = gerar_sql_cached(prompt)

if "sql_gerado" not in st.session_state:
    st.session_state.sql_gerado = ""

# sql = ""
sql = gerar_sql_cached(prompt)

# 1. Validar e gerar SQL
if st.button("Converter para SQL"):
    valido, mensagem = validar_prompt(prompt)
    if not valido:
        st.warning(mensagem)
    else:
        if USE_LANGCHAIN:
            from langchain_client import gerar_sql_com_langchain
            sql = gerar_sql_com_langchain(prompt)
        else:
            sql = gerar_sql_cached(prompt)

        st.session_state.sql_gerado = sql
        st.success("SQL gerado com sucesso!")

# 2. Mostrar o SQL gerado (se existir)
if st.session_state.sql_gerado:
    st.subheader("SQL Gerado")
    st.code(st.session_state.sql_gerado, language='sql')

    # 3. Executar o SQL
    if st.button("Executar Script"):
        permitido, aviso = verifica_comando_perigoso(
            st.session_state.sql_gerado)
        st.warning(aviso)

        if permitido:
            conn = conectar_banco()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(st.session_state.sql_gerado)

                    try:
                        resultado = cur.fetchall()
                        st.success("Consulta executada com sucesso!")
                        st.dataframe(resultado)
                    except:
                        st.success("Comando executado sem retorno.")
                    conn.commit()
                    log_event(f"SQL executado: {st.session_state.sql_gerado}")
                except Exception as e:
                    st.error(f"Erro na execução: {e}")
                    log_event(f"Erro ao executar SQL: {e}")
                finally:
                    conn.close()
