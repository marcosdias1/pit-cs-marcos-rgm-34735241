# regras do cancelamento de pedido (melhoria pedida nos testes: "fiz um pedido errado e quis cancelar")
# aqui só tem regra e texto: nada de banco de dados (assim dá pra testar sem o PostgreSQL)
# REGRA QUE EU ESCOLHI: dá pra cancelar até o pedido sair para entrega (depois disso o motoboy já está na rua)

# os status em que ainda dá pra cancelar
STATUS_QUE_PODEM_CANCELAR = ["CONFIRMADO", "EM_PREPARO"]

# o motivo de cada status que NÃO pode cancelar
MOTIVOS = {
    "AGUARDANDO_PAGAMENTO": "Esse pedido ainda não foi pago, então não tem o que cancelar.",
    "SAIU_PARA_ENTREGA": "O pedido já saiu para entrega e não pode mais ser cancelado.",
    "ENTREGUE": "O pedido já foi entregue e não pode ser cancelado.",
    "CANCELADO": "Esse pedido já foi cancelado.",
}


# função que diz se o pedido ainda pode ser cancelado
def pode_cancelar(status):
    return status in STATUS_QUE_PODEM_CANCELAR


# função que devolve o motivo de não poder cancelar (se o status não está na lista, devolve um texto genérico)
def motivo_de_nao_poder(status):
    if status in MOTIVOS:
        return MOTIVOS[status]
    return "Esse pedido não pode ser cancelado."


# função que escreve a mensagem que aparece depois de cancelar
# o pagamento aqui é de mentira (simulado), então eu aviso que nada foi cobrado de verdade
def mensagem_de_cancelado(numero):
    return ("Pedido #" + str(numero) + " cancelado. Os itens voltaram para o estoque. "
            "Como o pagamento é de demonstração, nenhum valor foi cobrado de verdade.")
