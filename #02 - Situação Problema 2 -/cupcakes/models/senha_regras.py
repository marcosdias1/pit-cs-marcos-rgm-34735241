# regras da recuperação de senha (cartão 19)
# aqui só tem conta e texto: nada de banco de dados (assim dá pra testar sem o PostgreSQL)
# regra do cartão: o link vale 1 hora e só pode ser usado uma vez

import secrets
import hashlib

# quantos minutos o link vale
MINUTOS_DE_VALIDADE = 60

# letras e números que um token pode ter (o token_urlsafe só usa esses)
LETRAS_DO_TOKEN = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"


# função que cria um token novo: uma sequência grande de letras e números impossível de adivinhar
def gerar_token():
    return secrets.token_urlsafe(32)


# função que transforma o token em um código de 64 letras e números (hash)
# no banco eu guardo só o hash, nunca o token, igual a senha: se alguém ver o banco, não consegue usar o link
def hash_do_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# função que confere se o texto do link parece um token (tamanho e letras)
# serve só pra nem perguntar pro banco quando o link é lixo
def token_parece_valido(token):
    if len(token) < 20 or len(token) > 100:
        return False
    for letra in token:
        if letra not in LETRAS_DO_TOKEN:
            return False
    return True


# função que escreve o e-mail com o link (devolve o assunto e o texto)
def montar_email(nome, link):
    assunto = "Troque a sua senha - Loja de Cupcakes"
    texto = "Olá, " + nome + "!\n\n"
    texto = texto + "Recebemos um pedido para trocar a senha da sua conta.\n"
    texto = texto + "Para escolher uma senha nova, abra o link abaixo:\n\n"
    texto = texto + link + "\n\n"
    texto = texto + "O link vale por " + str(MINUTOS_DE_VALIDADE) + " minutos e só pode ser usado uma vez.\n"
    texto = texto + "Se não foi você que pediu, ignore este e-mail: a sua senha continua a mesma."
    return assunto, texto