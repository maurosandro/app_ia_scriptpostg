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
import psycopg2
import pymysql
import pyodbc # Para SQL Server
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_TYPE
from utils import log_event

def conectar_banco():
    """
    Estabelece uma conexão com o banco de dados configurado.

    Returns:
        objeto de conexão | None: O objeto de conexão se a conexão for bem-sucedida, caso contrário None.
    """
    conn = None
    try:
        if DB_TYPE == 'postgresql':
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                dbname=DB_NAME
            )
            log_event(f"Conexão PostgreSQL estabelecida com {DB_NAME}.")
        elif DB_TYPE == 'sqlserver':
            # Para SQL Server, você precisa de um driver ODBC instalado.
            # Ex: 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=host,port;DATABASE=db_name;UID=user;PWD=password'
            # Certifique-se de que o driver ODBC correto esteja instalado no seu sistema.
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={DB_HOST},{DB_PORT};"
                f"DATABASE={DB_NAME};"
                f"UID={DB_USER};"
                f"PWD={DB_PASSWORD}"
            )
            conn = pyodbc.connect(conn_str)
            log_event(f"Conexão SQL Server estabelecida com {DB_NAME}.")
        elif DB_TYPE == 'mysql':
            conn = pymysql.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            log_event(f"Conexão MySQL estabelecida com {DB_NAME}.")
        else:
            log_event(f"Tipo de banco de dados não suportado: {DB_TYPE}")
            return None
        return conn
    except Exception as e:
        log_event(f"Erro ao conectar ao banco de dados {DB_TYPE}: {e}")
        return None

def get_table_schema(conn) -> str:
    """
    Recupera o esquema das tabelas do banco de dados.

    Args:
        conn: Objeto de conexão com o banco de dados.

    Returns:
        str: Uma string formatada com o esquema das tabelas (nome da tabela, colunas e tipos).
    """
    schema_info = []
    try:
        cursor = conn.cursor()
        if DB_TYPE == 'postgresql':
            cursor.execute("""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)
        elif DB_TYPE == 'sqlserver':
            cursor.execute("""
                SELECT
                    t.name AS table_name,
                    c.name AS column_name,
                    ty.name AS data_type
                FROM sys.tables t
                INNER JOIN sys.columns c ON t.object_id = c.object_id
                INNER JOIN sys.types ty ON c.system_type_id = ty.system_type_id
                ORDER BY t.name, c.column_id;
            """)
        elif DB_TYPE == 'mysql':
            cursor.execute(f"""
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = '{DB_NAME}'
                ORDER BY table_name, ordinal_position;
            """)
        else:
            log_event(f"Tipo de banco de dados {DB_TYPE} não suportado para obter esquema.")
            return "Informações do esquema não disponíveis para este tipo de banco de dados."

        rows = cursor.fetchall()
        current_table = None
        for row in rows:
            table_name, column_name, data_type = row
            if table_name != current_table:
                if current_table is not None:
                    schema_info.append("") # Linha em branco entre tabelas
                schema_info.append(f"Tabela: {table_name}")
                current_table = table_name
            schema_info.append(f"  - {column_name} ({data_type})")
        cursor.close()
        log_event("Esquema do banco de dados recuperado com sucesso.")
        return "\n".join(schema_info)
    except Exception as e:
        log_event(f"Erro ao obter esquema do banco de dados: {e}")
        return f"Erro ao obter esquema do banco de dados: {e}"

def get_table_size_and_row_count(conn) -> dict:
    """
    Recupera o tamanho aproximado e a contagem de linhas de todas as tabelas.

    Args:
        conn: Objeto de conexão com o banco de dados.

    Returns:
        dict: Um dicionário onde as chaves são nomes de tabelas e os valores são dicionários
              com 'size_bytes' e 'row_count'.
    """
    table_stats = {}
    try:
        cursor = conn.cursor()
        if DB_TYPE == 'postgresql':
            cursor.execute("""
                SELECT
                    relname AS table_name,
                    pg_total_relation_size(oid) AS total_size_bytes,
                    reltuples AS row_count
                FROM pg_class
                WHERE relkind = 'r' AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
                ORDER BY relname;
            """)
        elif DB_TYPE == 'sqlserver':
            cursor.execute("""
                SELECT
                    t.name AS table_name,
                    SUM(a.total_pages) * 8 * 1024 AS total_size_bytes, -- 8KB por página
                    SUM(p.rows) AS row_count
                FROM sys.tables t
                INNER JOIN sys.indexes i ON t.object_id = i.object_id
                INNER JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
                INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
                GROUP BY t.name
                ORDER BY t.name;
            """)
        elif DB_TYPE == 'mysql':
            cursor.execute(f"""
                SELECT
                    table_name,
                    data_length + index_length AS total_size_bytes,
                    table_rows AS row_count
                FROM information_schema.tables
                WHERE table_schema = '{DB_NAME}'
                ORDER BY table_name;
            """)
        else:
            log_event(f"Tipo de banco de dados {DB_TYPE} não suportado para obter tamanho/linhas.")
            return {}

        rows = cursor.fetchall()
        for row in rows:
            table_name = row[0]
            size_bytes = row[1] if row[1] is not None else 0
            row_count = row[2] if row[2] is not None else 0
            table_stats[table_name] = {
                'size_bytes': size_bytes,
                'row_count': row_count
            }
        cursor.close()
        log_event("Tamanhos e contagens de linhas das tabelas recuperados com sucesso.")
        return table_stats
    except Exception as e:
        log_event(f"Erro ao obter tamanho e contagem de linhas das tabelas: {e}")
        return {}