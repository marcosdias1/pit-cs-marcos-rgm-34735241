from app import app
from models import produto_model

# testes das rotas da vitrine (filtro, busca, detalhe e api)
# esses testes NÃO mexem no banco: o monkeypatch troca as funções do model por funções de mentira


# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
    return navegador


# deixa o navegador de mentira como visitante (assim ele passa da tela de login)
def entrar_como_visitante():
    navegador = pegar_navegador()
    navegador.get("/visitante")
    return navegador


# funções de mentira (no lugar das que falam com o banco) 

def categorias_de_mentira():
    lista = []
    lista.append({"id": 1, "nome": "Diet"})
    lista.append({"id": 2, "nome": "Salgado"})
    return lista

def cupcakes_de_mentira(id_categoria, busca):
    lista = []
    lista.append({"id": 3, "nome": "Chocolate", "preco": "R$ 12,00", "categorias": "-", "ingredientes": "cacau"})
    return lista

def cupcakes_vazio(id_categoria, busca):
    return []

def cupcake_de_mentira(id_cupcake):
    cupcake = {}
    cupcake["id"] = id_cupcake
    cupcake["nome"] = "Limão"
    cupcake["preco"] = "R$ 12,00"
    cupcake["descricao"] = "Bolinho de limão com cobertura cítrica"
    cupcake["ingredientes"] = "farinha, suco de limão"
    cupcake["alergenos"] = "leite, glúten"
    cupcake["contem_acucar"] = True
    cupcake["categorias"] = "Promoção"
    return cupcake

def cupcake_sem_alergenos(id_cupcake):
    cupcake = cupcake_de_mentira(id_cupcake)
    cupcake["alergenos"] = None
    return cupcake

def cupcake_diet(id_cupcake):
    cupcake = cupcake_de_mentira(id_cupcake)
    cupcake["contem_acucar"] = False
    return cupcake

def cupcake_nenhum(id_cupcake):
    return None

# função que dá erro de propósito (o * faz ela aceitar qualquer quantidade de argumentos)
def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")


# troca as funções da vitrine pelas de mentira
def deixar_vitrine_de_mentira(monkeypatch):
    monkeypatch.setattr(produto_model, "listar_categorias", categorias_de_mentira)
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", cupcakes_de_mentira)


# api (json que o javascript usa) 

def test_api_sem_entrar_devolve_401():
    navegador = pegar_navegador()
    resposta = navegador.get("/api/cupcakes")
    assert resposta.status_code == 401
    assert "erro" in resposta.get_json()

def test_api_devolve_a_lista(monkeypatch):
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", cupcakes_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/api/cupcakes")
    dados = resposta.get_json()
    assert resposta.status_code == 200
    assert dados["cupcakes"][0]["nome"] == "Chocolate"

def test_api_repassa_categoria_e_busca_pro_model(monkeypatch):
    recebidos = []

    def falso(id_categoria, busca):
        recebidos.append(id_categoria)
        recebidos.append(busca)
        return []

    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", falso)
    navegador = entrar_como_visitante()
    navegador.get("/api/cupcakes", query_string={"categoria": "2", "busca": "  limao  "})
    # a categoria vira número e a busca fica sem os espaços
    assert recebidos[0] == 2
    assert recebidos[1] == "limao"

def test_api_categoria_que_nao_e_numero_vira_none(monkeypatch):
    recebidos = []

    def falso(id_categoria, busca):
        recebidos.append(id_categoria)
        return []

    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", falso)
    navegador = entrar_como_visitante()
    navegador.get("/api/cupcakes", query_string={"categoria": "1; DROP TABLE produto"})
    assert recebidos[0] is None

def test_api_corta_busca_muito_grande(monkeypatch):
    recebidos = []

    def falso(id_categoria, busca):
        recebidos.append(busca)
        return []

    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", falso)
    navegador = entrar_como_visitante()
    navegador.get("/api/cupcakes", query_string={"busca": "a" * 200})
    assert len(recebidos[0]) == 60

def test_api_com_erro_no_banco_devolve_500(monkeypatch):
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", erro_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/api/cupcakes")
    assert resposta.status_code == 500
    assert "erro" in resposta.get_json()


#  vitrine 

def test_vitrine_mostra_botoes_e_cupcakes(monkeypatch):
    deixar_vitrine_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = navegador.get("/").data.decode("utf-8")
    assert ">Todos<" in texto
    assert ">Diet<" in texto
    assert ">Salgado<" in texto
    assert "Chocolate" in texto
    # o card tem que levar pra tela de detalhes
    assert 'href="/cupcake/3"' in texto

def test_vitrine_marca_a_categoria_escolhida(monkeypatch):
    deixar_vitrine_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = navegador.get("/", query_string={"categoria": "2"}).data.decode("utf-8")

    achou_salgado = False
    achou_todos = False
    pedacos = texto.split("<a ")
    for pedaco in pedacos:
        if 'data-id="2"' in pedaco:
            achou_salgado = True
            assert "chip-ativo" in pedaco
        if 'data-id=""' in pedaco:
            achou_todos = True
            assert "chip-ativo" not in pedaco
    assert achou_salgado == True
    assert achou_todos == True

def test_vitrine_mantem_o_texto_da_busca(monkeypatch):
    deixar_vitrine_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = navegador.get("/", query_string={"busca": "limao"}).data.decode("utf-8")
    assert 'value="limao"' in texto


def test_vitrine_sem_resultado_na_busca(monkeypatch):
    monkeypatch.setattr(produto_model, "listar_categorias", categorias_de_mentira)
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", cupcakes_vazio)
    navegador = entrar_como_visitante()
    texto = navegador.get("/", query_string={"busca": "pizza"}).data.decode("utf-8")
    assert "Nenhum cupcake encontrado" in texto

def test_vitrine_sem_nenhum_cupcake_a_venda(monkeypatch):
    monkeypatch.setattr(produto_model, "listar_categorias", categorias_de_mentira)
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", cupcakes_vazio)
    navegador = entrar_como_visitante()
    texto = navegador.get("/").data.decode("utf-8")
    assert "Nenhum cupcake disponível no momento" in texto

def test_vitrine_com_erro_no_banco_mostra_mensagem(monkeypatch):
    monkeypatch.setattr(produto_model, "listar_categorias", erro_de_mentira)
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", erro_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/")
    texto = resposta.data.decode("utf-8")
    assert resposta.status_code == 200
    assert "Não foi possível carregar os cupcakes agora" in texto


# tela de detalhes 

def test_detalhe_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/cupcake/1")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_detalhe_mostra_os_dados_do_cupcake(monkeypatch):
    monkeypatch.setattr(produto_model, "buscar_cupcake_por_id", cupcake_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/cupcake/1")
    texto = resposta.data.decode("utf-8")
    assert resposta.status_code == 200
    assert "Limão" in texto
    assert "R$ 12,00" in texto
    assert "Bolinho de limão com cobertura cítrica" in texto
    assert "farinha, suco de limão" in texto
    assert "Contém: leite, glúten" in texto
    assert "Contém açúcar comum" in texto

def test_detalhe_sem_alergenos_avisa_que_nao_foi_informado(monkeypatch):
    monkeypatch.setattr(produto_model, "buscar_cupcake_por_id", cupcake_sem_alergenos)
    navegador = entrar_como_visitante()
    texto = navegador.get("/cupcake/1").data.decode("utf-8")
    assert "Não informado" in texto

def test_detalhe_do_cupcake_diet(monkeypatch):
    monkeypatch.setattr(produto_model, "buscar_cupcake_por_id", cupcake_diet)
    navegador = entrar_como_visitante()
    texto = navegador.get("/cupcake/1").data.decode("utf-8")
    assert "Sem açúcar comum" in texto

def test_detalhe_de_cupcake_que_nao_existe_volta_pra_vitrine(monkeypatch):
    deixar_vitrine_de_mentira(monkeypatch)
    monkeypatch.setattr(produto_model, "buscar_cupcake_por_id", cupcake_nenhum)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/cupcake/999", follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Esse cupcake não está disponível no momento." in texto

def test_detalhe_com_id_gigante_nem_chega_no_banco(monkeypatch):
    chamadas = []

    def falso(id_cupcake):
        chamadas.append(id_cupcake)
        return None

    deixar_vitrine_de_mentira(monkeypatch)
    monkeypatch.setattr(produto_model, "buscar_cupcake_por_id", falso)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/cupcake/99999999999")
    assert resposta.status_code == 302
    assert chamadas == []

def test_detalhe_com_id_que_nao_e_numero_da_404():
    navegador = entrar_como_visitante()
    resposta = navegador.get("/cupcake/abc")
    assert resposta.status_code == 404

def test_detalhe_com_erro_no_banco_avisa_e_volta(monkeypatch):
    deixar_vitrine_de_mentira(monkeypatch)
    monkeypatch.setattr(produto_model, "buscar_cupcake_por_id", erro_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/cupcake/1", follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Não foi possível abrir esse cupcake agora" in texto