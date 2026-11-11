# aqui fica o que mexe no banco para o histórico de compras e a recompra (cartão 15)

from models import carrinho_model
from models import historico_regras
from models.conexao import pegar_conexao


# função que lista os pedidos de um cliente, do mais novo pro mais antigo
# não mostra o pedido que ficou esperando pagamento (a pessoa nunca terminou a compra)
# devolve uma lista de dicionários já com os textos prontos pra tela
def listar_pedidos_do_cliente(id_cliente, limite):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT id_pedido, numero, status, total, data_hora
        FROM pedido
        WHERE id_cliente = %s AND status <> 'AGUARDANDO_PAGAMENTO'
        ORDER BY data_hora DESC, id_pedido DESC
        LIMIT %s
    """
    cur.execute(sql, (id_cliente, limite))
    res = cur.fetchall()

    lista = []
    ids = []
    for x in res:
        pedido = {}
        pedido["id"] = x[0]
        pedido["numero"] = x[1]
        pedido["status"] = x[2]
        pedido["status_texto"] = historico_regras.texto_do_status(x[2])
        pedido["total_texto"] = carrinho_model.formatar_dinheiro(x[3])
        pedido["data_texto"] = historico_regras.formatar_data(x[4])
        pedido["pode_acompanhar"] = historico_regras.pode_acompanhar(x[2])
        pedido["itens"] = []
        lista.append(pedido)
        ids.append(x[0])

    # busca os itens de todos os pedidos de uma vez só (uma consulta só, em vez de uma por pedido)
    if len(ids) > 0:
        sql = """
            SELECT i.id_pedido, p.nome, i.quantidade
            FROM item_pedido i
            JOIN produto p ON p.id_produto = i.id_produto
            WHERE i.id_pedido = ANY(%s)
            ORDER BY CASE WHEN p.tipo = 'CUPCAKE' THEN 0 ELSE 1 END, p.nome
        """
        cur.execute(sql, (ids,))
        itens = cur.fetchall()

        for linha in itens:
            for pedido in lista:
                if pedido["id"] == linha[0]:
                    pedido["itens"].append({"nome": linha[1], "quantidade": linha[2]})

    for pedido in lista:
        pedido["itens_texto"] = historico_regras.resumir_itens(pedido["itens"])

    cur.close()
    con.close()
    return lista


# função que lista os itens de um pedido com o código do produto (pra colocar tudo no carrinho de novo)
def listar_itens_para_recompra(id_pedido):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT i.id_produto, p.nome, i.quantidade
        FROM item_pedido i
        JOIN produto p ON p.id_produto = i.id_produto
        WHERE i.id_pedido = %s
        ORDER BY CASE WHEN p.tipo = 'CUPCAKE' THEN 0 ELSE 1 END, p.nome
    """
    cur.execute(sql, (id_pedido,))
    res = cur.fetchall()

    lista = []
    for x in res:
        item = {}
        item["id_produto"] = x[0]
        item["nome"] = x[1]
        item["quantidade"] = x[2]
        lista.append(item)

    cur.close()
    con.close()
    return lista