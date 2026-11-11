# regras do cupom de desconto (cartão 09)

from decimal import Decimal, ROUND_HALF_UP


# função que confere se o cupom pode ser usado agora
# devolve "" se pode, ou o texto do erro pra mostrar pra pessoa
#   cupom: o dicionário do cupom (ou None se não achou)
#   hoje: a data de hoje
#   id_cliente: quem está comprando (None se for visitante)
#   ja_usado: se esse cliente já usou esse cupom num pedido confirmado
#   ja_comprou: se esse cliente já tem algum pedido confirmado

def validar_cupom(cupom, hoje, id_cliente, ja_usado, ja_comprou):
    if cupom is None:
        return "Cupom não encontrado."

    # cupom desativado é como se não existisse
    if cupom["ativo"] == False:
        return "Cupom não encontrado."

    # prazo de validade
    if hoje < cupom["valido_de"]:
        return "Esse cupom só começa a valer em " + cupom["valido_de"].strftime("%d/%m/%Y") + "."
    if hoje > cupom["valido_ate"]:
        return "Esse cupom está vencido."

    # cupom pessoal (ligado a um cpf) só vale pra quem é o dono
    if cupom["id_cliente"] is not None:
        if cupom["id_cliente"] != id_cliente:
            return "Esse cupom é de outra conta."

    # uso único: cada cliente usa uma vez só
    # (o visitante não tem como a gente saber se já usou, então precisa ter conta)
    if cupom["uso_unico"] == True:
        if id_cliente is None:
            return "Esse cupom só vale para quem tem conta. Entre na sua conta para usar."
        if ja_usado == True:
            return "Esse cupom já foi usado."

    # primeira compra
    if cupom["primeira_compra"] == True:
        if id_cliente is None:
            return "Esse cupom é só para a primeira compra de quem tem conta. Entre na sua conta para usar."
        if ja_comprou == True:
            return "Esse cupom vale só na primeira compra."

    return ""


# função que calcula quanto o cupom desconta do subtotal
def calcular_desconto(cupom, subtotal):
    if cupom is None:
        return Decimal("0.00")

    if cupom["tipo"] == "VALOR_FIXO":
        desconto = cupom["valor"]
    else:
        desconto = (subtotal * cupom["valor"] / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # o desconto nunca pode ser maior que o subtotal
    if desconto > subtotal:
        desconto = subtotal

    return desconto