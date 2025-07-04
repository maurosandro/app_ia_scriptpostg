from langchain_core.messages import HumanMessage
from langchain_community.chat_models import ChatOllama  # Corrigido para modo chat
from langchain.prompts import ChatPromptTemplate

# Conecte ao modelo local via Ollama
llm = ChatOllama(model="llama3", base_url="http://localhost:11434")

#llm = Ollama(model="nome-do-modelo", base_url="http://localhost:11434")  # ou LM Studio

template = ChatPromptTemplate.from_template(
    "Converta a instrução abaixo em SQL PostgreSQL seguro, com cláusulas adequadas e proteção:\n\n{instrucao}"
)

def gerar_sql_com_langchain(instrucao):
    prompt = template.format_messages(instrucao=instrucao)
    response = llm.invoke(prompt)
    return response.content.strip()
