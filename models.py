import re
from utils import log_event


def verifica_comando_perigoso(sql: str) -> tuple[bool, str]:
    """
    Verifica comandos SQL potencialmente perigosos (DELETE, UPDATE, DROP)
    e garante a presença da cláusula WHERE. Adiciona comentários de segurança.

    Args:
        sql (str): A instrução SQL a ser verificada.

    Returns:
        tuple[bool, str]: Uma tupla onde o primeiro elemento indica se o comando é seguro (True/False)
                          e o segundo elemento é uma mensagem de aviso ou um comentário a ser adicionado ao SQL.
    """
    sql_upper = sql.strip().upper()
    comando_match = re.match(r"^(DELETE|UPDATE|DROP)\s", sql_upper)

    if comando_match:
        comando = comando_match.group(1)
        log_event(f"Verificando comando perigoso: {comando}")

        # Para DELETE, UPDATE, DROP, a cláusula WHERE é obrigatória
        if "WHERE" not in sql_upper:
            log_event(f"Comando {comando} sem cláusula WHERE detectado.")
            return False, f"-- ⚠️ ATENÇÃO: O comando {comando} é perigoso e não contém uma cláusula WHERE. " \
                          f"Isso pode afetar todos os registros da tabela. Execução bloqueada."
        else:
            log_event(
                f"Comando {comando} com cláusula WHERE detectado. Adicionando aviso.")
            return True, f"-- ⚠️ ATENÇÃO: Comando '{comando}' detectado. Revise cuidadosamente a cláusula WHERE para evitar perda de dados.\n" \
                         f"-- Este comando afetará apenas os registros que correspondem à condição WHERE.\n" \
                         f"-- Certifique-se de ter um backup antes de executar comandos de modificação de dados."
    else:
        log_event("Nenhum comando perigoso (DELETE, UPDATE, DROP) detectado.")
        return True, ""  # Nenhum aviso necessário para comandos não perigosos
