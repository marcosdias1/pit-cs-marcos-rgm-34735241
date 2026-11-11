# regras do histórico de compras e da recompra (cartão 15)
# aqui só tem conta e texto: nada de banco de dados (assim dá pra testar sem o PostgreSQL)

# o texto de cada status do pedido
NOMES_DO_STATUS = {
    "AGUARDANDO_PAGAMENTO": "Aguardando pagamento",
    "CONFIRMADO": "Pedido confirmado",
    "EM_PREPARO": "Em preparo",
    "SAIU_PARA_ENTREGA": "Saiu para entrega",
    "ENTREGUE": "Entregue",
    "CANCELADO": "Cancelado",
}

# os status que têm tela de acompanhamento (o pedido cancelado e o que não foi pago não têm)
STATUS_COM_ACOMPANHAMENTO = ["CONFIRMADO", "EM_PREPARO", "SAIU_PARA_ENTREGA", "ENTREGUE"]

# os status em que o pedido ainda está andando (a simulação ainda pode mudar o status)
STATUS_EM_ANDAMENTO = ["CONFIRMADO", "EM_PREPARO", "SAIU_PARA_ENTREGA"]

# quantos pedidos aparecem na lista (os mais novos)
LIMITE_DE_PEDIDOS = 20


# função que devolve o texto do status (se não conhecer o status, devolve ele mesmo)
def texto_do_status(status):
    return NOMES_DO_STATUS.get(status, status)


# função que diz se o pedido tem o botão "Acompanhar"
def pode_acompanhar(status):
    return status in STATUS_COM_ACOMPANHAMENTO


# função que diz se o pedido ainda está andando
def esta_em_andamento(status):
    return status in STATUS_EM_ANDAMENTO


# função que escreve a data do pedido, ex: "08/11/2026 às 18:05"
def formatar_data(data):
    if data is None:
        return ""
    return data.strftime("%d/%m/%Y") + " às " + data.strftime("%H:%M")


# função que resume os itens do pedido em uma linha, ex: "2x Chocolate, 1x Morango e mais 2 itens"
# itens é uma lista de dicionários com "nome" e "quantidade"
def resumir_itens(itens, maximo=3):
    partes = []
    for item in itens:
        if len(partes) < maximo:
            partes.append(str(item["quantidade"]) + "x " + item["nome"])

    texto = ", ".join(partes)

    sobraram = len(itens) - maximo
    if sobraram == 1:
        texto = texto + " e mais 1 item"
    elif sobraram > 1:
        texto = texto + " e mais " + str(sobraram) + " itens"
    return texto


# função que escreve as mensagens que aparecem depois de "Comprar de novo"
# quantos = quantos itens foram para o carrinho
# problemas = lista de dicionários com "nome" e "motivo" dos itens que não foram
# devolve duas mensagens: a de sucesso e a de aviso (qualquer uma pode ser "")
def montar_mensagens_da_recompra(quantos, problemas):
    mensagem_ok = ""
    if quantos == 1:
        mensagem_ok = "1 item foi para o carrinho. Os preços são os de hoje."
    elif quantos > 1:
        mensagem_ok = str(quantos) + " itens foram para o carrinho. Os preços são os de hoje."

    # cada motivo já termina com ponto (vem da função que coloca no carrinho)
    mensagem_aviso = ""
    if len(problemas) > 0:
        partes = []
        for problema in problemas:
            partes.append(problema["nome"] + ": " + problema["motivo"])
        mensagem_aviso = "Não deu para colocar no carrinho. " + " ".join(partes)

    return mensagem_ok, mensagem_aviso