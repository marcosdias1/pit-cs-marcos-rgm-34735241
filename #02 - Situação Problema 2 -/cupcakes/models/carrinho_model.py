from decimal import Decimal
from models.conexao import pegar_conexao

# aqui fica tudo que mexe no carrinho de compras no banco de dados


# função que deixa um valor em dinheiro no formato brasileiro
# ex: 1234.5 vira "R$ 1.234,50"
def formatar_dinheiro(valor):
    # o {:,.2f} usa virgula nos milhares e ponto nos centavos (formato americano)
    texto = "{:,.2f}".format(valor)
    # troca as duas usando um X no meio (senão uma troca desfaz a outra)
    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")
    return "R$ " + texto


# função que soma o valor dos itens (preço x quantidade)
def calcular_subtotal(itens):
    total = Decimal("0.00")
    for item in itens:
        total = total + item["preco_unitario"] * item["quantidade"]
    return total


# função que acha o carrinho da pessoa, ou cria um se ainda não tiver
# cliente logado usa o id_cliente, visitante usa o id_sessao (um código guardado na sessão)
def pegar_ou_criar_carrinho(id_cliente, id_sessao):
    con = pegar_conexao()
    cur = con.cursor()
    id_carrinho = None

    if id_cliente is not None:
        cur.execute("SELECT id_carrinho FROM carrinho WHERE id_cliente = %s", (id_cliente,))
    else:
        cur.execute("SELECT id_carrinho FROM carrinho WHERE id_sessao = %s AND id_cliente IS NULL", (id_sessao,))
    linha = cur.fetchone()

    if linha is not None:
        id_carrinho = linha[0]
    else:
        # não tem ainda, então cria
        try:
            if id_cliente is not None:
                cur.execute("INSERT INTO carrinho (id_cliente) VALUES (%s) RETURNING id_carrinho", (id_cliente,))
            else:
                cur.execute("INSERT INTO carrinho (id_sessao) VALUES (%s) RETURNING id_carrinho", (id_sessao,))
            id_carrinho = cur.fetchone()[0]
            con.commit()
        except Exception as e:
            con.rollback()
            cur.close()
            con.close()
            raise e

    cur.close()
    con.close()
    return id_carrinho

# função que conta quantas unidades tem no carrinho (é o número do ícone do carrinho no topo)
# não cria carrinho: se a pessoa nunca adicionou nada, devolve 0
def contar_itens(id_cliente, id_sessao):
    if id_cliente is None and id_sessao is None:
        return 0

    con = pegar_conexao()
    cur = con.cursor()

    if id_cliente is not None:
        sql = """SELECT COALESCE(SUM(i.quantidade), 0)
                 FROM item_carrinho i JOIN carrinho c ON c.id_carrinho = i.id_carrinho
                 WHERE c.id_cliente = %s"""
        cur.execute(sql, (id_cliente,))
    else:
        sql = """SELECT COALESCE(SUM(i.quantidade), 0)
                 FROM item_carrinho i JOIN carrinho c ON c.id_carrinho = i.id_carrinho
                 WHERE c.id_sessao = %s AND c.id_cliente IS NULL"""
        cur.execute(sql, (id_sessao,))

    total = cur.fetchone()[0]
    cur.close()
    con.close()
    return int(total)


# função que lista os itens do carrinho com o preço da tabela ativa (cartões 05, 06 e 07)
def listar_itens(id_carrinho):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT p.id_produto, p.nome, p.tipo, p.estoque, p.ativo, pp.valor, i.quantidade
        FROM item_carrinho i
        JOIN produto p ON p.id_produto = i.id_produto
        JOIN preco_produto pp ON pp.id_produto = p.id_produto
        JOIN tabela_preco tp ON tp.id_tabela_preco = pp.id_tabela_preco AND tp.ativa = TRUE
        WHERE i.id_carrinho = %s
        ORDER BY CASE WHEN p.tipo = 'CUPCAKE' THEN 0 ELSE 1 END, p.nome
    """
    cur.execute(sql, (id_carrinho,))
    res = cur.fetchall()

    lista = []
    for x in res:
        item = {}
        item["id"] = x[0]
        item["nome"] = x[1]
        item["tipo"] = x[2]
        item["estoque"] = x[3]
        # disponível quer dizer: está ativo e tem estoque
        item["disponivel"] = (x[4] == True and x[3] > 0)
        item["preco_unitario"] = x[5]
        item["quantidade"] = x[6]
        item["preco_texto"] = formatar_dinheiro(x[5])
        item["subtotal_texto"] = formatar_dinheiro(x[5] * x[6])
        lista.append(item)

    cur.close()
    con.close()
    return lista


# função que lista os adicionais pra sugerir na tela do carrinho (cartão 06)
def listar_adicionais(id_carrinho):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT p.id_produto, p.nome, a.tipo_adicional, pp.valor
        FROM produto p
        JOIN adicional a ON a.id_adicional = p.id_produto
        JOIN preco_produto pp ON pp.id_produto = p.id_produto
        JOIN tabela_preco tp ON tp.id_tabela_preco = pp.id_tabela_preco AND tp.ativa = TRUE
        WHERE p.ativo = TRUE AND p.estoque > 0
          AND p.id_produto NOT IN (SELECT id_produto FROM item_carrinho WHERE id_carrinho = %s)
        ORDER BY a.tipo_adicional, p.nome
    """
    cur.execute(sql, (id_carrinho,))
    res = cur.fetchall()

    lista = []
    for x in res:
        adicional = {}
        adicional["id"] = x[0]
        adicional["nome"] = x[1]
        adicional["tipo"] = x[2]
        adicional["preco_texto"] = formatar_dinheiro(x[3])
        lista.append(adicional)

    cur.close()
    con.close()
    return lista


# função que coloca um produto no carrinho (cartão 05)
# devolve "" se deu certo, ou o texto do erro pra mostrar pra pessoa
def adicionar_item(id_carrinho, id_produto, quantidade):
    mensagem = ""
    con = pegar_conexao()
    cur = con.cursor()

    try:
        # confere se o produto existe, está à venda e tem preço na tabela ativa
        sql = """
            SELECT p.estoque
            FROM produto p
            JOIN preco_produto pp ON pp.id_produto = p.id_produto
            JOIN tabela_preco tp ON tp.id_tabela_preco = pp.id_tabela_preco AND tp.ativa = TRUE
            WHERE p.id_produto = %s AND p.ativo = TRUE
        """
        cur.execute(sql, (id_produto,))
        linha = cur.fetchone()

        if linha is None:
            mensagem = "Esse produto não está disponível no momento."
        else:
            estoque = linha[0]

            # vê quantas unidades dele já estão no carrinho
            cur.execute("SELECT quantidade FROM item_carrinho WHERE id_carrinho = %s AND id_produto = %s",
                        (id_carrinho, id_produto))
            linha = cur.fetchone()
            ja_tem = 0
            if linha is not None:
                ja_tem = linha[0]

            # regra do cartão 05: não pode pedir mais do que tem no estoque
            if estoque <= 0:
                mensagem = "Esse produto está sem estoque no momento."
            elif ja_tem + quantidade > estoque:
                mensagem = "Só temos " + str(estoque) + " em estoque (você já tem " + str(ja_tem) + " no carrinho)."
            else:
                if ja_tem == 0:
                    cur.execute("INSERT INTO item_carrinho (id_carrinho, id_produto, quantidade) VALUES (%s, %s, %s)",
                                (id_carrinho, id_produto, quantidade))
                else:
                    cur.execute("UPDATE item_carrinho SET quantidade = %s WHERE id_carrinho = %s AND id_produto = %s",
                                (ja_tem + quantidade, id_carrinho, id_produto))
                cur.execute("UPDATE carrinho SET atualizado_em = CURRENT_TIMESTAMP WHERE id_carrinho = %s",
                            (id_carrinho,))
                con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return mensagem


# função que aumenta ou diminui a quantidade de um item (cartão 07)
# devolve "" se deu certo, ou o texto do erro
def alterar_quantidade(id_carrinho, id_produto, mudanca):
    mensagem = ""
    con = pegar_conexao()
    cur = con.cursor()

    try:
        sql = """
            SELECT i.quantidade, p.estoque
            FROM item_carrinho i
            JOIN produto p ON p.id_produto = i.id_produto
            WHERE i.id_carrinho = %s AND i.id_produto = %s
        """
        cur.execute(sql, (id_carrinho, id_produto))
        linha = cur.fetchone()

        if linha is None:
            mensagem = "Esse item não está mais no carrinho."
        else:
            quantidade_atual = linha[0]
            estoque = linha[1]
            nova = quantidade_atual + mudanca

            if nova <= 0:
                # regra do cartão 07: chegou a zero, tira o item do carrinho
                cur.execute("DELETE FROM item_carrinho WHERE id_carrinho = %s AND id_produto = %s",
                            (id_carrinho, id_produto))
                con.commit()
            elif mudanca > 0 and nova > estoque:
                # só confere o estoque quando está aumentando
                mensagem = "Só temos " + str(estoque) + " em estoque."
            else:
                cur.execute("UPDATE item_carrinho SET quantidade = %s WHERE id_carrinho = %s AND id_produto = %s",
                            (nova, id_carrinho, id_produto))
                cur.execute("UPDATE carrinho SET atualizado_em = CURRENT_TIMESTAMP WHERE id_carrinho = %s",
                            (id_carrinho,))
                con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return mensagem


# função que tira um item do carrinho (a lixeira do cartão 07)
def remover_item(id_carrinho, id_produto):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        cur.execute("DELETE FROM item_carrinho WHERE id_carrinho = %s AND id_produto = %s",
                    (id_carrinho, id_produto))
        cur.execute("UPDATE carrinho SET atualizado_em = CURRENT_TIMESTAMP WHERE id_carrinho = %s",
                    (id_carrinho,))
        con.commit()
    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return ""

# função que confere se o carrinho está pronto pra fechar o pedido (etapa 5)
# devolve "" se está tudo certo, ou o texto do problema
def conferir_carrinho(itens):
    if len(itens) == 0:
        return "Seu carrinho está vazio."
    tem_cupcake = False
    for item in itens:
        if item["tipo"] == "CUPCAKE":
            tem_cupcake = True
        if item["disponivel"] == False:
            return "O item " + item["nome"] + " está sem estoque. Tire ele do carrinho para continuar."
        if item["quantidade"] > item["estoque"]:
            return "Só temos " + str(item["estoque"]) + " de " + item["nome"] + " em estoque. Diminua a quantidade no carrinho."

    # adicional sozinho não vale (precisa de pelo menos um cupcake)
    if tem_cupcake == False:
        return "Escolha pelo menos um cupcake para fechar o pedido."

    return ""


# função que calcula o total do pedido: subtotal + frete - desconto
def calcular_total(subtotal, valor_frete, desconto):
    return subtotal + valor_frete - desconto

# função que passa o carrinho do visitante pra conta de quem acabou de entrar ou criar conta
# se o mesmo produto já estava no carrinho da conta, soma as quantidades
def juntar_carrinho_do_visitante(id_sessao, id_cliente):
    movidos = 0
    con = pegar_conexao()
    cur = con.cursor()

    try:
        # acha o carrinho do visitante
        cur.execute("SELECT id_carrinho FROM carrinho WHERE id_sessao = %s AND id_cliente IS NULL", (id_sessao,))
        linha = cur.fetchone()

        if linha is not None:
            id_do_visitante = linha[0]

            # acha o carrinho da conta (ou cria, se ainda não tem)
            cur.execute("SELECT id_carrinho FROM carrinho WHERE id_cliente = %s", (id_cliente,))
            linha = cur.fetchone()
            if linha is None:
                cur.execute("INSERT INTO carrinho (id_cliente) VALUES (%s) RETURNING id_carrinho", (id_cliente,))
                linha = cur.fetchone()
            id_da_conta = linha[0]

            # passa os itens (se o produto já está no carrinho da conta, soma as quantidades)
            sql = """
                INSERT INTO item_carrinho (id_carrinho, id_produto, quantidade)
                SELECT %s, id_produto, quantidade FROM item_carrinho WHERE id_carrinho = %s
                ON CONFLICT (id_carrinho, id_produto)
                DO UPDATE SET quantidade = item_carrinho.quantidade + EXCLUDED.quantidade
            """
            cur.execute(sql, (id_da_conta, id_do_visitante))
            movidos = cur.rowcount

            # apaga o carrinho do visitante (os itens dele somem junto, por causa do ON DELETE CASCADE)
            cur.execute("DELETE FROM carrinho WHERE id_carrinho = %s", (id_do_visitante,))
            cur.execute("UPDATE carrinho SET atualizado_em = CURRENT_TIMESTAMP WHERE id_carrinho = %s",
                        (id_da_conta,))

        con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return movidos