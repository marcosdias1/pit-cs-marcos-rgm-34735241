# arquivo de configuração do projeto
# aqui eu pego as senhas e dados do banco do arquivo .env

import os
from dotenv import load_dotenv

# lê o arquivo .env e joga tudo nas variáveis de ambiente
load_dotenv()

# dados do banco de dados
DB_HOST = os.getenv("DB_HOST")
DB_PORTA = os.getenv("DB_PORTA")
DB_NOME = os.getenv("DB_NOME")
DB_USUARIO = os.getenv("DB_USUARIO")
DB_SENHA = os.getenv("DB_SENHA")

# chave secreta do flask (vai servir depois pro login)
CHAVE_SECRETA = os.getenv("CHAVE_SECRETA")

print(DB_HOST, DB_PORTA, DB_NOME)


# mostrar o link de trocar a senha na tela? (so para demonstracao e testes, no .env: MOSTRAR_LINK_DE_SENHA_NA_TELA=sim)
# com "nao" o link aparece so no terminal onde o Flask esta rodando (o e-mail simulado)
MOSTRAR_LINK_DE_SENHA_NA_TELA = os.getenv("MOSTRAR_LINK_DE_SENHA_NA_TELA", "nao").strip().lower() == "sim"

DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer").strip()
