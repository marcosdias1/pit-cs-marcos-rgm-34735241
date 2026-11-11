from werkzeug.security import generate_password_hash
from models import senha_regras
from models.conexao import pegar_conexao

# aqui fica o que mexe no banco para a recuperação de senha (cartão 19)


# função que cria o token de recuperação de um cliente (procura pelo cpf)
# devolve um dicionário com o nome, o e-mail e o token, ou None se não existe conta ativa com esse cpf
# o token de verdade só existe aqui e no e-mail: no banco vai só o hash
def criar_token_de_recuperacao(cpf):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        sql = """
            SELECT c.id_cliente, p.nome, p.email
            FROM cliente c
            JOIN pessoa p ON p.id_pessoa = c.id_cliente
            WHERE c.cpf = %s AND c.ativo = TRUE
        """
        cur.execute(sql, (cpf,))
        linha = cur.fetchone()

        if linha is None:
            con.rollback()
            cur.close()
            con.close()
            return None

        id_cliente = linha[0]
        nome = linha[1]
        email = linha[2]

        # os links antigos que ainda não foram usados deixam de valer (só o último pedido vale)
        cur.execute("UPDATE token_recuperacao_senha SET usado = TRUE WHERE id_cliente = %s AND usado = FALSE",
                    (id_cliente,))

        token = senha_regras.gerar_token()
        sql = """
            INSERT INTO token_recuperacao_senha (id_cliente, token_hash, expira_em)
            VALUES (%s, %s, CURRENT_TIMESTAMP + (%s * INTERVAL '1 minute'))
        """
        cur.execute(sql, (id_cliente, senha_regras.hash_do_token(token), senha_regras.MINUTOS_DE_VALIDADE))

        con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return {"nome": nome, "email": email, "token": token}


# função que confere se o token do link ainda vale (existe, não foi usado e não venceu)
def token_e_valido(token):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT 1 FROM token_recuperacao_senha
        WHERE token_hash = %s AND usado = FALSE AND expira_em > CURRENT_TIMESTAMP
    """
    cur.execute(sql, (senha_regras.hash_do_token(token),))
    linha = cur.fetchone()

    cur.close()
    con.close()
    return linha is not None


# função que troca a senha usando o token do link
# devolve True se trocou, ou False se o token não vale mais
def trocar_senha_com_token(token, nova_senha):
    nova_hash = generate_password_hash(nova_senha)
    trocou = False

    con = pegar_conexao()
    cur = con.cursor()

    try:
        # o FOR UPDATE trava a linha do token: se duas pessoas usarem o mesmo link ao mesmo tempo, só uma passa
        sql = """
            SELECT id_cliente FROM token_recuperacao_senha
            WHERE token_hash = %s AND usado = FALSE AND expira_em > CURRENT_TIMESTAMP
            FOR UPDATE
        """
        cur.execute(sql, (senha_regras.hash_do_token(token),))
        linha = cur.fetchone()

        if linha is None:
            con.rollback()
        else:
            id_cliente = linha[0]
            cur.execute("UPDATE cliente SET senha_hash = %s WHERE id_cliente = %s", (nova_hash, id_cliente))
            # o link usado (e qualquer outro que sobrou) não vale mais
            cur.execute("UPDATE token_recuperacao_senha SET usado = TRUE WHERE id_cliente = %s AND usado = FALSE",
                        (id_cliente,))
            con.commit()
            trocou = True

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return trocou