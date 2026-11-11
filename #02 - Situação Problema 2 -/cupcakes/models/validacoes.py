# arquivo com as funções que conferem se o que a pessoa digitou está certo
# (cpf, senha, email, celular, cep e uf)
# as regras vêm dos cartões de história 16 e 17

import string

LISTA_UF = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
            "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]


# função que tira os pontos, traços, parênteses e espaços de um texto
# ex: "123.456.789-09" vira "12345678909"
def tirar_enfeites(texto):
    texto = texto.replace(".", "")
    texto = texto.replace("-", "")
    texto = texto.replace("(", "")
    texto = texto.replace(")", "")
    texto = texto.replace(" ", "")
    return texto


# função que confere se o texto tem SÓ números
def so_tem_numeros(texto):
    # texto vazio não vale
    if texto == "":
        return False
    for letra in texto:
        if letra not in "0123456789":
            return False
    return True


# função que valida o cpf (confere os dois dígitos verificadores)
def validar_cpf(cpf):
    # tira os pontos e traços
    cpf = tirar_enfeites(cpf)
    # se tem letra ou símbolo já está errado
    if so_tem_numeros(cpf) == False:
        return False
    # se não tem 11 números também está errado
    if len(cpf) != 11:
        return False
    else:
        # se é tudo igual (ex: 11111111111) também é inválido
        if cpf == cpf[0] * 11:
            return False
        else:
            # primeiro dígito verificador
            soma = 0
            for i in range(9):
                soma = soma + int(cpf[i]) * (10 - i)
            d1 = (soma * 10) % 11
            if d1 == 10:
                d1 = 0
            # segundo dígito verificador
            soma = 0
            for i in range(10):
                soma = soma + int(cpf[i]) * (11 - i)
            d2 = (soma * 10) % 11
            if d2 == 10:
                d2 = 0
            # compara com os dois últimos números do cpf
            if d1 == int(cpf[9]) and d2 == int(cpf[10]):
                return True
            else:
                return False


# função que valida a senha (cartão 17)
# regra RN: 8 ou mais caracteres, com uma letra maiúscula e um caractere especial
def validar_senha(senha):
    # mais de 8 quer dizer 9 ou mais
    if len(senha) < 8:
        return False

    tem_maiuscula = False
    tem_especial = False
    for letra in senha:
        if letra.isupper():
            tem_maiuscula = True
        # string.punctuation tem todos os símbolos (!@#$% etc)
        if letra in string.punctuation:
            tem_especial = True

    if tem_maiuscula == True and tem_especial == True:
        return True
    else:
        return False


# função que valida o email
def validar_email(email):
    if len(email) > 120:
        return False
    if " " in email:
        return False
    # tem que ter um @ só
    if email.count("@") != 1:
        return False
    partes = email.split("@")
    antes = partes[0]
    depois = partes[1]
    # tem que ter alguma coisa antes do @
    if antes == "":
        return False
    # depois do @ tem que ter um ponto no meio (ex: gmail.com)
    if "." not in depois:
        return False
    if depois.startswith(".") or depois.endswith("."):
        return False
    return True


# função que valida o celular (10 ou 11 números, com ddd)
def validar_celular(celular):
    celular = tirar_enfeites(celular)
    if so_tem_numeros(celular) == False:
        return False
    if len(celular) == 10 or len(celular) == 11:
        return True
    else:
        return False

# função que valida o cep (8 números)
def validar_cep(cep):
    cep = tirar_enfeites(cep)
    if so_tem_numeros(cep) == False:
        return False
    if len(cep) == 8:
        return True
    else:
        return False

# função que confere o formulário de cadastro inteiro
# devolve um dicionário com os erros (se estiver vazio, está tudo certo)
def conferir_cadastro(nome, email, celular, cpf, senha, cep, rua, numero, bairro, cidade, uf):
    erros = {}

    if nome == "":
        erros["nome"] = "Informe seu nome."
    else:
        if len(nome) > 100:
            erros["nome"] = "O nome pode ter no máximo 100 letras."

    if validar_cpf(cpf) == False:
        erros["cpf"] = "CPF inválido"

    if validar_email(email) == False:
        erros["email"] = "E-mail inválido. Exemplo: nome@gmail.com"

    if validar_celular(celular) == False:
        erros["celular"] = "Celular inválido. Digite o DDD e o número."

    if validar_cep(cep) == False:
        erros["cep"] = "CEP inválido. Digite os 8 números."

    if rua == "" or len(rua) > 120:
        erros["rua"] = "Informe a rua."

    if numero == "" or len(numero) > 10:
        erros["numero"] = "Informe o número."

    if bairro == "" or len(bairro) > 60:
        erros["bairro"] = "Informe o bairro."

    if cidade == "" or len(cidade) > 60:
        erros["cidade"] = "Informe a cidade."

    if uf not in LISTA_UF:
        erros["uf"] = "Estado inválido. Exemplo: SP"

    if validar_senha(senha) == False:
        erros["senha"] = "A senha precisa ter no mínimo 8 caracteres, uma letra maiúscula e um caractere especial."
    return erros


# função que confere só o endereço de entrega (tela de fechar pedido)
def conferir_endereco(cep, rua, numero, bairro, cidade, uf):
    erros = {}

    if validar_cep(cep) == False:
        erros["cep"] = "CEP inválido. Digite os 8 números."

    if rua == "" or len(rua) > 120:
        erros["rua"] = "Informe a rua."

    if numero == "" or len(numero) > 10:
        erros["numero"] = "Informe o número."

    if bairro == "" or len(bairro) > 60:
        erros["bairro"] = "Informe o bairro."

    if cidade == "" or len(cidade) > 60:
        erros["cidade"] = "Informe a cidade."

    if uf not in LISTA_UF:
        erros["uf"] = "Estado inválido. Exemplo: SP"

    return erros


# função que confere o contato do visitante (nome, e-mail e celular)
def conferir_contato(nome, email, celular):
    erros = {}

    if nome == "":
        erros["nome"] = "Informe seu nome."
    else:
        if len(nome) > 100:
            erros["nome"] = "O nome pode ter no máximo 100 letras."

    if validar_email(email) == False:
        erros["email"] = "E-mail inválido. Exemplo: nome@gmail.com"

    if validar_celular(celular) == False:
        erros["celular"] = "Celular inválido. Digite o DDD e o número."

    return erros