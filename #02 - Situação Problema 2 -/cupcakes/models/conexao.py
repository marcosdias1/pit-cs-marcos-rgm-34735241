# arquivo que faz a conexão com o banco de dados postgresql
# todo model que precisar do banco chama a função daqui

import psycopg2
from config import *


# função que abre a conexão com o banco e devolve ela
def pegar_conexao():
    con = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORTA,
        dbname=DB_NOME,
        user=DB_USUARIO,
        password=DB_SENHA,
        sslmode=DB_SSLMODE
    )
    print("conexão com o banco estabelecida")
    return con