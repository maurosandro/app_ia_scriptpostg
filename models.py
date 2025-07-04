import re


def verifica_comando_perigoso(sql):
    comando = sql.strip().split()[0].upper()
    if comando in ["DELETE", "UPDATE", "DROP"]:
        if "WHERE" not in sql.upper():
            return False, f"-- ⚠️ Atenção: comando perigoso sem cláusula WHERE!"
        return True, f"-- ⚠️ Verifique cuidadosamente a cláusula WHERE!"
    return True, ""
