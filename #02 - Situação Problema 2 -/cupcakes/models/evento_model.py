# aqui fica o que mexe no banco para o orçamento de evento (cartão 08)

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