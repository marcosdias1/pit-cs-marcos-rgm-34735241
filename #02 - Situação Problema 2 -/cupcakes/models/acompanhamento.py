# regras do acompanhamento do pedido (cartão 12)
# SIMPLIFICAÇÃO: como não tem funcionário nem entregador no sistema (cartões 13 e 14), o status do pedido avança sozinho com o tempo
# os tempos abaixo são de DEMONSTRAÇÃO (bem rápidos, pra dar pra ver o status mudar durante um teste)

# as etapas do pedido, na ordem
ETAPAS = ["CONFIRMADO", "EM_PREPARO", "SAIU_PARA_ENTREGA", "ENTREGUE"]

# o texto de cada etapa
TEXTOS = {
    "CONFIRMADO": "Pedido confirmado",
    "EM_PREPARO": "Em preparo",
    "SAIU_PARA_ENTREGA": "Saiu para entrega",
    "ENTREGUE": "Entregue",
}

# uma frase explicando cada etapa
DESCRICOES = {
    "CONFIRMADO": "Recebemos o seu pedido e o pagamento foi aprovado.",
    "EM_PREPARO": "Estamos preparando e embalando os seus cupcakes.",
    "SAIU_PARA_ENTREGA": "O seu pedido saiu para entrega. Fique de olho na porta!",
    "ENTREGUE": "Pedido entregue. Bom apetite!",
}

# quantos segundos depois da confirmação cada etapa começa (tempo de demonstração)
SEGUNDOS_DE_CADA_ETAPA = {
    "CONFIRMADO": 0,
    "EM_PREPARO": 30,
    "SAIU_PARA_ENTREGA": 90,
    "ENTREGUE": 150,
}

# quanto por cento do tempo previsto ainda falta em cada etapa
# (a estimativa muda quando o status muda, como pede o cartão 12)
QUANTO_FALTA = {
    "CONFIRMADO": 100,
    "EM_PREPARO": 75,
    "SAIU_PARA_ENTREGA": 40,
    "ENTREGUE": 0,
}


# função que diz em qual etapa o pedido deveria estar, pelo tempo que passou desde a confirmação
def status_esperado(segundos):
    esperado = "CONFIRMADO"
    for etapa in ETAPAS:
        if segundos >= SEGUNDOS_DE_CADA_ETAPA[etapa]:
            esperado = etapa
    return esperado


# função que diz a posição da etapa na lista (0, 1, 2 ou 3)
# devolve -1 se o status não faz parte do acompanhamento (ex: CANCELADO)
def posicao_da_etapa(status):
    if status in ETAPAS:
        return ETAPAS.index(status)
    return -1


# função que monta a lista de etapas pra tela, dizendo o que já foi feito, o que é agora e o que vem depois
def montar_etapas(status):
    posicao_atual = posicao_da_etapa(status)

    lista = []
    for i in range(len(ETAPAS)):
        etapa = {}
        etapa["codigo"] = ETAPAS[i]
        etapa["texto"] = TEXTOS[ETAPAS[i]]

        if status == "ENTREGUE" or i < posicao_atual:
            etapa["estado"] = "feito"
        elif i == posicao_atual:
            etapa["estado"] = "atual"
        else:
            etapa["estado"] = "proximo"

        lista.append(etapa)
    return lista


# função que estima quantos minutos faltam pra entrega, de 5 em 5 minutos
# minutos_previstos é o tempo total que o frete previu pro pedido
def estimar_minutos(status, minutos_previstos):
    if status not in QUANTO_FALTA:
        return 0

    minutos = minutos_previstos * QUANTO_FALTA[status] / 100
    if minutos <= 0:
        return 0

    # arredonda pra múltiplo de 5 (e nunca menos que 5)
    arredondado = int(minutos / 5 + 0.5) * 5
    if arredondado < 5:
        arredondado = 5
    return arredondado


# função que escreve a frase da previsão que aparece na tela
# quando_entregou é o texto de quando entregou (ex: "hoje às 19:40"), ou "" se ainda não entregou
def frase_da_previsao(status, minutos_previstos, quando_entregou):
    if status == "ENTREGUE":
        if quando_entregou != "":
            return "Entregue " + quando_entregou + "."
        return "Entregue."

    minutos = estimar_minutos(status, minutos_previstos)
    if minutos == 0:
        return ""
    return "Previsão de entrega: cerca de " + str(minutos) + " min."