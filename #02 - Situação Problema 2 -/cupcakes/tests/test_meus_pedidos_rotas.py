# testes das rotas "Meus pedidos" e "Comprar de novo" (cartão 15)

from decimal import Decimal
from app import app
from models import carrinho_model
from models import historico_model
from models import pedido_model
 

# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
    return navegador

def entrar_como_visitante():
    navegador = pegar_navegador()
    navegador.get("/visitante")
    return navegador


# cliente logado de mentira (id 7)
def entrar_como_cliente():
    navegador = pegar_navegador()
    with navegador.session_transaction() as sessao:
        sessao["tipo"] = "cliente"
        sessao["id_cliente"] = 7
        sessao["nome"] = "Ana Teste"
    return navegador

def pegar_texto(resposta):
    return resposta.data.decode("utf-8")


# lê as mensagens (flash) que ficaram guardadas na sessão, sem precisar abrir a tela que as mostra
def pegar_mensagens(navegador):
    with navegador.session_transaction() as sessao:
        lista = sessao.get("_flashes", [])
    textos = []
    for categoria, texto in lista:
        textos.append(categoria + ": " + texto)
    return textos


# dados de mentira 

def pedido_da_lista(numero, status, itens_texto="2x Chocolate"):
    pedido = {}
    pedido["id"] = numero - 10000
    pedido["numero"] = numero
    pedido["status"] = status
    pedido["status_texto"] = status.capitalize()
    pedido["total_texto"] = "R$ 36,50"
    pedido["data_texto"] = "08/11/2026 às 18:05"
    pedido["pode_acompanhar"] = (status not in ["CANCELADO", "AGUARDANDO_PAGAMENTO"])
    pedido["itens"] = []
    pedido["itens_texto"] = itens_texto
    return pedido


# o pedido que o buscar_pedido_por_numero devolve (id 50, número 10050, do cliente 7)
def pedido_de_mentira(id_cliente, status):
    pedido = {}
    pedido["id"] = 50
    pedido["numero"] = 10050
    pedido["id_cliente"] = id_cliente
    pedido["status"] = status
    pedido["total"] = Decimal("36.50")
    pedido["total_texto"] = "R$ 36,50"
    pedido["previsao_entrega"] = None
    pedido["email_contato"] = "ana@gmail.com"
    pedido["id_cupom"] = None
    return pedido

def contador_zero(id_cliente, id_sessao):
    return 0


# função que dá erro de propósito (o * faz ela aceitar qualquer quantidade de argumentos)
def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")


# troca as funções do banco pelas de mentira da tela "Meus pedidos"
# devolve a lista de chamadas da atualização de status e a lista de chamadas da listagem
def preparar_lista(monkeypatch, pedidos):
    atualizadas = []
    listagens = []

    def listar(id_cliente, limite):
        listagens.append((id_cliente, limite))
        return pedidos

    def atualizar(id_pedido):
        atualizadas.append(id_pedido)

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(historico_model, "listar_pedidos_do_cliente", listar)
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", atualizar)
    return atualizadas, listagens


# troca as funções do banco pelas de mentira da recompra
# itens: o que o pedido antigo tinha. falhas: dicionário {id_produto: mensagem de erro}
# devolve a lista de itens que foram colocados no carrinho
def preparar_recompra(monkeypatch, pedido, itens, falhas):
    colocados = []

    def buscar(numero):
        return pedido

    def listar_itens(id_pedido):
        return itens

    def carrinho_de_mentira(id_cliente, id_sessao):
        return 5

    def adicionar(id_carrinho, id_produto, quantidade):
        if id_produto in falhas:
            return falhas[id_produto]
        colocados.append((id_carrinho, id_produto, quantidade))
        return ""

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", buscar)
    monkeypatch.setattr(historico_model, "listar_itens_para_recompra", listar_itens)
    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", carrinho_de_mentira)
    monkeypatch.setattr(carrinho_model, "adicionar_item", adicionar)
    return colocados

ITENS_ANTIGOS = [
    {"id_produto": 1, "nome": "Chocolate", "quantidade": 2},
    {"id_produto": 2, "nome": "Morango", "quantidade": 1},
]


# MEUS PEDIDOS: quem pode ver 

def test_meus_pedidos_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/meus-pedidos")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_visitante_nao_tem_historico(monkeypatch):
    preparar_lista(monkeypatch, [])
    navegador = entrar_como_visitante()
    resposta = navegador.get("/meus-pedidos", follow_redirects=True)
    texto = pegar_texto(resposta)
    assert "Entre na sua conta para ver o histórico de compras" in texto
    assert "Acompanhar" not in texto.replace("Acompanhar um pedido", "")

def test_visitante_nem_pergunta_pro_banco(monkeypatch):
    atualizadas, listagens = preparar_lista(monkeypatch, [])
    navegador = entrar_como_visitante()
    navegador.get("/meus-pedidos")
    assert listagens == []


# MEUS PEDIDOS: o que aparece 

def test_cliente_ve_os_proprios_pedidos(monkeypatch):
    pedidos = [pedido_da_lista(10050, "ENTREGUE", "2x Chocolate, 1x Morango"),
               pedido_da_lista(10040, "CANCELADO", "1x Baunilha")]
    preparar_lista(monkeypatch, pedidos)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/meus-pedidos")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Pedido #10050" in texto
    assert "Pedido #10040" in texto
    assert "2x Chocolate, 1x Morango" in texto
    assert "R$ 36,50" in texto
    assert "08/11/2026 às 18:05" in texto

def test_lista_pede_so_os_pedidos_do_cliente_logado(monkeypatch):
    atualizadas, listagens = preparar_lista(monkeypatch, [])
    navegador = entrar_como_cliente()
    navegador.get("/meus-pedidos")
    # primeiro o id do cliente (7), depois o limite (20)
    assert listagens == [(7, 20)]

def test_botao_acompanhar_so_nos_pedidos_que_tem_acompanhamento(monkeypatch):
    pedidos = [pedido_da_lista(10050, "EM_PREPARO"), pedido_da_lista(10040, "CANCELADO")]
    preparar_lista(monkeypatch, pedidos)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert 'href="/pedido/10050"' in texto
    assert 'href="/pedido/10040"' not in texto

def test_todo_pedido_tem_o_botao_comprar_de_novo(monkeypatch):
    pedidos = [pedido_da_lista(10050, "ENTREGUE"), pedido_da_lista(10040, "CANCELADO")]
    preparar_lista(monkeypatch, pedidos)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert 'action="/pedido/10050/comprar-de-novo"' in texto
    assert 'action="/pedido/10040/comprar-de-novo"' in texto
    assert texto.count("Comprar de novo") == 2

def test_comprar_de_novo_e_um_formulario_post(monkeypatch):
    preparar_lista(monkeypatch, [pedido_da_lista(10050, "ENTREGUE")])
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert 'method="POST"' in texto

def test_sem_pedidos_mostra_mensagem_e_link_pra_vitrine(monkeypatch):
    preparar_lista(monkeypatch, [])
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert "Você ainda não fez nenhum pedido." in texto
    assert "Ver cupcakes" in texto

def test_erro_no_banco_mostra_mensagem(monkeypatch):
    preparar_lista(monkeypatch, [])
    monkeypatch.setattr(historico_model, "listar_pedidos_do_cliente", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/meus-pedidos")
    assert resposta.status_code == 200
    assert "Não foi possível abrir o histórico agora" in pegar_texto(resposta)

def test_aviso_quando_a_lista_chega_no_limite(monkeypatch):
    pedidos = []
    for i in range(20):
        pedidos.append(pedido_da_lista(10100 + i, "ENTREGUE"))
    preparar_lista(monkeypatch, pedidos)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert "Mostrando os 20 pedidos mais recentes." in texto

def test_sem_aviso_de_limite_quando_tem_poucos_pedidos(monkeypatch):
    preparar_lista(monkeypatch, [pedido_da_lista(10050, "ENTREGUE")])
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert "pedidos mais recentes" not in texto


# MEUS PEDIDOS: o status andando (simulação) 

def test_atualiza_so_os_pedidos_que_ainda_estao_andando(monkeypatch):
    pedidos = [pedido_da_lista(10050, "EM_PREPARO"),
               pedido_da_lista(10049, "ENTREGUE"),
               pedido_da_lista(10048, "CANCELADO"),
               pedido_da_lista(10047, "CONFIRMADO")]
    atualizadas, listagens = preparar_lista(monkeypatch, pedidos)
    navegador = entrar_como_cliente()
    navegador.get("/meus-pedidos")
    # os ids dos pedidos 10050 e 10047
    assert atualizadas == [50, 47]

def test_lista_de_novo_depois_de_atualizar(monkeypatch):
    atualizadas, listagens = preparar_lista(monkeypatch, [pedido_da_lista(10050, "EM_PREPARO")])
    navegador = entrar_como_cliente()
    navegador.get("/meus-pedidos")
    assert len(listagens) == 2

def test_nao_lista_de_novo_se_nada_andou(monkeypatch):
    atualizadas, listagens = preparar_lista(monkeypatch, [pedido_da_lista(10050, "ENTREGUE")])
    navegador = entrar_como_cliente()
    navegador.get("/meus-pedidos")
    assert atualizadas == []
    assert len(listagens) == 1

def test_erro_ao_atualizar_um_pedido_nao_derruba_a_pagina(monkeypatch):
    pedidos = [pedido_da_lista(10050, "EM_PREPARO")]
    preparar_lista(monkeypatch, pedidos)
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/meus-pedidos")
    assert resposta.status_code == 200
    assert "Pedido #10050" in pegar_texto(resposta)


# link "Meus pedidos" no cabeçalho 

def test_cabecalho_do_cliente_tem_o_link_meus_pedidos(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert 'href="/meus-pedidos"' in texto
    assert "Meus pedidos" in texto

def test_cabecalho_do_visitante_nao_tem_o_link_meus_pedidos(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert 'href="/meus-pedidos"' not in texto


# COMPRAR DE NOVO: quem pode 

def test_comprar_de_novo_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_visitante_nao_compra_de_novo(monkeypatch):
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(None, "ENTREGUE"), ITENS_ANTIGOS, {})
    navegador = entrar_como_visitante()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    assert colocados == []

def test_nao_compra_de_novo_pedido_de_outro_cliente(monkeypatch):
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(8, "ENTREGUE"), ITENS_ANTIGOS, {})
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert resposta.status_code == 302
    assert "/meus-pedidos" in resposta.headers["Location"]
    assert colocados == []
    assert "erro: Pedido não encontrado." in pegar_mensagens(navegador)

def test_nao_compra_de_novo_pedido_que_nao_existe(monkeypatch):
    colocados = preparar_recompra(monkeypatch, None, ITENS_ANTIGOS, {})
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert "/meus-pedidos" in resposta.headers["Location"]
    assert colocados == []

def test_pedido_nao_pago_volta_pro_pagamento(monkeypatch):
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(7, "AGUARDANDO_PAGAMENTO"), ITENS_ANTIGOS, {})
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert "/pagamento/10050" in resposta.headers["Location"]
    assert colocados == []

def test_comprar_de_novo_por_get_nao_existe():
    navegador = entrar_como_cliente()
    resposta = navegador.get("/pedido/10050/comprar-de-novo")
    assert resposta.status_code == 405


# COMPRAR DE NOVO: o que acontece 

def test_coloca_todos_os_itens_no_carrinho(monkeypatch):
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(7, "ENTREGUE"), ITENS_ANTIGOS, {})
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert resposta.status_code == 302
    assert "/carrinho" in resposta.headers["Location"]
    # (id do carrinho, id do produto, quantidade)
    assert colocados == [(5, 1, 2), (5, 2, 1)]
    assert "ok: 2 itens foram para o carrinho. Os preços são os de hoje." in pegar_mensagens(navegador)

def test_pedido_cancelado_tambem_pode_ser_comprado_de_novo(monkeypatch):
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(7, "CANCELADO"), ITENS_ANTIGOS, {})
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert "/carrinho" in resposta.headers["Location"]
    assert len(colocados) == 2

def test_item_sem_estoque_nao_impede_os_outros(monkeypatch):
    falhas = {2: "Esse produto está sem estoque no momento."}
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(7, "ENTREGUE"), ITENS_ANTIGOS, falhas)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert "/carrinho" in resposta.headers["Location"]
    assert colocados == [(5, 1, 2)]
    mensagens = pegar_mensagens(navegador)
    assert "ok: 1 item foi para o carrinho. Os preços são os de hoje." in mensagens
    assert "aviso: Não deu para colocar no carrinho. Morango: Esse produto está sem estoque no momento." in mensagens

def test_se_nenhum_item_foi_volta_pra_lista(monkeypatch):
    falhas = {1: "Sem estoque.", 2: "Sem estoque."}
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(7, "ENTREGUE"), ITENS_ANTIGOS, falhas)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert "/meus-pedidos" in resposta.headers["Location"]
    assert colocados == []
    mensagens = pegar_mensagens(navegador)
    assert len(mensagens) == 1
    assert mensagens[0].startswith("aviso: Não deu para colocar no carrinho.")

def test_erro_inesperado_em_um_item_vira_aviso(monkeypatch):
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(7, "ENTREGUE"), ITENS_ANTIGOS, {})

    def adicionar(id_carrinho, id_produto, quantidade):
        if id_produto == 1:
            raise Exception("o banco caiu (de mentira)")
        colocados.append((id_carrinho, id_produto, quantidade))
        return ""

    monkeypatch.setattr(carrinho_model, "adicionar_item", adicionar)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert "/carrinho" in resposta.headers["Location"]
    assert colocados == [(5, 2, 1)]
    assert "Chocolate: Não foi possível adicionar agora." in pegar_mensagens(navegador)[1]

def test_erro_ao_buscar_os_itens_mostra_mensagem(monkeypatch):
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(7, "ENTREGUE"), ITENS_ANTIGOS, {})
    monkeypatch.setattr(historico_model, "listar_itens_para_recompra", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert "/meus-pedidos" in resposta.headers["Location"]
    assert colocados == []
    assert "erro: Não foi possível comprar de novo agora. Tente de novo em alguns minutos." in pegar_mensagens(navegador)

def test_pedido_sem_itens_nao_coloca_nada(monkeypatch):
    colocados = preparar_recompra(monkeypatch, pedido_de_mentira(7, "ENTREGUE"), [], {})
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/comprar-de-novo")
    assert "/meus-pedidos" in resposta.headers["Location"]
    assert colocados == []
