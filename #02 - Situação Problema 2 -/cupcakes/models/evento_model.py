# aqui fica o que mexe no banco para o orçamento de evento (cartão 08)

from models import evento_regras
from models import historico_regras
from models.conexao import pegar_conexao


# função que guarda o pedido de orçamento e devolve o número dele (o protocolo)
# campos: nome, email, celular, data_evento, quantidade, tema e observacoes (tema e observacoes podem ser None)
# id_cliente é None quando quem pediu é visitante
def criar_solicitacao(id_cliente, campos):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        sql = """
            INSERT INTO solicitacao_evento (id_cliente, nome_contato, email_contato, telefone_contato, data_evento, quantidade, tema, observacoes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_solicitacao_evento
        """
        cur.execute(sql, (id_cliente, campos["nome"], campos["email"], campos["celular"],
                          campos["data_evento"], campos["quantidade"], campos["tema"], campos["observacoes"]))
        numero = cur.fetchone()[0]
        con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return numero


# função que lista as encomendas (orçamentos de evento) de um cliente que tem conta, da mais nova pra mais antiga
# (orçamento de visitante não entra: ele não tem conta pra ver a lista)
# devolve uma lista de dicionários já com os textos prontos pra tela
def listar_solicitacoes_do_cliente(id_cliente, limite):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT id_solicitacao_evento, data_evento, quantidade, tema, status, data_solicitacao
        FROM solicitacao_evento
        WHERE id_cliente = %s
        ORDER BY data_solicitacao DESC, id_solicitacao_evento DESC
        LIMIT %s
    """
    cur.execute(sql, (id_cliente, limite))
    res = cur.fetchall()

    lista = []
    for x in res:
        encomenda = {}
        encomenda["numero"] = x[0]
        encomenda["status"] = x[4]
        encomenda["status_texto"] = evento_regras.texto_do_status_da_encomenda(x[4])
        encomenda["data_evento_texto"] = evento_regras.formatar_data_do_evento(x[1])
        encomenda["resumo"] = evento_regras.resumir_encomenda(x[2], x[3])
        encomenda["data_texto"] = historico_regras.formatar_data(x[5])
        lista.append(encomenda)

    cur.close()
    con.close()
    return lista


# função que conta quantos pedidos de orçamento esse e-mail mandou nas últimas 24 horas
def contar_solicitacoes_recentes(email):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT COUNT(*) FROM solicitacao_evento
        WHERE email_contato = %s AND data_solicitacao > CURRENT_TIMESTAMP - INTERVAL '24 hours'
    """
    cur.execute(sql, (email,))
    total = cur.fetchone()[0]

    cur.close()
    con.close()
    return int(total)