from decimal import Decimal
from app import app
from models import carrinho_model
from models import produto_model


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

# deixa o navegador de mentira como cliente logado (o cliente de mentira tem id 7)
def entrar_como_cliente():
    navegador = pegar_navegador()
    with navegador.session_transaction() as sessao:
        sessao["tipo"] = "cliente"
        sessao["id_cliente"] = 7
        sessao["nome"] = "Ana Teste"
    return navegador


#  funções de mentira (no lugar das que falam com o banco) 

def item_de_mentira(id_produto, nome, tipo, preco, quantidade, estoque):
    item = {}
    item["id"] = id_produto
    item["nome"] = nome
    item["tipo"] = tipo
    item["estoque"] = estoque
    item["disponivel"] = estoque > 0
    item["preco_unitario"] = Decimal(preco)
    item["quantidade"] = quantidade
    item["preco_texto"] = carrinho_model.formatar_dinheiro(Decimal(preco))
    item["subtotal_texto"] = carrinho_model.formatar_dinheiro(Decimal(preco) * quantidade)
    return item

# 2 chocolates (12,00 cada) e 1 calda (5,00) = 29,00
def itens_com_cupcake(id_carrinho):
    lista = []
    lista.append(item_de_mentira(3, "Chocolate", "CUPCAKE", "12.00", 2, 50))
    lista.append(item_de_mentira(9, "Calda de chocolate", "ADICIONAL", "5.00", 1, 100))
    return lista

def itens_so_adicional(id_carrinho):
    lista = []
    lista.append(item_de_mentira(9, "Calda de chocolate", "ADICIONAL", "5.00", 1, 100))
    return lista

def itens_passando_do_estoque(id_carrinho):
    lista = []
    lista.append(item_de_mentira(3, "Chocolate", "CUPCAKE", "12.00", 5, 3))
    return lista

def itens_sem_estoque(id_carrinho):
    lista = []
    lista.append(item_de_mentira(3, "Chocolate", "CUPCAKE", "12.00", 1, 0))
    return lista

def itens_vazio(id_carrinho):
    return []

def adicionais_de_mentira(id_carrinho):
    lista = []
    lista.append({"id": 10, "nome": "Chocolate extra", "tipo": "CHOCOLATE", "preco_texto": "R$ 4,00"})
    return lista

def carrinho_numero_1(id_cliente, id_sessao):
    return 1

def contador_zero(id_cliente, id_sessao):
    return 0

def contador_tres(id_cliente, id_sessao):
    return 3


# função que dá erro de propósito (o * faz ela aceitar qualquer quantidade de argumentos)
def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")

# troca as funções do carrinho pelas de mentira (carrinho vazio)
def deixar_carrinho_de_mentira(monkeypatch):
    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", carrinho_numero_1)
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_vazio)
    monkeypatch.setattr(carrinho_model, "listar_adicionais", adicionais_de_mentira)

# troca as funções da vitrine (quando o teste termina na vitrine)
def deixar_vitrine_de_mentira(monkeypatch):
    def categorias():
        return []

    def cupcakes(id_categoria, busca):
        return []

    monkeypatch.setattr(produto_model, "listar_categorias", categorias)
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", cupcakes)

# troca a função da tela de detalhes (quando o teste termina nela)
def deixar_detalhe_de_mentira(monkeypatch):
    def cupcake(id_cupcake):
        dados = {}
        dados["id"] = id_cupcake
        dados["nome"] = "Chocolate"
        dados["preco"] = "R$ 12,00"
        dados["descricao"] = "Bolinho de chocolate"
        dados["ingredientes"] = "farinha, cacau"
        dados["alergenos"] = "leite"
        dados["contem_acucar"] = True
        dados["categorias"] = "-"
        return dados

    monkeypatch.setattr(produto_model, "buscar_cupcake_por_id", cupcake)

# troca uma função do carrinho por uma que anota com o que foi chamada
# (devolve a lista de chamadas pra gente conferir no teste)
def espionar(monkeypatch, nome_da_funcao, retorno):
    chamadas = []

    def falso(*args):
        chamadas.append(args)
        return retorno

    monkeypatch.setattr(carrinho_model, nome_da_funcao, falso)
    return chamadas

#  tela do carrinho 

def test_carrinho_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/carrinho")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_carrinho_vazio_mostra_o_aviso(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = navegador.get("/carrinho").data.decode("utf-8")
    assert "Seu carrinho está vazio" in texto
    assert "Ver cupcakes" in texto

def test_carrinho_mostra_os_itens_e_o_total(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_com_cupcake)
    navegador = entrar_como_visitante()
    texto = navegador.get("/carrinho").data.decode("utf-8")
    assert "Chocolate" in texto
    assert "Calda de chocolate" in texto
    # 2 x 12,00 do cupcake
    assert "R$ 24,00" in texto
    # total: 24,00 + 5,00
    assert "R$ 29,00" in texto

def test_carrinho_sugere_adicionais_quando_tem_cupcake(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_com_cupcake)
    navegador = entrar_como_visitante()
    texto = navegador.get("/carrinho").data.decode("utf-8")
    assert "Que tal adicionar?" in texto
    assert "Chocolate extra" in texto

def test_carrinho_nao_sugere_adicionais_sem_cupcake(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_so_adicional)
    navegador = entrar_como_visitante()
    texto = navegador.get("/carrinho").data.decode("utf-8")
    assert "Que tal adicionar?" not in texto

def test_carrinho_avisa_quando_passa_do_estoque(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_passando_do_estoque)
    navegador = entrar_como_visitante()
    texto = navegador.get("/carrinho").data.decode("utf-8")
    assert "Só temos 3 em estoque" in texto

def test_carrinho_avisa_quando_o_item_ficou_sem_estoque(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_sem_estoque)
    navegador = entrar_como_visitante()
    texto = navegador.get("/carrinho").data.decode("utf-8")
    assert "Sem estoque no momento" in texto

def test_carrinho_com_erro_no_banco_mostra_mensagem(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", erro_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/carrinho")
    texto = resposta.data.decode("utf-8")
    assert resposta.status_code == 200
    assert "Não foi possível abrir o carrinho agora" in texto

def test_numero_do_carrinho_aparece_no_topo(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_tres)
    navegador = entrar_como_visitante()
    texto = navegador.get("/carrinho").data.decode("utf-8")
    assert 'qtd-carrinho">3<' in texto


#  tela de detalhes (formulário de adicionar) 

def test_detalhe_tem_o_formulario_de_adicionar(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    deixar_detalhe_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = navegador.get("/cupcake/3").data.decode("utf-8")
    assert 'action="/carrinho/adicionar"' in texto
    assert 'name="quantidade"' in texto
    assert "Adicionar ao carrinho" in texto
    # o formulário tem que mandar o id do cupcake
    assert 'name="id_produto" value="3"' in texto


#  adicionar 

def test_adicionar_pelo_get_nao_pode(monkeypatch):
    navegador = entrar_como_visitante()
    resposta = navegador.get("/carrinho/adicionar")
    # 405 quer dizer "método não permitido"
    assert resposta.status_code == 405

def test_adicionar_sem_entrar_manda_pro_login(monkeypatch):
    chamadas = espionar(monkeypatch, "adicionar_item", "")
    navegador = pegar_navegador()
    resposta = navegador.post("/carrinho/adicionar", data={"id_produto": "3", "quantidade": "1"})
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    assert chamadas == []

def test_adicionar_chama_o_model_e_avisa_na_vitrine(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    deixar_vitrine_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "adicionar_item", "")
    navegador = entrar_como_visitante()
    dados = {"id_produto": "3", "quantidade": "2", "voltar_para": "vitrine"}
    resposta = navegador.post("/carrinho/adicionar", data=dados, follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    # o model recebeu: carrinho 1, produto 3, quantidade 2
    assert chamadas == [(1, 3, 2)]
    assert "Adicionado ao carrinho!" in texto

def test_adicionar_com_quantidade_invalida_nao_chega_no_model(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    deixar_detalhe_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "adicionar_item", "")
    navegador = entrar_como_visitante()
    for quantidade in ["0", "-1", "abc", "100", "", "1.5"]:
        dados = {"id_produto": "3", "quantidade": quantidade}
        resposta = navegador.post("/carrinho/adicionar", data=dados, follow_redirects=True)
        texto = resposta.data.decode("utf-8")
        assert "Escolha uma quantidade entre 1 e 99" in texto
    assert chamadas == []

def test_adicionar_com_produto_invalido_nao_chega_no_model(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    deixar_vitrine_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "adicionar_item", "")
    navegador = entrar_como_visitante()
    dados = {"id_produto": "abc", "quantidade": "1"}
    resposta = navegador.post("/carrinho/adicionar", data=dados, follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Produto inválido" in texto
    assert chamadas == []

def test_adicionar_mostra_o_erro_de_estoque_que_veio_do_model(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    deixar_detalhe_de_mentira(monkeypatch)
    espionar(monkeypatch, "adicionar_item", "Só temos 3 em estoque (você já tem 0 no carrinho).")
    navegador = entrar_como_visitante()
    dados = {"id_produto": "3", "quantidade": "5"}
    resposta = navegador.post("/carrinho/adicionar", data=dados, follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Só temos 3 em estoque" in texto
    # o erro aparece na tela de detalhes, onde a pessoa estava
    assert "Bolinho de chocolate" in texto

def test_adicionar_adicional_pelo_carrinho_volta_pro_carrinho(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_com_cupcake)
    espionar(monkeypatch, "adicionar_item", "")
    navegador = entrar_como_visitante()
    dados = {"id_produto": "10", "quantidade": "1", "voltar_para": "carrinho"}
    resposta = navegador.post("/carrinho/adicionar", data=dados, follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Adicionado ao carrinho!" in texto
    assert "Meu carrinho" in texto

def test_adicionar_nao_deixa_redirecionar_pra_outro_site(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    espionar(monkeypatch, "adicionar_item", "")
    navegador = entrar_como_visitante()
    dados = {"id_produto": "3", "quantidade": "1", "voltar_para": "http://site-malvado.com"}
    resposta = navegador.post("/carrinho/adicionar", data=dados)
    assert resposta.status_code == 302
    assert "site-malvado" not in resposta.headers["Location"]

def test_adicionar_com_erro_no_banco_mostra_mensagem(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    deixar_detalhe_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "adicionar_item", erro_de_mentira)
    navegador = entrar_como_visitante()
    dados = {"id_produto": "3", "quantidade": "1"}
    resposta = navegador.post("/carrinho/adicionar", data=dados, follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Não foi possível adicionar agora" in texto


#  de quem é o carrinho 

def test_visitante_ganha_um_codigo_de_sessao_que_dura(monkeypatch):
    recebidos = []

    def falso(id_cliente, id_sessao):
        recebidos.append(id_cliente)
        recebidos.append(id_sessao)
        return 1

    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", falso)
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    espionar(monkeypatch, "adicionar_item", "")
    navegador = entrar_como_visitante()
    navegador.post("/carrinho/adicionar", data={"id_produto": "3", "quantidade": "1"})

    # visitante: não tem id de cliente e tem um código de 32 letras e números
    assert recebidos[0] is None
    assert len(recebidos[1]) == 32
    with navegador.session_transaction() as sessao:
        assert sessao["id_sessao"] == recebidos[1]
        # sessão permanente: o carrinho não some se fechar o navegador
        assert sessao.permanent == True

def test_visitante_mantem_o_mesmo_codigo_nas_proximas_compras(monkeypatch):
    recebidos = []

    def falso(id_cliente, id_sessao):
        recebidos.append(id_sessao)
        return 1

    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", falso)
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    espionar(monkeypatch, "adicionar_item", "")
    navegador = entrar_como_visitante()
    navegador.post("/carrinho/adicionar", data={"id_produto": "3", "quantidade": "1"})
    navegador.post("/carrinho/adicionar", data={"id_produto": "4", "quantidade": "1"})
    assert recebidos[0] == recebidos[1]

def test_cliente_usa_o_id_do_cliente(monkeypatch):
    recebidos = []

    def falso(id_cliente, id_sessao):
        recebidos.append(id_cliente)
        recebidos.append(id_sessao)
        return 1

    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", falso)
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    espionar(monkeypatch, "adicionar_item", "")
    navegador = entrar_como_cliente()
    navegador.post("/carrinho/adicionar", data={"id_produto": "3", "quantidade": "1"})
    assert recebidos[0] == 7
    assert recebidos[1] is None


#  aumentar, diminuir e tirar 

def test_alterar_mais_e_menos(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "alterar_quantidade", "")
    navegador = entrar_como_visitante()
    navegador.post("/carrinho/alterar", data={"id_produto": "3", "acao": "mais"})
    navegador.post("/carrinho/alterar", data={"id_produto": "3", "acao": "menos"})
    # (carrinho, produto, mudança)
    assert chamadas == [(1, 3, 1), (1, 3, -1)]

def test_alterar_com_acao_invalida_nao_chega_no_model(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "alterar_quantidade", "")
    navegador = entrar_como_visitante()
    resposta = navegador.post("/carrinho/alterar", data={"id_produto": "3", "acao": "apagar"},
                              follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Não entendi o que você quis fazer" in texto
    assert chamadas == []

def test_alterar_mostra_o_erro_de_estoque_que_veio_do_model(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    espionar(monkeypatch, "alterar_quantidade", "Só temos 3 em estoque.")
    navegador = entrar_como_visitante()
    resposta = navegador.post("/carrinho/alterar", data={"id_produto": "3", "acao": "mais"},
                              follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Só temos 3 em estoque." in texto

def test_alterar_sem_entrar_manda_pro_login(monkeypatch):
    chamadas = espionar(monkeypatch, "alterar_quantidade", "")
    navegador = pegar_navegador()
    resposta = navegador.post("/carrinho/alterar", data={"id_produto": "3", "acao": "mais"})
    assert "/login" in resposta.headers["Location"]
    assert chamadas == []

def test_remover_chama_o_model(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "remover_item", "")
    navegador = entrar_como_visitante()
    navegador.post("/carrinho/remover", data={"id_produto": "3"})
    assert chamadas == [(1, 3)]

def test_remover_com_id_invalido_nao_chega_no_model(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "remover_item", "")
    navegador = entrar_como_visitante()
    navegador.post("/carrinho/remover", data={"id_produto": "abc"})
    assert chamadas == []

def test_remover_com_erro_no_banco_mostra_mensagem(monkeypatch):
    deixar_carrinho_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "remover_item", erro_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.post("/carrinho/remover", data={"id_produto": "3"}, follow_redirects=True)
    texto = resposta.data.decode("utf-8")
    assert "Não foi possível remover agora" in texto