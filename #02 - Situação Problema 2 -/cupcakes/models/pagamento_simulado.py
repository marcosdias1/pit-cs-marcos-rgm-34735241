import secrets
from models import validacoes

# pagamento simulado (cartão 11)


# cartões de teste (eles aparecem na tela de pagamento)
CARTAO_APROVADO = "4111111111111111"
CARTAO_RECUSADO = "4000000000000002"


# função que deixa só os números do cartão (tira espaço e traço)
def limpar_numero(numero):
    numero = numero.replace(" ", "")
    numero = numero.replace("-", "")
    return numero

# função que deixa o número do cartão em grupos de 4 (ex: 4111 1111 1111 1111)
def formatar_numero(numero):
    grupos = []
    for i in range(0, len(numero), 4):
        grupos.append(numero[i:i + 4])
    return " ".join(grupos)


# função que lê a validade do cartão (ex: "12/35" ou "12/2035")
# devolve (mes, ano) ou None se o texto não faz sentido
def ler_validade(texto):
    texto = texto.replace(" ", "")
    partes = texto.split("/")
    if len(partes) != 2:
        return None

    mes_texto = partes[0]
    ano_texto = partes[1]
    if validacoes.so_tem_numeros(mes_texto) == False or validacoes.so_tem_numeros(ano_texto) == False:
        return None
    if len(mes_texto) > 2:
        return None

    mes = int(mes_texto)
    ano = int(ano_texto)
    # ano com 2 números (35) vira 2035
    if len(ano_texto) == 2:
        ano = 2000 + ano
    elif len(ano_texto) != 4:
        return None

    if mes < 1 or mes > 12:
        return None
    return (mes, ano)

# função que confere os dados do cartão
# devolve um dicionário com os erros (se estiver vazio, está tudo certo)
def validar_cartao(numero, nome, validade, cvv, hoje):
    erros = {}

    # número: só números, de 13 a 19 dígitos
    numero = limpar_numero(numero)
    if validacoes.so_tem_numeros(numero) == False or len(numero) < 13 or len(numero) > 19:
        erros["numero"] = "Número do cartão inválido."

    # nome impresso no cartão
    nome = nome.strip()
    if nome == "" or len(nome) > 60:
        erros["nome"] = "Informe o nome impresso no cartão."

    # validade: o cartão vale até o fim do mês que está escrito
    lida = ler_validade(validade)
    if lida is None:
        erros["validade"] = "Validade inválida. Exemplo: 12/35"
    else:
        mes = lida[0]
        ano = lida[1]
        if ano < hoje.year or (ano == hoje.year and mes < hoje.month):
            erros["validade"] = "Cartão vencido."
        elif ano > hoje.year + 20:
            erros["validade"] = "Validade inválida. Exemplo: 12/35"

    # cvv: 3 ou 4 números
    if validacoes.so_tem_numeros(cvv) == False or (len(cvv) != 3 and len(cvv) != 4):
        erros["cvv"] = "CVV inválido. São 3 números."

    return erros

# função que SIMULA a operadora do cartão
# devolve um dicionário: aprovado (True ou False), codigo da transação e o motivo
def autorizar_cartao(numero):
    numero = limpar_numero(numero)
    resultado = {}
    resultado["codigo"] = "SIM-" + secrets.token_hex(8).upper()

    # o cartão de teste de recusa é recusado, qualquer outro cartão válido é aprovado
    if numero == CARTAO_RECUSADO:
        resultado["aprovado"] = False
        resultado["motivo"] = "Pagamento recusado pela operadora (simulação)."
    else:
        resultado["aprovado"] = True
        resultado["motivo"] = ""
    return resultado

# função que SIMULA o PIX: sempre aprova (a pessoa clicou em "Confirmar pagamento")
def autorizar_pix():
    resultado = {}
    resultado["codigo"] = "SIM-PIX-" + secrets.token_hex(8).upper()
    resultado["aprovado"] = True
    resultado["motivo"] = ""
    return resultado