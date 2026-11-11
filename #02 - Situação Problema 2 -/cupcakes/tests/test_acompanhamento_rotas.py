from decimal import Decimal
from datetime import datetime, timedelta
from app import app
from models import carrinho_model
from models import pedido_model

# testes das rotas do acompanhamento do pedido: tela, json de status e busca por número e e-mail
# esses testes NÃO mexem no banco: o monkeypatch troca as funções do model por funções de mentira


# o pedido de mentira foi confirmado nesse horário (fixo, pra a previsão dar sempre 40 minutos)
CONFIRMADO_EM = datetime(2026, 11, 8, 18, 0, 0)


# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
    return navegador

def entrar_como_visitante():
    navegador = pegar_navegador()
    navegador.get("/visitante")
    return navegador

# visitante que criou o pedido 50 (é o pedido de mentira dos testes)
def entrar_como_visitante_com_pedido():
    navegador = entrar_como_visitante()
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


# dados de mentira 

# o pedido 50 (número 10050). id_cliente None é pedido de visitante
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


# o histórico do pedido até o status que eu quiser
def historico_ate(status):
    historico = [{"status": "CONFIRMADO", "data_hora": CONFIRMADO_EM}]
    if status in ["EM_PREPARO", "SAIU_PARA_ENTREGA", "ENTREGUE"]:
        historico.append({"status": "EM_PREPARO", "data_hora": CONFIRMADO_EM + timedelta(seconds=30)})
    if status in ["SAIU_PARA_ENTREGA", "ENTREGUE"]:
        historico.append({"status": "SAIU_PARA_ENTREGA", "data_hora": CONFIRMADO_EM + timedelta(seconds=90)})
    if status == "ENTREGUE":
        historico.append({"status": "ENTREGUE", "data_hora": CONFIRMADO_EM + timedelta(seconds=150)})
    return historico

def itens_do_pedido_de_mentira(id_pedido):
    lista = []
    lista.append({"nome": "Chocolate", "quantidade": 2, "subtotal_texto": "R$ 24,00"})
    return lista

def contador_zero(id_cliente, id_sessao):
    return 0


# função que dá erro de propósito (o * faz ela aceitar qualquer quantidade de argumentos)
def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")


# troca o "buscar pedido" por uma função que sempre devolve o pedido que eu quiser
def usar_pedido(monkeypatch, pedido):
    def buscar(numero):
        return pedido

    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", buscar)


# troca as funções do banco pelas de mentira
# devolve a lista de chamadas da "atualização do status", pra conferir se a tela chamou
def preparar(monkeypatch, status, id_cliente=None):
    chamadas = []

    def atualizar(id_pedido):
        chamadas.append(id_pedido)

    def historico(id_pedido):
        return historico_ate(status)

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", atualizar)
    monkeypatch.setattr(pedido_model, "listar_historico_do_pedido", historico)
    monkeypatch.setattr(pedido_model, "listar_itens_do_pedido", itens_do_pedido_de_mentira)
    usar_pedido(monkeypatch, pedido_de_mentira(id_cliente, status))
    return chamadas


# TELA DE ACOMPANHAMENTO: acesso 

def test_acompanhar_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/pedido/10050")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_visitante_acompanha_o_proprio_pedido(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pedido/10050")
    assert resposta.status_code == 200
    assert "Pedido #10050" in pegar_texto(resposta)

def test_cliente_acompanha_o_proprio_pedido(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO", 7)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/pedido/10050")
    assert resposta.status_code == 200

def test_cliente_nao_acompanha_pedido_de_outro_cliente(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO", 8)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/pedido/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_cliente_nao_acompanha_pedido_de_visitante(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/pedido/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_visitante_nao_acompanha_pedido_de_cliente(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO", 7)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_visitante_nao_acompanha_pedido_que_nao_e_dele(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 51
    texto = pegar_texto(navegador.get("/pedido/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_visitante_com_pedido_liberado_pela_busca_acompanha(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedidos_liberados"] = [50]
    resposta = navegador.get("/pedido/10050")
    assert resposta.status_code == 200

def test_pedido_esperando_pagamento_volta_pro_pagamento(monkeypatch):
    preparar(monkeypatch, "AGUARDANDO_PAGAMENTO")
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pedido/10050")
    assert resposta.status_code == 302
    assert "/pagamento/10050" in resposta.headers["Location"]

def test_pedido_cancelado_nao_tem_acompanhamento(monkeypatch):
    preparar(monkeypatch, "CANCELADO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050", follow_redirects=True))
    assert "Esse pedido foi cancelado" in texto

def test_erro_no_banco_ao_buscar_o_pedido(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", erro_de_mentira)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050", follow_redirects=True))
    assert "Não foi possível abrir o pedido agora" in texto


# TELA DE ACOMPANHAMENTO: o que aparece em cada etapa 

def test_tela_logo_depois_da_confirmacao(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "Recebemos o seu pedido" in texto
    assert "Previsão de entrega: cerca de 40 min." in texto
    # as 4 etapas aparecem
    assert ">Pedido confirmado<" in texto
    assert ">Em preparo<" in texto
    assert ">Saiu para entrega<" in texto
    assert ">Entregue<" in texto

def test_tela_em_preparo_atualiza_a_estimativa(monkeypatch):
    preparar(monkeypatch, "EM_PREPARO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "Estamos preparando e embalando os seus cupcakes." in texto
    assert "Previsão de entrega: cerca de 30 min." in texto

def test_tela_saiu_para_entrega(monkeypatch):
    preparar(monkeypatch, "SAIU_PARA_ENTREGA")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "O seu pedido saiu para entrega" in texto
    assert "Previsão de entrega: cerca de 15 min." in texto

def test_tela_entregue(monkeypatch):
    preparar(monkeypatch, "ENTREGUE")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "Pedido entregue. Bom apetite!" in texto
    assert "Entregue " in texto
    assert "às 18:02" in texto
    assert "Previsão de entrega" not in texto
    # o javascript não precisa mais perguntar
    assert 'data-entregue="1"' in texto

def test_tela_ainda_nao_entregue_deixa_o_javascript_perguntar(monkeypatch):
    preparar(monkeypatch, "EM_PREPARO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert 'data-entregue="0"' in texto
    assert 'data-numero="10050"' in texto

def test_tela_marca_so_uma_etapa_como_atual(monkeypatch):
    preparar(monkeypatch, "EM_PREPARO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert texto.count("etapa-atual") == 1
    assert texto.count('aria-current="step"') == 1
    assert texto.count("etapa-feito") == 1
    assert texto.count("etapa-proximo") == 2

def test_tela_chama_a_atualizacao_do_status(monkeypatch):
    chamadas = preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    navegador.get("/pedido/10050")
    # chamou a atualização com o id do pedido
    assert chamadas == [50]

def test_tela_mostra_os_itens_e_o_total_do_pedido(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050"))
    assert "2x Chocolate" in texto
    assert "R$ 36,50" in texto

def test_erro_ao_atualizar_o_status_a_tela_abre_com_aviso(monkeypatch):
    preparar(monkeypatch, "EM_PREPARO")
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", erro_de_mentira)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pedido/10050")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Não foi possível atualizar o status agora" in texto
    # mostra o último status que o banco tinha
    assert "Em preparo" in texto

def test_erro_ao_listar_os_itens_a_tela_abre_mesmo_assim(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    monkeypatch.setattr(pedido_model, "listar_itens_do_pedido", erro_de_mentira)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pedido/10050")
    assert resposta.status_code == 200
    assert "Pedido #10050" in pegar_texto(resposta)


# JSON DE STATUS (o javascript usa) 


def test_api_sem_entrar_devolve_401():
    navegador = pegar_navegador()
    resposta = navegador.get("/api/pedido/10050/status")
    assert resposta.status_code == 401
    assert "erro" in resposta.get_json()

def test_api_de_pedido_de_outra_pessoa_devolve_404(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO", 8)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/api/pedido/10050/status")
    assert resposta.status_code == 404
    assert resposta.get_json()["erro"] == "Pedido não encontrado."

def test_api_de_pedido_que_nao_existe_devolve_404(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    usar_pedido(monkeypatch, None)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/api/pedido/10050/status")
    assert resposta.status_code == 404

def test_api_devolve_o_status_as_etapas_e_a_previsao(monkeypatch):
    preparar(monkeypatch, "EM_PREPARO")
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/api/pedido/10050/status")
    dados = resposta.get_json()
    assert resposta.status_code == 200
    assert dados["numero"] == 10050
    assert dados["status"] == "EM_PREPARO"
    assert dados["status_texto"] == "Em preparo"
    assert dados["previsao"] == "Previsão de entrega: cerca de 30 min."
    assert dados["entregue"] == False
    assert len(dados["etapas"]) == 4
    assert dados["etapas"][1]["estado"] == "atual"

def test_api_chama_a_atualizacao_do_status(monkeypatch):
    chamadas = preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    navegador.get("/api/pedido/10050/status")
    assert chamadas == [50]

def test_api_avisa_quando_o_pedido_foi_entregue(monkeypatch):
    preparar(monkeypatch, "ENTREGUE")
    navegador = entrar_como_visitante_com_pedido()
    dados = navegador.get("/api/pedido/10050/status").get_json()
    assert dados["entregue"] == True
    assert dados["previsao"].startswith("Entregue ")

def test_api_de_pedido_esperando_pagamento_devolve_409(monkeypatch):
    preparar(monkeypatch, "AGUARDANDO_PAGAMENTO")
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/api/pedido/10050/status")
    assert resposta.status_code == 409

def test_api_com_erro_no_banco_devolve_500(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", erro_de_mentira)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/api/pedido/10050/status")
    assert resposta.status_code == 500
    assert "erro" in resposta.get_json()


# BUSCAR PEDIDO POR NÚMERO E E-MAIL (visitante) 

def test_tela_de_busca_abre_mesmo_sem_ter_entrado():
    navegador = pegar_navegador()
    resposta = navegador.get("/acompanhar")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert 'name="numero"' in texto
    assert 'name="email"' in texto

def test_busca_certa_libera_o_pedido_e_abre_o_acompanhamento(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "visita@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados)
    assert resposta.status_code == 302
    assert "/pedido/10050" in resposta.headers["Location"]
    with navegador.session_transaction() as sessao:
        assert sessao["pedidos_liberados"] == [50]
        # quem nunca tinha entrado vira visitante
        assert sessao["tipo"] == "visitante"

def test_depois_da_busca_a_tela_do_pedido_abre(monkeypatch):
    preparar(monkeypatch, "EM_PREPARO")
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "visita@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados, follow_redirects=True)
    texto = pegar_texto(resposta)
    assert "Pedido #10050" in texto
    assert "Em preparo" in texto

def test_busca_aceita_email_em_maiusculas_com_espacos(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "  VISITA@Gmail.com "}
    resposta = navegador.post("/acompanhar", data=dados)
    assert resposta.status_code == 302

def test_busca_aceita_o_numero_com_jogo_da_velha(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = pegar_navegador()
    dados = {"numero": "#10050", "email": "visita@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados)
    assert resposta.status_code == 302

def test_busca_com_email_errado_nao_libera_nada(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "outra.pessoa@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados)
    assert resposta.status_code == 200
    assert "Não encontramos um pedido com esse número e e-mail." in pegar_texto(resposta)
    with navegador.session_transaction() as sessao:
        assert "pedidos_liberados" not in sessao

def test_busca_nao_acha_pedido_de_cliente_nem_com_o_email_certo(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO", 7)
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "visita@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados)
    assert resposta.status_code == 200
    # a mesma mensagem de quando o pedido não existe (ninguém descobre quais pedidos existem)
    assert "Não encontramos um pedido com esse número e e-mail." in pegar_texto(resposta)

def test_busca_nao_acha_pedido_que_ainda_nao_foi_pago(monkeypatch):
    preparar(monkeypatch, "AGUARDANDO_PAGAMENTO")
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "visita@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados)
    assert "Não encontramos um pedido com esse número e e-mail." in pegar_texto(resposta)

def test_busca_nao_acha_pedido_cancelado(monkeypatch):
    preparar(monkeypatch, "CANCELADO")
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "visita@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados)
    assert "Não encontramos um pedido com esse número e e-mail." in pegar_texto(resposta)

def test_busca_de_pedido_que_nao_existe(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    usar_pedido(monkeypatch, None)
    navegador = pegar_navegador()
    dados = {"numero": "99999", "email": "visita@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados)
    assert "Não encontramos um pedido com esse número e e-mail." in pegar_texto(resposta)

def test_busca_com_dados_invalidos_nem_pergunta_pro_banco(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    consultas = []

    def buscar(numero):
        consultas.append(numero)
        return None

    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", buscar)
    navegador = pegar_navegador()
    dados = {"numero": "abc", "email": "semarroba"}
    texto = pegar_texto(navegador.post("/acompanhar", data=dados))
    assert "Digite só os números do pedido" in texto
    assert "E-mail inválido" in texto
    assert consultas == []

def test_busca_com_numero_gigante_nem_pergunta_pro_banco(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    consultas = []

    def buscar(numero):
        consultas.append(numero)
        return None

    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", buscar)
    navegador = pegar_navegador()
    dados = {"numero": "12345678901234567890", "email": "visita@gmail.com"}
    texto = pegar_texto(navegador.post("/acompanhar", data=dados))
    assert "Digite só os números do pedido" in texto
    assert consultas == []

def test_busca_mantem_o_que_a_pessoa_digitou(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "outra.pessoa@gmail.com"}
    texto = pegar_texto(navegador.post("/acompanhar", data=dados))
    assert 'value="10050"' in texto
    assert 'value="outra.pessoa@gmail.com"' in texto

def test_busca_com_erro_no_banco_mostra_mensagem(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", erro_de_mentira)
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "visita@gmail.com"}
    resposta = navegador.post("/acompanhar", data=dados)
    assert resposta.status_code == 200
    assert "Não foi possível buscar o pedido agora" in pegar_texto(resposta)

def test_busca_guarda_so_os_10_ultimos_pedidos_liberados(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = pegar_navegador()
    with navegador.session_transaction() as sessao:
        sessao["tipo"] = "visitante"
        sessao["pedidos_liberados"] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    dados = {"numero": "10050", "email": "visita@gmail.com"}
    navegador.post("/acompanhar", data=dados)
    with navegador.session_transaction() as sessao:
        assert len(sessao["pedidos_liberados"]) == 10
        assert sessao["pedidos_liberados"][-1] == 50
        assert sessao["pedidos_liberados"][0] == 2

def test_buscar_o_mesmo_pedido_duas_vezes_nao_repete_na_lista(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = pegar_navegador()
    dados = {"numero": "10050", "email": "visita@gmail.com"}
    navegador.post("/acompanhar", data=dados)
    navegador.post("/acompanhar", data=dados)
    with navegador.session_transaction() as sessao:
        assert sessao["pedidos_liberados"] == [50]


# LINKS PRA ESSAS TELAS 

def test_tela_de_login_tem_o_link_pra_acompanhar_um_pedido():
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.get("/login"))
    assert 'href="/acompanhar"' in texto
    assert "Acompanhar um pedido" in texto

def test_pedido_confirmado_tem_o_botao_de_acompanhar(monkeypatch):
    preparar(monkeypatch, "CONFIRMADO")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050/confirmado"))
    assert 'href="/pedido/10050"' in texto
    assert "Acompanhar pedido" in texto
