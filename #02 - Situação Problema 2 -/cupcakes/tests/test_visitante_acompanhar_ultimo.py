from decimal import Decimal
from app import app
from models import carrinho_model
from models import pedido_model

# testes do link "Acompanhar pedido" do topo (item 2: o visitante não achava o pedido depois de sair da tela de confirmação)
# a rota /acompanhar/ultimo leva o visitante direto ao último pedido dele

# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
    return navegador

def entrar_como_visitante():
    navegador = pegar_navegador()
    navegador.get("/visitante")
    return navegador

def pegar_texto(resposta):
    return resposta.data.decode("utf-8")

def contador_zero(id_cliente, id_sessao):
    return 0

def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")

def pegar_mensagens(navegador):
    with navegador.session_transaction() as sessao:
        lista = sessao.get("_flashes", [])
    textos = []
    for categoria, texto in lista:
        textos.append(categoria + ": " + texto)
    return textos


# troca a busca "id -> número" por uma de mentira (o pedido de id 50 tem o número 10050, o de id 51 tem o 10051)
# devolve a lista de ids que foram perguntados
def preparar(monkeypatch):
    perguntados = []

    def buscar_numero(id_pedido):
        perguntados.append(id_pedido)
        if id_pedido == 50:
            return 10050
        if id_pedido == 51:
            return 10051
        return None

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(pedido_model, "buscar_numero_por_id", buscar_numero)
    return perguntados


def test_link_sem_nenhum_pedido_leva_pra_busca_por_numero_e_email(monkeypatch):
    perguntados = preparar(monkeypatch)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/acompanhar/ultimo")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/acompanhar"
    # nem foi no banco
    assert perguntados == []

def test_visitante_que_acabou_de_criar_o_pedido_vai_pra_ele(monkeypatch):
    preparar(monkeypatch)
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 50
    resposta = navegador.get("/acompanhar/ultimo")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/pedido/10050"

def test_com_varios_pedidos_vai_pro_mais_novo(monkeypatch):
    # a lista guarda o mais novo no final
    preparar(monkeypatch)
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedidos_liberados"] = [50, 51]
    resposta = navegador.get("/acompanhar/ultimo")
    assert resposta.headers["Location"] == "/pedido/10051"

def test_pedido_pago_ganha_de_um_novo_pedido_ainda_sem_pagar(monkeypatch):
    # o visitante pagou o 50 e depois começou outro pedido (51) sem pagar
    # o link tem que levar pro que ele pagou
    preparar(monkeypatch)
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedidos_liberados"] = [50]
        sessao["pedido_atual"] = 51
    resposta = navegador.get("/acompanhar/ultimo")
    assert resposta.headers["Location"] == "/pedido/10050"

def test_pedido_que_nao_existe_mais_cai_na_busca(monkeypatch):
    preparar(monkeypatch)
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 999
    resposta = navegador.get("/acompanhar/ultimo")
    assert resposta.headers["Location"] == "/acompanhar"

def test_erro_no_banco_mostra_mensagem_e_vai_pra_busca(monkeypatch):
    preparar(monkeypatch)
    monkeypatch.setattr(pedido_model, "buscar_numero_por_id", erro_de_mentira)
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 50
    resposta = navegador.get("/acompanhar/ultimo")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/acompanhar"
    assert pegar_mensagens(navegador)[0].startswith("erro: Não foi possível abrir o pedido agora")

def test_quem_nunca_entrou_tambem_cai_na_busca(monkeypatch):
    # sem nem escolher "visitante" a busca por número e e-mail abre do mesmo jeito
    preparar(monkeypatch)
    navegador = pegar_navegador()
    resposta = navegador.get("/acompanhar/ultimo")
    assert resposta.headers["Location"] == "/acompanhar"


# depois de pagar, o pedido entra na lista do visitante 

def test_pagar_guarda_o_pedido_na_lista_de_pedidos_do_visitante(monkeypatch):
    from models import pagamento_simulado
    from controllers import pagamento_controller

    pedido = {}
    pedido["id"] = 50
    pedido["numero"] = 10050
    pedido["id_cliente"] = None
    pedido["status"] = "AGUARDANDO_PAGAMENTO"
    pedido["total"] = Decimal("36.50")
    pedido["total_texto"] = "R$ 36,50"
    pedido["previsao_entrega"] = None
    pedido["nome_contato"] = "Visitante Teste"
    pedido["email_contato"] = "visita@gmail.com"
    pedido["id_cupom"] = None
    pedido["forma"] = ""

    def buscar(numero):
        return pedido

    def conferir_cupom(pedido, hoje):
        return ""

    def confirmar(id_pedido, id_carrinho, forma, valor, codigo, id_cliente):
        return ""

    def carrinho_de_mentira():
        return 5

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", buscar)
    monkeypatch.setattr(pedido_model, "conferir_cupom_do_pedido", conferir_cupom)
    monkeypatch.setattr(pedido_model, "confirmar_pagamento", confirmar)
    monkeypatch.setattr(pagamento_controller, "pegar_id_do_carrinho", carrinho_de_mentira)

    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 50

    resposta = navegador.post("/pagamento/10050", data={"forma": "PIX"})
    assert resposta.status_code == 302
    assert "/pedido/10050/confirmado" in resposta.headers["Location"]

    with navegador.session_transaction() as sessao:
        assert sessao["pedidos_liberados"] == [50]

    # paga de novo (a função de mentira não muda o status): o pedido não pode aparecer duas vezes na lista
    navegador.post("/pagamento/10050", data={"forma": "PIX"})
    with navegador.session_transaction() as sessao:
        assert sessao["pedidos_liberados"] == [50]
