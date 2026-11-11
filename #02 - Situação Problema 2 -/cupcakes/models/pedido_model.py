from decimal import Decimal
from models import cupom_regras
from models import carrinho_model
from models import acompanhamento
from models.conexao import pegar_conexao

# model do pedido
# nesta etapa só tem as buscas da tela de fechar pedido


# colunas do cupom (uso nas duas buscas de cupom, é um texto fixo meu, não vem de ninguém)
COLUNAS_DO_CUPOM = "id_cupom, id_cliente, codigo, tipo, valor, valido_de, valido_ate, uso_unico, primeira_compra, ativo"


# função que monta o dicionário do cupom a partir de uma linha que veio do banco
def montar_cupom(linha):
    cupom = {}
    cupom["id"] = linha[0]
    cupom["id_cliente"] = linha[1]
    cupom["codigo"] = linha[2]
    cupom["tipo"] = linha[3]
    cupom["valor"] = linha[4]
    cupom["valido_de"] = linha[5]
    cupom["valido_ate"] = linha[6]
    cupom["uso_unico"] = linha[7]
    cupom["primeira_compra"] = linha[8]
    cupom["ativo"] = linha[9]
    return cupom


# função que busca o endereço principal do cliente (cartão 20: já vem preenchido no fechamento)
# devolve um dicionário ou None se ele não tem endereço
def buscar_endereco_principal(id_cliente):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT cep, rua, numero, bairro, cidade, uf
        FROM endereco
        WHERE id_cliente = %s AND principal = TRUE AND ativo = TRUE
    """
    cur.execute(sql, (id_cliente,))
    linha = cur.fetchone()

    cur.close()
    con.close()

    if linha is None:
        return None

    endereco = {}
    # o cep está no banco só com números, aqui eu ponho o traço (00000-000)
    endereco["cep"] = linha[0][0:5] + "-" + linha[0][5:8]
    endereco["rua"] = linha[1]
    endereco["numero"] = linha[2]
    endereco["bairro"] = linha[3]
    endereco["cidade"] = linha[4]
    endereco["uf"] = linha[5]
    return endereco


# função que busca nome, e-mail e celular do cliente (o contato da entrega)
def buscar_contato_do_cliente(id_cliente):
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT nome, email, celular FROM pessoa WHERE id_pessoa = %s", (id_cliente,))
    linha = cur.fetchone()
    cur.close()
    con.close()

    if linha is None:
        return None

    contato = {}
    contato["nome"] = linha[0]
    contato["email"] = linha[1]
    contato["celular"] = linha[2]
    return contato


# função que procura um cupom pelo código (sem ligar pra maiúscula)
def buscar_cupom_por_codigo(codigo):
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT " + COLUNAS_DO_CUPOM + " FROM cupom WHERE upper(codigo) = upper(%s)", (codigo,))
    linha = cur.fetchone()
    cur.close()
    con.close()

    if linha is None:
        return None
    return montar_cupom(linha)


# função que lista os cupons ligados ao cliente (o "desconto atrelado ao cpf" do cartão 09)
def listar_cupons_do_cliente(id_cliente):
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT " + COLUNAS_DO_CUPOM + " FROM cupom WHERE id_cliente = %s AND ativo = TRUE", (id_cliente,))
    res = cur.fetchall()
    cur.close()
    con.close()

    lista = []
    for linha in res:
        lista.append(montar_cupom(linha))
    return lista


# função que conta quantas vezes o cliente usou o cupom em pedidos já confirmados
# (pedido esperando pagamento ou cancelado não conta)
def contar_usos_do_cupom(id_cupom, id_cliente):
    con = pegar_conexao()
    cur = con.cursor()
    sql = """
        SELECT COUNT(*) FROM pedido
        WHERE id_cupom = %s AND id_cliente = %s
          AND status NOT IN ('AGUARDANDO_PAGAMENTO', 'CANCELADO')
    """
    cur.execute(sql, (id_cupom, id_cliente))
    total = cur.fetchone()[0]
    cur.close()
    con.close()
    return int(total)


# função que confere se o cliente já tem algum pedido confirmado (pro cupom de primeira compra)
def cliente_ja_comprou(id_cliente):
    con = pegar_conexao()
    cur = con.cursor()
    sql = """
        SELECT COUNT(*) FROM pedido
        WHERE id_cliente = %s AND status NOT IN ('AGUARDANDO_PAGAMENTO', 'CANCELADO')
    """
    cur.execute(sql, (id_cliente,))
    total = cur.fetchone()[0]
    cur.close()
    con.close()
    if total > 0:
        return True
    else:
        return False


# função que escolhe o cupom do pedido (cartão 09)
# devolve (cupom, mensagem):
#   se a pessoa digitou um código: confere ele, e a mensagem diz o motivo se não pode usar
#   se não digitou nada: procura sozinho o melhor cupom ligado ao cpf dela (cliente logado)
def escolher_cupom(id_cliente, codigo, subtotal, hoje):
    # digitou um código 
    if codigo != "":
        cupom = buscar_cupom_por_codigo(codigo)
        if cupom is None:
            return (None, "Cupom não encontrado.")

        ja_usado = False
        ja_comprou = False
        if id_cliente is not None:
            ja_usado = (contar_usos_do_cupom(cupom["id"], id_cliente) > 0)
            ja_comprou = cliente_ja_comprou(id_cliente)

        mensagem = cupom_regras.validar_cupom(cupom, hoje, id_cliente, ja_usado, ja_comprou)
        if mensagem != "":
            return (None, mensagem)
        return (cupom, "")

    # não digitou: visitante não tem cupom automático 
    if id_cliente is None:
        return (None, "")

    # não digitou: procura o melhor cupom do cpf 
    ja_comprou = cliente_ja_comprou(id_cliente)
    melhor = None
    maior_desconto = Decimal("0.00")

    for cupom in listar_cupons_do_cliente(id_cliente):
        ja_usado = (contar_usos_do_cupom(cupom["id"], id_cliente) > 0)
        mensagem = cupom_regras.validar_cupom(cupom, hoje, id_cliente, ja_usado, ja_comprou)
        if mensagem == "":
            desconto = cupom_regras.calcular_desconto(cupom, subtotal)
            if desconto > maior_desconto:
                melhor = cupom
                maior_desconto = desconto

    return (melhor, "")



# função que cria o pedido no banco com o status AGUARDANDO_PAGAMENTO (cartão 11)
# grava o endereço, o pedido, os itens e o histórico, tudo junto (se der erro em alguma parte, desfaz tudo)
#   contato: dicionário com nome, email e celular
#   endereco: dicionário com cep (só números), rua, numero, bairro, cidade e uf
#   itens: a lista do carrinho (com id, preco_unitario e quantidade)
#   id_pedido_antigo: pedido que a pessoa já tinha criado e não pagou (é cancelado pra não ficar repetido)
# devolve um dicionário com o id e o número do pedido
def criar_pedido(id_cliente, contato, endereco, itens, subtotal, frete_info, desconto, total, id_cupom, id_pedido_antigo):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        # 0) se a pessoa já tinha um pedido esperando pagamento, cancela ele (só se for dela)
        if id_pedido_antigo is not None:
            cur.execute("""UPDATE pedido SET status = 'CANCELADO'
                           WHERE id_pedido = %s AND status = 'AGUARDANDO_PAGAMENTO'
                             AND id_cliente IS NOT DISTINCT FROM %s""", (id_pedido_antigo, id_cliente))
            if cur.rowcount == 1:
                cur.execute("INSERT INTO historico_status (id_pedido, id_pessoa, status) VALUES (%s, %s, 'CANCELADO')",
                            (id_pedido_antigo, id_cliente))

        # 1) endereço: se o cliente já tem um igual, usa ele, senão grava um novo
        id_endereco = None
        if id_cliente is not None:
            sql = """SELECT id_endereco FROM endereco
                     WHERE id_cliente = %s AND ativo = TRUE AND cep = %s AND rua = %s
                       AND numero = %s AND bairro = %s AND cidade = %s AND uf = %s
                     LIMIT 1"""
            cur.execute(sql, (id_cliente, endereco["cep"], endereco["rua"], endereco["numero"],
                              endereco["bairro"], endereco["cidade"], endereco["uf"]))
            linha = cur.fetchone()
            if linha is not None:
                id_endereco = linha[0]

        if id_endereco is None:
            cur.execute("""INSERT INTO endereco (id_cliente, cep, rua, numero, bairro, cidade, uf, principal)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE) RETURNING id_endereco""",
                        (id_cliente, endereco["cep"], endereco["rua"], endereco["numero"],
                         endereco["bairro"], endereco["cidade"], endereco["uf"]))
            id_endereco = cur.fetchone()[0]

        # 2) o pedido (a previsão de entrega é agora + os minutos do frete)
        sql = """INSERT INTO pedido (id_cliente, id_endereco, id_cupom, status, subtotal, valor_frete, desconto, total,
                                     previsao_entrega, nome_contato, email_contato, telefone_contato)
                 VALUES (%s, %s, %s, 'AGUARDANDO_PAGAMENTO', %s, %s, %s, %s,
                         CURRENT_TIMESTAMP + (%s * INTERVAL '1 minute'), %s, %s, %s)
                 RETURNING id_pedido, numero"""
        cur.execute(sql, (id_cliente, id_endereco, id_cupom, subtotal, frete_info["valor"], desconto, total,
                          frete_info["minutos"], contato["nome"], contato["email"], contato["celular"]))
        linha = cur.fetchone()
        id_pedido = linha[0]
        numero = linha[1]

        # 3) os itens (o preço fica gravado no pedido, assim ele não muda se a tabela de preços mudar)
        for item in itens:
            cur.execute("""INSERT INTO item_pedido (id_pedido, id_produto, quantidade, preco_unitario)
                           VALUES (%s, %s, %s, %s)""",
                        (id_pedido, item["id"], item["quantidade"], item["preco_unitario"]))

        # 4) histórico de status
        cur.execute("INSERT INTO historico_status (id_pedido, id_pessoa, status) VALUES (%s, %s, 'AGUARDANDO_PAGAMENTO')",
                    (id_pedido, id_cliente))

        con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return {"id": id_pedido, "numero": numero}


# função que busca um pedido pelo número
# devolve um dicionário ou None se não achar
def buscar_pedido_por_numero(numero):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT id_pedido, numero, id_cliente, status, subtotal, valor_frete, desconto, total,
               data_hora, previsao_entrega, nome_contato, email_contato, id_cupom
        FROM pedido
        WHERE numero = %s
    """
    cur.execute(sql, (numero,))
    linha = cur.fetchone()

    if linha is None:
        cur.close()
        con.close()
        return None

    pedido = {}
    pedido["id"] = linha[0]
    pedido["numero"] = linha[1]
    pedido["id_cliente"] = linha[2]
    pedido["status"] = linha[3]
    pedido["subtotal"] = linha[4]
    pedido["frete"] = linha[5]
    pedido["desconto"] = linha[6]
    pedido["total"] = linha[7]
    pedido["data_hora"] = linha[8]
    pedido["previsao_entrega"] = linha[9]
    pedido["nome_contato"] = linha[10]
    pedido["email_contato"] = linha[11]
    pedido["id_cupom"] = linha[12]

    # os valores já formatados pra tela
    pedido["subtotal_texto"] = carrinho_model.formatar_dinheiro(linha[4])
    pedido["frete_texto"] = carrinho_model.formatar_dinheiro(linha[5])
    pedido["desconto_texto"] = carrinho_model.formatar_dinheiro(linha[6])
    pedido["total_texto"] = carrinho_model.formatar_dinheiro(linha[7])
    pedido["tem_desconto"] = (linha[6] > 0)

    # a forma de pagamento aprovada (só tem se o pedido já foi pago)
    cur.execute("""SELECT forma FROM pagamento
                   WHERE id_pedido = %s AND status = 'APROVADO'
                   ORDER BY data_hora DESC LIMIT 1""", (pedido["id"],))
    linha = cur.fetchone()
    pedido["forma"] = ""
    if linha is not None:
        pedido["forma"] = linha[0]

    cur.close()
    con.close()
    return pedido


# função que lista os itens de um pedido (pra tela de pedido confirmado)
def listar_itens_do_pedido(id_pedido):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT p.nome, i.quantidade, i.preco_unitario
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
        item["nome"] = x[0]
        item["quantidade"] = x[1]
        item["subtotal_texto"] = carrinho_model.formatar_dinheiro(x[2] * x[1])
        lista.append(item)

    cur.close()
    con.close()
    return lista


# função que confere de novo se o cupom do pedido ainda vale (ele pode ter vencido, ou ter sido usado em outro pedido)
# devolve "" se vale (ou se o pedido não tem cupom), ou o texto do motivo
def conferir_cupom_do_pedido(pedido, hoje):
    if pedido["id_cupom"] is None:
        return ""

    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT codigo FROM cupom WHERE id_cupom = %s", (pedido["id_cupom"],))
    linha = cur.fetchone()
    cur.close()
    con.close()

    if linha is None:
        return "O cupom do pedido não existe mais."

    resposta = escolher_cupom(pedido["id_cliente"], linha[0], pedido["subtotal"], hoje)
    return resposta[1]


# função que guarda uma tentativa de pagamento que foi RECUSADA
# (o pedido continua esperando pagamento, a pessoa pode tentar de novo)
def registrar_pagamento_recusado(id_pedido, forma, valor, codigo):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        cur.execute("""INSERT INTO pagamento (id_pedido, forma, valor, status, codigo_transacao)
                       VALUES (%s, %s, %s, 'RECUSADO', %s)""", (id_pedido, forma, valor, codigo))
        con.commit()
    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()

# função que confirma o pedido depois que o pagamento foi aprovado (cartão 11)
# 1) baixa o estoque (só se ainda tem), 2) grava o pagamento, 3) muda o pedido pra CONFIRMADO,
# 4) grava no histórico e 5) tira do carrinho o que foi pro pedido
# tudo junto: se qualquer parte falhar, desfaz tudo
# devolve "" se deu certo, ou o texto do problema
def confirmar_pagamento(id_pedido, id_carrinho, forma, valor, codigo, id_cliente):
    mensagem = ""
    con = pegar_conexao()
    cur = con.cursor()

    try:
        # trava o pedido pra ninguém pagar duas vezes ao mesmo tempo
        cur.execute("SELECT status FROM pedido WHERE id_pedido = %s FOR UPDATE", (id_pedido,))
        linha = cur.fetchone()

        if linha is None or linha[0] != "AGUARDANDO_PAGAMENTO":
            mensagem = "Esse pedido já foi pago ou cancelado."
        else:
            # baixa o estoque de cada item (o UPDATE só mexe se ainda tem estoque suficiente)
            cur.execute("SELECT id_produto, quantidade FROM item_pedido WHERE id_pedido = %s", (id_pedido,))
            itens = cur.fetchall()

            faltou_estoque = False
            for item in itens:
                cur.execute("""UPDATE produto SET estoque = estoque - %s
                               WHERE id_produto = %s AND ativo = TRUE AND estoque >= %s""",
                            (item[1], item[0], item[1]))
                if cur.rowcount != 1:
                    faltou_estoque = True

            if faltou_estoque == True:
                # desfaz as baixas que já tinham sido feitas
                con.rollback()
                mensagem = "Um dos itens acabou no estoque agora há pouco. Nada foi cobrado. Volte ao carrinho e ajuste o pedido."
            else:
                cur.execute("""INSERT INTO pagamento (id_pedido, forma, valor, status, codigo_transacao)
                               VALUES (%s, %s, %s, 'APROVADO', %s)""", (id_pedido, forma, valor, codigo))

                # confirma o pedido (a previsão passa a contar a partir de agora, com a mesma duração de antes)
                cur.execute("""UPDATE pedido
                               SET status = 'CONFIRMADO',
                                   previsao_entrega = CURRENT_TIMESTAMP + (previsao_entrega - data_hora)
                               WHERE id_pedido = %s""", (id_pedido,))

                cur.execute("INSERT INTO historico_status (id_pedido, id_pessoa, status) VALUES (%s, %s, 'CONFIRMADO')",
                            (id_pedido, id_cliente))

                # tira do carrinho os produtos que foram pro pedido
                cur.execute("""DELETE FROM item_carrinho
                               WHERE id_carrinho = %s
                                 AND id_produto IN (SELECT id_produto FROM item_pedido WHERE id_pedido = %s)""",
                            (id_carrinho, id_pedido))

                con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return mensagem


# função que escreve a previsão de entrega de um jeito fácil de ler (ex: "hoje às 19:40" ou "04/11 às 09:15")
def formatar_previsao(previsao, agora):
    if previsao is None:
        return ""

    hora = previsao.strftime("%H:%M")
    if previsao.date() == agora.date():
        return "hoje às " + hora
    return previsao.strftime("%d/%m") + " às " + hora


# e-mail do entregador de mentira (ele só existe na simulação do acompanhamento)
EMAIL_DO_ENTREGADOR_SIMULADO = "entregador.simulado@exemplo.com"

# função que acha o entregador de mentira, ou cria ele se ainda não existir (o banco exige um entregador quando o pedido está "Saiu para entrega" ou "Entregue")
# o cur é o cursor da transação que já está aberta, quem chama é que fecha
def garantir_entregador_simulado(cur):
    sql = """
        SELECT e.id_entregador
        FROM entregador e
        JOIN pessoa p ON p.id_pessoa = e.id_entregador
        WHERE p.email = %s
    """
    cur.execute(sql, (EMAIL_DO_ENTREGADOR_SIMULADO,))
    linha = cur.fetchone()
    if linha is not None:
        return linha[0]

    # não existe ainda: cria a pessoa e depois o entregador
    cur.execute("""INSERT INTO pessoa (nome, email, celular)
                   VALUES ('Entregador (simulado)', %s, '11900000000') RETURNING id_pessoa""",
                (EMAIL_DO_ENTREGADOR_SIMULADO,))
    id_novo = cur.fetchone()[0]
    cur.execute("INSERT INTO entregador (id_entregador, placa) VALUES (%s, 'SIM0A00')", (id_novo,))
    return id_novo

# função que faz o pedido andar sozinho pelas etapas, conforme o tempo desde a confirmação (cartão 12)
# SIMULAÇÃO: sem funcionário e sem entregador, é o próprio sistema que muda o status
# cada etapa é gravada no histórico com o horário em que ela teria começado
def atualizar_status_simulado(id_pedido):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        # trava o pedido (pra duas telas abertas não gravarem a mesma etapa duas vezes)
        # e já pergunta pro banco quantos segundos passaram desde a confirmação
        sql = """
            SELECT p.status, h.data_hora, EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - h.data_hora))
            FROM pedido p
            JOIN historico_status h ON h.id_pedido = p.id_pedido AND h.status = 'CONFIRMADO'
            WHERE p.id_pedido = %s
            ORDER BY h.data_hora
            LIMIT 1
            FOR UPDATE OF p
        """
        cur.execute(sql, (id_pedido,))
        linha = cur.fetchone()

        if linha is not None:
            status_atual = linha[0]
            confirmado_em = linha[1]
            segundos = int(linha[2])

            posicao_atual = acompanhamento.posicao_da_etapa(status_atual)
            esperado = acompanhamento.status_esperado(segundos)
            posicao_esperada = acompanhamento.posicao_da_etapa(esperado)

            # só anda com pedido que está nas etapas (os cancelados e os que esperam pagamento ficam como estão)
            if posicao_atual >= 0 and posicao_esperada > posicao_atual:
                id_entregador = None

                # passa por cada etapa que faltava (se a pessoa ficou um tempão sem abrir, passa por várias)
                for i in range(posicao_atual + 1, posicao_esperada + 1):
                    nova = acompanhamento.ETAPAS[i]

                    if nova == "SAIU_PARA_ENTREGA":
                        id_entregador = garantir_entregador_simulado(cur)
                        cur.execute("UPDATE pedido SET status = %s, id_entregador = %s WHERE id_pedido = %s",
                                    (nova, id_entregador, id_pedido))
                    else:
                        cur.execute("UPDATE pedido SET status = %s WHERE id_pedido = %s", (nova, id_pedido))

                    # grava no histórico com o horário em que a etapa teria começado
                    cur.execute("""INSERT INTO historico_status (id_pedido, status, data_hora)
                                   VALUES (%s, %s, %s + (%s * INTERVAL '1 second'))""",
                                (id_pedido, nova, confirmado_em, acompanhamento.SEGUNDOS_DE_CADA_ETAPA[nova]))

        con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()


# função que lista o históric de status do pedido (do mais antigo pro mais novo)
def listar_historico_do_pedido(id_pedido):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT status, data_hora
        FROM historico_status
        WHERE id_pedido = %s
        ORDER BY data_hora, id_historico_status
    """
    cur.execute(sql, (id_pedido,))
    res = cur.fetchall()

    lista = []
    for x in res:
        registro = {}
        registro["status"] = x[0]
        registro["data_hora"] = x[1]
        lista.append(registro)

    cur.close()
    con.close()
    return lista