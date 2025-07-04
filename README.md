Conversor de Linguagem Natural para SQL
Este projeto é uma aplicação Streamlit que permite aos usuários converter instruções em linguagem natural em consultas SQL, interagir com um banco de dados local (PostgreSQL, SQL Server ou MySQL) e visualizar os resultados. A aplicação foca na segurança, controle de tokens e análise de volume de dados para otimizar o desempenho e proteger o banco de dados.

Funcionalidades
Conversão de LN para SQL: Utilize modelos de linguagem grandes (LLMs) locais (LM Studio ou Ollama) para transformar prompts em linguagem natural em instruções SQL.

Conexão a Bancos de Dados: Suporte para PostgreSQL, SQL Server e MySQL.

Análise Prévia de Tabelas: Antes de gerar o SQL, a aplicação analisa o tamanho e o volume de dados das tabelas envolvidas. Se uma tabela exceder 1GB, um LIMIT ou TOP é automaticamente adicionado à consulta para evitar sobrecarga.

Segurança e Validação:

Validação de prompts para evitar comandos perigosos (TRUNCATE, DROP DATABASE, GRANT, REVOKE).

Verificação obrigatória da cláusula WHERE para comandos UPDATE, DELETE e DROP.

Comentários de segurança adicionados ao SQL gerado para comandos potencialmente perigosos.

Ênfase na privacidade dos dados, pois todo o processamento LLM ocorre localmente.

Logging Completo: Todas as ações e eventos importantes são registrados em um arquivo de log (logs/app.log).

Controle de Tokens: Limitação do tamanho do prompt e da resposta para otimizar o uso de recursos do LLM.

Interface Amigável: Exibição do SQL gerado, resultados em DataFrame e tempo de execução total.

Feedback ao Usuário: Mensagens informativas sobre o status da consulta e sugestões.

Estrutura do Projeto
.
├── app.py              # Aplicação principal Streamlit
├── config.py           # Configurações globais (DB, LLM, logging, limites)
├── db.py               # Funções de conexão e interação com o banco de dados
├── llm_client.py       # Cliente para interação com LLMs locais (LM Studio/Ollama API)
├── langchain_client.py # Cliente para interação com LLMs locais via LangChain
├── models.py           # Lógica de validação e segurança SQL
├── utils.py            # Funções utilitárias (logging, validação de prompt, tokenização)
├── README.md           # Este arquivo
└── logs/               # Diretório para arquivos de log
    └── app.log         # Arquivo de log da aplicação

Pré-requisitos
Antes de executar a aplicação, certifique-se de ter o seguinte instalado:

Python 3.8+

Pip (gerenciador de pacotes Python)

Um servidor LLM local rodando (LM Studio ou Ollama) com um modelo baixado.

Instalação
Clone o repositório (se aplicável) ou crie a estrutura de pastas:
Crie os diretórios e arquivos conforme a estrutura acima.

Instale as dependências Python:
Crie um arquivo requirements.txt na raiz do projeto com o seguinte conteúdo:

streamlit
psycopg2-binary  # ou psycopg2 para sistemas com compilador C
pymysql
pyodbc
requests
langchain
langchain-community
python-dotenv

Em seguida, instale-as:

pip install -r requirements.txt

Observação para psycopg2: Se você tiver problemas de instalação com psycopg2, tente psycopg2-binary.

Observação para pyodbc: Pode exigir a instalação de drivers ODBC para SQL Server em seu sistema operacional.

Configurar o LLM Local:
Certifique-se de que seu servidor LM Studio ou Ollama esteja em execução e que você tenha um modelo baixado e carregado.

Ollama: ollama run <nome-do-modelo> (ex: ollama run llama3)

LM Studio: Inicie o LM Studio e carregue um modelo.

Configurar o config.py:
Abra config.py e preencha os detalhes de conexão do seu banco de dados e as URLs/modelos do LLM.

# Exemplo de configuração para PostgreSQL
DB_TYPE = 'postgresql' # 'postgresql', 'sqlserver', 'mysql'
DB_HOST = 'localhost'
DB_PORT = 5432
DB_USER = 'your_user'
DB_PASSWORD = 'your_password'
DB_NAME = 'your_database'

# Exemplo de configuração para LLM (Ollama)
LLM_API_URL = "http://localhost:11434/api/generate" # Ou LM Studio: "http://localhost:1234/v1/completions"
LLM_MODEL = "llama3" # Nome do modelo no Ollama ou LM Studio
USE_LANGCHAIN = True # Define se usa a integração direta ou LangChain

Como Executar
Navegue até o diretório raiz do projeto no terminal.

Execute a aplicação Streamlit:

streamlit run app.py

A aplicação será aberta em seu navegador padrão.

Uso
Digite sua instrução em linguagem natural na caixa de texto fornecida.

Clique em "Converter para SQL" para que o LLM gere a instrução SQL. A aplicação exibirá o SQL gerado e informações sobre as tabelas envolvidas (tamanho, linhas).

Revise o SQL gerado. Se for um comando perigoso (UPDATE, DELETE, DROP), a aplicação adicionará um aviso e garantirá a presença da cláusula WHERE.

Clique em "Executar Script" para executar a consulta no seu banco de dados. O resultado será exibido em um DataFrame, juntamente com o tempo total de execução.

Notas de Segurança e Privacidade
Processamento Local: Todos os modelos de linguagem utilizados são executados localmente em sua máquina (LM Studio ou Ollama). Isso significa que seus dados e prompts não são enviados para nenhum serviço de nuvem externo, garantindo a máxima privacidade.

Validação de Entrada: A aplicação implementa validações para evitar que comandos SQL perigosos sejam gerados ou executados sem a devida atenção.

Revisão Humana: É altamente recomendável que você sempre revise o SQL gerado antes de executá-lo, especialmente para comandos que modificam dados (INSERT, UPDATE, DELETE) ou a estrutura do banco (DROP, ALTER). A ferramenta é uma auxiliar, mas a responsabilidade final é do usuário.

Contribuição
Sinta-se à vontade para contribuir com melhorias, relatar bugs ou sugerir novas funcionalidades.