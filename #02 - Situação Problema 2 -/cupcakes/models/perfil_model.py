# aqui fica o que mexe no banco para o Meu perfil: dados da conta e endereços (cartão 20)

from models import perfil_regras
from models.conexao import pegar_conexao


## DADOS DA CONTA

# função que busca os dados do cliente (devolve um dicionário ou None se não achar)
def buscar_dados_do_cliente(id_cliente):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT p.nome, p.email, p.celular, c.cpf
        FROM cliente c
        JOIN pessoa p ON p.id_pessoa = c.id_cliente
        WHERE c.id_cliente = %s AND c.ativo = TRUE
    """
    cur.execute(sql, (id_cliente,))
    linha = cur.fetchone()

    cur.close()
    con.close()

    if linha is None:
        return None

    dados = {}
    dados["nome"] = linha[0]
    dados["email"] = linha[1]
    dados["celular"] = linha[2]
    dados["cpf"] = linha[3]
    return dados


# função que confere se OUTRA pessoa já usa esse e-mail (o e-mail é único no banco)
def email_em_uso_por_outro(email, id_cliente):
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT 1 FROM pessoa WHERE email = %s AND id_pessoa <> %s", (email, id_cliente))
    linha = cur.fetchone()
    cur.close()
    con.close()
    return linha is not None


# função que troca nome, e-mail e celular do cliente
# (os pedidos antigos continuam com o contato que tinham na hora da compra)
def atualizar_dados(id_cliente, nome, email, celular):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        cur.execute("UPDATE pessoa SET nome = %s, email = %s, celular = %s WHERE id_pessoa = %s",
                    (nome, email, celular, id_cliente))
        con.commit()
    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()


## ENDEREÇOS
COLUNAS_DO_ENDERECO = "id_endereco, apelido, cep, rua, numero, complemento, bairro, cidade, uf, principal"

# função que monta o dicionário do endereço a partir de uma linha do banco
def montar_endereco(linha):
    endereco = {}
    endereco["id"] = linha[0]
    endereco["apelido"] = linha[1]
    endereco["cep"] = linha[2]
    endereco["rua"] = linha[3]
    endereco["numero"] = linha[4]
    endereco["complemento"] = linha[5]
    endereco["bairro"] = linha[6]
    endereco["cidade"] = linha[7]
    endereco["uf"] = linha[8]
    endereco["principal"] = linha[9]
    endereco["nome"] = perfil_regras.nome_do_endereco(linha[1])
    endereco["resumo"] = perfil_regras.resumir_endereco(linha[3], linha[4], linha[5], linha[6],
                                                        linha[7], linha[8], linha[2])
    return endereco


# função que lista os endereços ativos do cliente (o principal vem primeiro)
def listar_enderecos(id_cliente):
    con = pegar_conexao()
    cur = con.cursor()

    sql = "SELECT " + COLUNAS_DO_ENDERECO + """
            FROM endereco
            WHERE id_cliente = %s AND ativo = TRUE
            ORDER BY principal DESC, id_endereco
    """
    cur.execute(sql, (id_cliente,))
    res = cur.fetchall()

    lista = []
    for linha in res:
        lista.append(montar_endereco(linha))

    cur.close()
    con.close()
    return lista


# função que busca UM endereço ativo do cliente (confere que é dele)
# devolve um dicionário ou None
def buscar_endereco(id_cliente, id_endereco):
    con = pegar_conexao()
    cur = con.cursor()

    sql = "SELECT " + COLUNAS_DO_ENDERECO + """
            FROM endereco
            WHERE id_endereco = %s AND id_cliente = %s AND ativo = TRUE
    """
    cur.execute(sql, (id_endereco, id_cliente))
    linha = cur.fetchone()

    cur.close()
    con.close()

    if linha is None:
        return None
    return montar_endereco(linha)


# função que conta quantos endereços ativos o cliente tem
def contar_enderecos(id_cliente):
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM endereco WHERE id_cliente = %s AND ativo = TRUE", (id_cliente,))
    total = cur.fetchone()[0]
    cur.close()
    con.close()
    return int(total)


# função que guarda um endereço novo
# campos é um dicionário com apelido, cep, rua, numero, complemento, bairro, cidade e uf
# o primeiro endereço do cliente já vira o principal
def criar_endereco(id_cliente, campos):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        cur.execute("SELECT COUNT(*) FROM endereco WHERE id_cliente = %s AND ativo = TRUE", (id_cliente,))
        ja_tem = cur.fetchone()[0]
        vira_principal = (ja_tem == 0)

        sql = """
            INSERT INTO endereco (id_cliente, apelido, cep, rua, numero, complemento, bairro, cidade, uf, principal)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql, (id_cliente, campos["apelido"], campos["cep"], campos["rua"], campos["numero"],
                          campos["complemento"], campos["bairro"], campos["cidade"], campos["uf"],
                          vira_principal))
        con.commit()

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()


# função que "edita" um endereço
# o endereço antigo é desativado e um novo é criado no lugar (com o mesmo "principal")
# por quê: os pedidos antigos apontam para o endereço antigo, e eles têm que continuar mostrando onde foram entregues
# devolve True se deu certo, ou False se o endereço não existe (ou não é dele)
def substituir_endereco(id_cliente, id_endereco, campos):
    achou = False
    con = pegar_conexao()
    cur = con.cursor()

    try:
        cur.execute("""SELECT principal FROM endereco
                       WHERE id_endereco = %s AND id_cliente = %s AND ativo = TRUE
                       FOR UPDATE""", (id_endereco, id_cliente))
        linha = cur.fetchone()

        if linha is None:
            con.rollback()
        else:
            era_principal = linha[0]

            # desativa o antigo primeiro (o banco só aceita um principal ativo por cliente)
            cur.execute("UPDATE endereco SET ativo = FALSE, principal = FALSE WHERE id_endereco = %s",
                        (id_endereco,))

            sql = """
                INSERT INTO endereco (id_cliente, apelido, cep, rua, numero, complemento, bairro, cidade, uf, principal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (id_cliente, campos["apelido"], campos["cep"], campos["rua"], campos["numero"],
                              campos["complemento"], campos["bairro"], campos["cidade"], campos["uf"],
                              era_principal))
            con.commit()
            achou = True

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return achou


# função que marca um endereço como o principal (o que vem preenchido no fechamento do pedido)
# devolve True se deu certo, ou False se o endereço não existe (ou não é dele)
def definir_principal(id_cliente, id_endereco):
    achou = False
    con = pegar_conexao()
    cur = con.cursor()

    try:
        cur.execute("SELECT 1 FROM endereco WHERE id_endereco = %s AND id_cliente = %s AND ativo = TRUE FOR UPDATE",
                    (id_endereco, id_cliente))
        linha = cur.fetchone()

        if linha is None:
            con.rollback()
        else:
            # primeiro tira o principal de todos, depois marca o escolhido
            cur.execute("UPDATE endereco SET principal = FALSE WHERE id_cliente = %s AND principal = TRUE",
                        (id_cliente,))
            cur.execute("UPDATE endereco SET principal = TRUE WHERE id_endereco = %s", (id_endereco,))
            con.commit()
            achou = True

    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return achou


# função que "exclui" um endereço (na verdade só desativa, os pedidos antigos continuam apontando para ele)
# devolve True se deu certo, ou False se o endereço não existe (ou não é dele)
def excluir_endereco(id_cliente, id_endereco):
    con = pegar_conexao()
    cur = con.cursor()

    try:
        cur.execute("UPDATE endereco SET ativo = FALSE, principal = FALSE WHERE id_endereco = %s AND id_cliente = %s AND ativo = TRUE",
                    (id_endereco, id_cliente))
        achou = (cur.rowcount == 1)
        con.commit()
    except Exception as e:
        con.rollback()
        cur.close()
        con.close()
        raise e

    cur.close()
    con.close()
    return achou