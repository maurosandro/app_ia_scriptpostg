import psycopg2
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from utils import log_event


def conectar_banco():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        log_event("Conexão com o banco estabelecida.")
        return conn
    except psycopg2.Error as e:
        log_event(f"Erro ao conectar ao banco: {e}")
        return None
