from werkzeug.security import generate_password_hash, check_password_hash
from models.conexao import pegar_conexao

# função que procura um cliente pelo cpf
# devolve um dicionário com os dados ou None se não achar

def buscar_cliente_por_cpf(cpf):
    con = pegar_conexao()
    cur = con.cursor()

    # o %s é pro banco colocar o cpf com segurança (nunca colar o texto direto no sql)
    sql = """
        SELECT c.id_cliente, p.nome, c.senha_hash, c.ativo
        FROM cliente c
        JOIN pessoa p ON p.id_pessoa = c.id_cliente
        WHERE c.cpf = %s
    """
    cur.execute(sql, (cpf,))
    linha = cur.fetchone()

    cur.close()
    con.close()

    # se não achou ninguém
    if linha is None:
        return None

    cliente = {}
    cliente["id"] = linha[0]
    cliente["nome"] = linha[1]
    cliente["senha_hash"] = linha[2]
    cliente["ativo"] = linha[3]
    return cliente


# função que confere se já tem alguém com esse email
def email_ja_existe(email):
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT 1 FROM pessoa WHERE email = %s", (email,))
    linha = cur.fetchone()
    cur.close()
    con.close()
    if linha is None:
        return False
    else:
        return True


# função do login: confere o cpf e a senha - devolve o cliente se estiver certo, ou None se estiver errado
def conferir_login(cpf, senha):
    cliente = buscar_cliente_por_cpf(cpf)

    # não achou o cpf
    if cliente is None:
        return None

    # conta desativada não entra
    if cliente["ativo"] == False:
        return None

    # compara a senha digitada com o hash que está no banco
    # (se o hash do banco estiver estragado, o werkzeug dá erro, aí eu trato como senha errada)
    senha_certa = False
    try:
        senha_certa = check_password_hash(cliente["senha_hash"], senha)
    except ValueError as e:
        print("HASH INVALIDO NO BANCO:", e)
        senha_certa = False

    if senha_certa == False:
        return None

    return cliente


# função que cria a conta nova (cartão 17)
# grava a pessoa, o cliente, o endereço principal e o cupom de 15 reais
# se der erro em qualquer parte, desfaz tudo (rollback)
def criar_cliente(nome, email, celular, cpf, senha, cep, rua, numero, bairro, cidade, uf):
    # faz o hash da senha antes de guardar
    senha_hash = generate_password_hash(senha)

    con = pegar_conexao()
    cur = con.cursor()

    try:
        # 1 grava na tabela pessoa e pega o id que o banco criou
        cur.execute(
            "INSERT INTO pessoa (nome, email, celular) VALUES (%s, %s, %s) RETURNING id_pessoa",
            (nome, email, celular)
        )
        id_novo = cur.fetchone()[0]

        # 2 grava na tabela cliente (mesmo id da pessoa)
        cur.execute(
            "INSERT INTO cliente (id_cliente, cpf, senha_hash) VALUES (%s, %s, %s)",
            (id_novo, cpf, senha_hash)
        )

        # 3 grava o endereço e marca como principal
        cur.execute(
            """INSERT INTO endereco (id_cliente, apelido, cep, rua, numero, bairro, cidade, uf, principal)
               VALUES (%s, 'Casa', %s, %s, %s, %s, %s, %s, TRUE)""",
            (id_novo, cep, rua, numero, bairro, cidade, uf)
        )

        # 4 cria o cupom de 15 reais pra primeira compra (vale 30 dias)
        codigo_cupom = "BEMVINDO15-" + str(id_novo)
        cur.execute(
            """INSERT INTO cupom (id_cliente, codigo, tipo, valor, valido_de, valido_ate, uso_unico, primeira_compra)
               VALUES (%s, %s, 'VALOR_FIXO', 15.00, CURRENT_DATE, CURRENT_DATE + 30, TRUE, TRUE)""",
            (id_novo, codigo_cupom)
        )

        # deu tudo certo, então salva de verdade
        con.commit()

    except Exception as e:
        # deu erro, desfaz tudo que tinha feito
        con.rollback()
        cur.close()
        con.close()

        raise e

    cur.close()
    con.close()
    return id_novo