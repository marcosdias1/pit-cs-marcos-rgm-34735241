from decimal import Decimal
from datetime import datetime, timedelta
from app import app
from models import carrinho_model
from models import pedido_model
from models import historico_model
from models import evento_model

# testes das rotas de CANCELAR PEDIDO e do que aparece nas telas por causa dele (item 15)
# também confere o aviso de saída da tela de acompanhamento (item 17)
# esses testes NÃO mexem no banco: o monkeypatch troca as funções do model por funções de mentira
# (o SQL de verdade do cancelar_pedido não é testado aqui: ele só roda com o PostgreSQL)

CONFIRMADO_EM = datetime(2026, 11, 8, 18, 0, 0)


# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
    return navegador

def entrar_como_visitante_com_pedido():
    navegador = pegar_navegador()
    navegador.get("/visitante")
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 50
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

# lê as mensagens (flash) que ficaram guardadas na sessão
def pegar_mensagens(navegador):
    with navegador.session_transaction() as sessao:
        lista = sessao.get("_flashes", [])
    textos = []
    for categoria, texto in lista:
        textos.append(categoria + ": " + texto)
    return textos


# dados de mentira

def pedido_de_mentira(id_cliente, status):
    pedido = {}
    pedido["id"] = 50
    pedido["numero"] = 10050
    pedido["id_cliente"] = id_cliente
    pedido["status"] = status
    pedido["total"] = Decimal("36.50")
    pedido["total_texto"] = "R$ 36,50"
    pedido["previsao_entrega"] = CONFIRMADO_EM + timedelta(minutes=40)
    pedido["nome_contato"] = "Visitante Teste"
    pedido["email_contato"] = "visita@gmail.com"
    pedido["id_cupom"] = None
    pedido["forma"] = "PIX"
    return pedido

def contador_zero(id_cliente, id_sessao):
    return 0

def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")


# prepara as funções do banco que a rota de cancelar usa
# resposta_do_cancelamento é o que o cancelar_pedido devolve ("" = deu certo)
# devolve a lista de chamadas (na ordem em que aconteceram)
def preparar_cancelamento(monkeypatch, id_cliente, status, resposta_do_cancelamento=""):
    chamadas = []

    def buscar(numero):
        return pedido_de_mentira(id_cliente, status)

    def atualizar(id_pedido):
        chamadas.append(("atualizar", id_pedido))

    def cancelar(id_pedido, id_pessoa):
        chamadas.append(("cancelar", id_pedido, id_pessoa))
        return resposta_do_cancelamento

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", buscar)
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", atualizar)
    monkeypatch.setattr(pedido_model, "cancelar_pedido", cancelar)
    return chamadas


# a rota POST /pedido/<numero>/cancelar 

def test_cancelar_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.post("/pedido/10050/cancelar")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_cancelar_nao_abre_pelo_endereco_get(monkeypatch):
    # cancelar muda dados, então só aceita POST (o get cai na página de erro 405)
    preparar_cancelamento(monkeypatch, 7, "CONFIRMADO")
    navegador = entrar_como_cliente()
    resposta = navegador.get("/pedido/10050/cancelar")
    assert resposta.status_code == 405

def test_cliente_cancela_o_proprio_pedido(monkeypatch):
    chamadas = preparar_cancelamento(monkeypatch, 7, "CONFIRMADO")
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/cancelar")
    assert resposta.status_code == 302
    assert "/meus-pedidos" in resposta.headers["Location"]
    # o id do pedido e quem cancelou (o cliente 7) foram pro model
    assert ("cancelar", 50, 7) in chamadas
    mensagens = pegar_mensagens(navegador)
    assert len(mensagens) == 1
    assert mensagens[0].startswith("ok: ")
    assert "#10050" in mensagens[0]

def test_o_pedido_anda_na_simulacao_antes_de_cancelar(monkeypatch):
    # se a pessoa ficou com a tela aberta, o pedido pode já ter saído pra entrega
    # por isso o status é atualizado ANTES de tentar cancelar
    chamadas = preparar_cancelamento(monkeypatch, 7, "EM_PREPARO")
    navegador = entrar_como_cliente()
    navegador.post("/pedido/10050/cancelar")
    assert chamadas[0][0] == "atualizar"
    assert chamadas[1][0] == "cancelar"

def test_cancelar_pedido_que_ja_saiu_mostra_o_motivo(monkeypatch):
    # o model devolve o motivo (ele confere o status de novo dentro da transação)
    chamadas = preparar_cancelamento(monkeypatch, 7, "SAIU_PARA_ENTREGA",
                                     "O pedido já saiu para entrega e não pode mais ser cancelado.")
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/cancelar")
    assert resposta.status_code == 302
    mensagens = pegar_mensagens(navegador)
    assert mensagens == ["aviso: O pedido já saiu para entrega e não pode mais ser cancelado."]

def test_visitante_cancela_o_pedido_dele_e_volta_pra_vitrine(monkeypatch):
    chamadas = preparar_cancelamento(monkeypatch, None, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.post("/pedido/10050/cancelar")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/"
    # visitante não tem id de pessoa
    assert ("cancelar", 50, None) in chamadas

def test_ninguem_cancela_o_pedido_de_outra_pessoa(monkeypatch):
    # o pedido é do cliente 99, quem está logado é o cliente 7
    chamadas = preparar_cancelamento(monkeypatch, 99, "CONFIRMADO")
    navegador = entrar_como_cliente()
    navegador.post("/pedido/10050/cancelar")
    for chamada in chamadas:
        assert chamada[0] != "cancelar"
    assert "erro: Pedido não encontrado." in pegar_mensagens(navegador)

def test_visitante_nao_cancela_o_pedido_de_um_cliente(monkeypatch):
    chamadas = preparar_cancelamento(monkeypatch, 7, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    navegador.post("/pedido/10050/cancelar")
    for chamada in chamadas:
        assert chamada[0] != "cancelar"

def test_erro_no_banco_ao_cancelar_mostra_mensagem_e_nao_quebra(monkeypatch):
    preparar_cancelamento(monkeypatch, 7, "CONFIRMADO")
    monkeypatch.setattr(pedido_model, "cancelar_pedido", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/pedido/10050/cancelar")
    assert resposta.status_code == 302
    mensagens = pegar_mensagens(navegador)
    assert len(mensagens) == 1
    assert mensagens[0].startswith("erro: Não foi possível cancelar o pedido agora")

def test_erro_na_simulacao_do_status_tambem_nao_cancela(monkeypatch):
    chamadas = preparar_cancelamento(monkeypatch, 7, "CONFIRMADO")
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", erro_de_mentira)
    navegador = entrar_como_cliente()
    navegador.post("/pedido/10050/cancelar")
    assert chamadas == []
    assert pegar_mensagens(navegador)[0].startswith("erro: ")


# tela de acompanhamento: botão de cancelar e aviso de saída 

def historico_ate(status):
    historico = [{"status": "CONFIRMADO", "data_hora": CONFIRMADO_EM}]
    if status in ["EM_PREPARO", "SAIU_PARA_ENTREGA", "ENTREGUE"]:
        historico.append({"status": "EM_PREPARO", "data_hora": CONFIRMADO_EM + timedelta(seconds=30)})
    if status in ["SAIU_PARA_ENTREGA", "ENTREGUE"]:
        historico.append({"status": "SAIU_PARA_ENTREGA", "data_hora": CONFIRMADO_EM + timedelta(seconds=90)})
    if status == "ENTREGUE":
        historico.append({"status": "ENTREGUE", "data_hora": CONFIRMADO_EM + timedelta(seconds=150)})
    return historico

def preparar_tela(monkeypatch, status):
    def buscar(numero):
        return pedido_de_mentira(None, status)

    def historico(id_pedido):
        return historico_ate(status)

    def itens(id_pedido):
        return [{"nome": "Chocolate", "quantidade": 2, "subtotal_texto": "R$ 24,00"}]

    def nada(id_pedido):
        pass

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", buscar)
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", nada)
    monkeypatch.setattr(pedido_model, "listar_historico_do_pedido", historico)
    monkeypatch.setattr(pedido_model, "listar_itens_do_pedido", itens)

def test_tela_do_pedido_confirmado_tem_o_botao_de_cancelar(monkeypatch):
    preparar_tela(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "Cancelar pedido" in texto
    assert 'action="/pedido/10050/cancelar"' in texto
    assert "area-cancelar" in texto

def test_tela_do_pedido_em_preparo_ainda_tem_o_botao_de_cancelar(monkeypatch):
    preparar_tela(monkeypatch, "EM_PREPARO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "Cancelar pedido" in texto

def test_tela_do_pedido_que_saiu_nao_tem_botao_de_cancelar(monkeypatch):
    preparar_tela(monkeypatch, "SAIU_PARA_ENTREGA")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "Cancelar pedido" not in texto
    assert "area-cancelar" not in texto

def test_tela_do_pedido_entregue_nao_tem_botao_de_cancelar(monkeypatch):
    preparar_tela(monkeypatch, "ENTREGUE")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "Cancelar pedido" not in texto

def test_o_json_do_status_diz_se_ainda_pode_cancelar(monkeypatch):
    preparar_tela(monkeypatch, "EM_PREPARO")
    navegador = entrar_como_visitante_com_pedido()
    dados = navegador.get("/api/pedido/10050/status").get_json()
    assert dados["pode_cancelar"] == True
    assert dados["avisar_saida"] == True

    preparar_tela(monkeypatch, "SAIU_PARA_ENTREGA")
    dados = navegador.get("/api/pedido/10050/status").get_json()
    assert dados["pode_cancelar"] == False
    assert dados["avisar_saida"] == False

def test_aviso_de_saida_aparece_com_o_pedido_confirmado_e_diz_que_nao_envia_de_verdade(monkeypatch):
    preparar_tela(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "Avisaremos você por mensagem quando o pedido sair para entrega" in texto
    # o texto tem que ser honesto: nenhuma mensagem é enviada de verdade
    assert "nenhuma mensagem é enviada de verdade" in texto
    # e a caixa não está escondida
    assert 'id="aviso-saida" class="mensagem-info" >' in texto

def test_aviso_de_saida_vem_escondido_quando_o_pedido_ja_saiu(monkeypatch):
    preparar_tela(monkeypatch, "SAIU_PARA_ENTREGA")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert 'id="aviso-saida" class="mensagem-info" hidden>' in texto

def test_o_javascript_do_acompanhamento_esconde_o_aviso_e_o_botao():
    # o JS não roda no pytest, então aqui eu só confiro se o código está no arquivo
    arquivo = open("public/static/js/acompanhar.js", encoding="utf-8").read()
    assert "aviso-saida" in arquivo
    assert "area-cancelar" in arquivo
    assert "dados.pode_cancelar" in arquivo
    assert "dados.avisar_saida" in arquivo


# tela Meus pedidos: botão de cancelar em cada pedido 

def pedido_da_lista(numero, status, pode_cancelar):
    pedido = {}
    pedido["id"] = numero - 10000
    pedido["numero"] = numero
    pedido["status"] = status
    pedido["status_texto"] = status.capitalize()
    pedido["total_texto"] = "R$ 36,50"
    pedido["data_texto"] = "08/11/2026 às 18:05"
    pedido["pode_acompanhar"] = (status != "CANCELADO")
    pedido["pode_cancelar"] = pode_cancelar
    pedido["itens"] = []
    pedido["itens_texto"] = "2x Chocolate"
    return pedido

def test_meus_pedidos_so_mostra_cancelar_nos_pedidos_que_podem(monkeypatch):
    lista = [pedido_da_lista(10003, "CONFIRMADO", True),
             pedido_da_lista(10002, "ENTREGUE", False),
             pedido_da_lista(10001, "CANCELADO", False)]

    def listar(id_cliente, limite):
        return lista

    def nenhuma(id_cliente, limite):
        return []

    def nada(id_pedido):
        pass

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(historico_model, "listar_pedidos_do_cliente", listar)
    monkeypatch.setattr(evento_model, "listar_solicitacoes_do_cliente", nenhuma)
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", nada)

    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    # só o pedido 10003 tem o formulário de cancelar
    assert texto.count("Cancelar pedido") == 1
    assert 'action="/pedido/10003/cancelar"' in texto
    assert 'action="/pedido/10002/cancelar"' not in texto
    assert 'action="/pedido/10001/cancelar"' not in texto
