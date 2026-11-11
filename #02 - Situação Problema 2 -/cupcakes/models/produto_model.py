# model dos produtos (cupcakes)
# aqui fica tudo que busca produto no banco de dados

from models.conexao import pegar_conexao
import unicodedata

# função que pega os cupcakes que vão aparecer na vitrine
# regra do cartão 01: produto com estoque zero não aparece
# regra do cartão 03: o preço é o da tabela de preço que está ativa
def listar_cupcakes_vitrine():
    # abre a conexão com o banco
    con = pegar_conexao()
    # o cursor é o que executa os comandos sql
    cur = con.cursor()

    # o sql que busca os cupcakes (peguei das consultas de exemplo do banco)
    sql = """
        SELECT p.id_produto, p.nome, pp.valor,
               COALESCE(string_agg(cat.nome, ', ' ORDER BY cat.nome), '-') AS categorias
        FROM produto p
        JOIN cupcake c ON c.id_cupcake = p.id_produto
        JOIN preco_produto pp ON pp.id_produto = p.id_produto
        JOIN tabela_preco tp ON tp.id_tabela_preco = pp.id_tabela_preco AND tp.ativa = TRUE
        LEFT JOIN cupcake_categoria cc ON cc.id_cupcake = c.id_cupcake
        LEFT JOIN categoria cat ON cat.id_categoria = cc.id_categoria
        WHERE p.ativo = TRUE AND p.estoque > 0
        GROUP BY p.id_produto, p.nome, pp.valor
        ORDER BY p.nome
    """
    cur.execute(sql)

    # pega todas as linhas que o banco devolveu
    res = cur.fetchall()
    print(res)  # pra ver o que veio do banco

    # monta uma lista de dicionarios pra ficar mais facil de usar no html
    lista = []
    for x in res:
        cupcake = {}
        cupcake["id"] = x[0]
        cupcake["nome"] = x[1]
        # deixa o preço no formato brasileiro, com virgula
        preco_texto = str(x[2])
        preco_texto = preco_texto.replace(".", ",")
        cupcake["preco"] = "R$ " + preco_texto
        cupcake["categorias"] = x[3]
        lista.append(cupcake)
    cur.close()
    con.close()

    return lista


# função que tira os acentos e deixa tudo minúsculo (pra busca achar "limao" quando no banco está "Limão")
def tirar_acentos(texto):
    # o NFD separa a letra do acento (ex: "ã" vira "a" + "~")
    texto = unicodedata.normalize("NFD", texto)
    resultado = ""
    for letra in texto:
        # os acentos soltos são da categoria "Mn", então eu pulo eles
        if unicodedata.category(letra) != "Mn":
            resultado = resultado + letra
    return resultado.lower()

# função que filtra uma lista de cupcakes pelo texto da busca (cartão 04)
# procura no nome e nos ingredientes, sem ligar pra acento nem maiúscula
def filtrar_por_busca(lista, busca):
    # separa o que a pessoa digitou em palavras (ex: "red velvet" vira ["red", "velvet"])
    palavras = tirar_acentos(busca).split()

    if len(palavras) == 0:
        return lista

    resultado = []
    for cupcake in lista:
        # junta nome e ingredientes num texto só
        texto = tirar_acentos(cupcake["nome"] + " " + cupcake["ingredientes"])

        # o cupcake só entra se TODAS as palavras aparecerem no texto
        achou_todas = True
        for palavra in palavras:
            if palavra not in texto:
                achou_todas = False
        if achou_todas == True:
            resultado.append(cupcake)

    return resultado


# função que lista as categorias pros botões de filtro (cartão 02)
def listar_categorias():
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT id_categoria, nome FROM categoria ORDER BY id_categoria")
    res = cur.fetchall()

    lista = []
    for x in res:
        categoria = {}
        categoria["id"] = x[0]
        categoria["nome"] = x[1]
        lista.append(categoria)

    cur.close()
    con.close()
    return lista


# função que lista os cupcakes da vitrine com filtro de categoria e busca (cartões 01, 02 e 04)
def listar_cupcakes_filtrados(id_categoria, busca):
    con = pegar_conexao()
    cur = con.cursor()

    # parte de cima do sql (igual à da vitrine, só que agora traz os ingredientes também)
    sql_inicio = """
        SELECT p.id_produto, p.nome, pp.valor, c.ingredientes,
               COALESCE(string_agg(cat.nome, ', ' ORDER BY cat.nome), '-') AS categorias
        FROM produto p
        JOIN cupcake c ON c.id_cupcake = p.id_produto
        JOIN preco_produto pp ON pp.id_produto = p.id_produto
        JOIN tabela_preco tp ON tp.id_tabela_preco = pp.id_tabela_preco AND tp.ativa = TRUE
        LEFT JOIN cupcake_categoria cc ON cc.id_cupcake = c.id_cupcake
        LEFT JOIN categoria cat ON cat.id_categoria = cc.id_categoria
        WHERE p.ativo = TRUE AND p.estoque > 0
    """
    # condição extra do filtro (começa vazia)
    sql_filtro = ""
    parametros = []

    if id_categoria is not None:
        # descobre o nome da categoria escolhida
        cur.execute("SELECT nome FROM categoria WHERE id_categoria = %s", (id_categoria,))
        linha = cur.fetchone()

        if linha is None:
            # categoria que não existe: não mostra nada
            sql_filtro = " AND FALSE "
        else:
            if linha[0].lower() == "diet":
                # regra do cartão 02: no diet some tudo que tem açúcar comum
                sql_filtro = " AND c.contem_acucar = FALSE "
            else:
                sql_filtro = """ AND EXISTS (SELECT 1 FROM cupcake_categoria x
                                 WHERE x.id_cupcake = p.id_produto AND x.id_categoria = %s) """
                parametros.append(id_categoria)

    # parte de baixo do sql
    sql_fim = """
        GROUP BY p.id_produto, p.nome, pp.valor, c.ingredientes
        ORDER BY p.nome
    """

    # junta as 3 partes (o que a pessoa digitou NUNCA entra no texto do sql, só pelo %s)
    cur.execute(sql_inicio + sql_filtro + sql_fim, parametros)
    res = cur.fetchall()

    lista = []
    for x in res:
        cupcake = {}
        cupcake["id"] = x[0]
        cupcake["nome"] = x[1]
        preco_texto = str(x[2])
        preco_texto = preco_texto.replace(".", ",")
        cupcake["preco"] = "R$ " + preco_texto
        cupcake["ingredientes"] = x[3]
        cupcake["categorias"] = x[4]
        lista.append(cupcake)

    cur.close()
    con.close()

    # a busca por texto é feita aqui no python (assim ignora acento e maiúscula)
    lista = filtrar_por_busca(lista, busca)
    return lista


# função que busca UM cupcake pelo id, pra tela de detalhes (cartão 03)
# devolve o dicionário ou None se não achar (ou se estiver sem estoque)
def buscar_cupcake_por_id(id_cupcake):
    con = pegar_conexao()
    cur = con.cursor()

    sql = """
        SELECT p.id_produto, p.nome, pp.valor, c.descricao, c.ingredientes, c.alergenos, c.contem_acucar,
               COALESCE(string_agg(cat.nome, ', ' ORDER BY cat.nome), '-') AS categorias
        FROM produto p
        JOIN cupcake c ON c.id_cupcake = p.id_produto
        JOIN preco_produto pp ON pp.id_produto = p.id_produto
        JOIN tabela_preco tp ON tp.id_tabela_preco = pp.id_tabela_preco AND tp.ativa = TRUE
        LEFT JOIN cupcake_categoria cc ON cc.id_cupcake = c.id_cupcake
        LEFT JOIN categoria cat ON cat.id_categoria = cc.id_categoria
        WHERE p.id_produto = %s AND p.ativo = TRUE AND p.estoque > 0
        GROUP BY p.id_produto, p.nome, pp.valor, c.descricao, c.ingredientes, c.alergenos, c.contem_acucar
    """
    cur.execute(sql, (id_cupcake,))
    x = cur.fetchone()

    cur.close()
    con.close()

    # não achou
    if x is None:
        return None

    cupcake = {}
    cupcake["id"] = x[0]
    cupcake["nome"] = x[1]
    preco_texto = str(x[2])
    preco_texto = preco_texto.replace(".", ",")
    cupcake["preco"] = "R$ " + preco_texto
    cupcake["descricao"] = x[3]
    cupcake["ingredientes"] = x[4]
    cupcake["alergenos"] = x[5]
    cupcake["contem_acucar"] = x[6]
    cupcake["categorias"] = x[7]
    return cupcake