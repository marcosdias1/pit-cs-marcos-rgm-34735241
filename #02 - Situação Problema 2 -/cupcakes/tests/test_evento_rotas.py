# testes das rotas do orçamento de evento (cartão 08)

from datetime import date, timedelta
from app import app
from models import carrinho_model
from models import email_simulado
from models import evento_model
from models import evento_regras
from models import pedido_model
from models import produto_model


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

def contador_zero(id_cliente, id_sessao):
    return 0


# função que dá erro de propósito (o * faz ela aceitar qualquer quantidade de argumentos)
def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")


# uma data que vale (15 dias pra frente, sempre de acordo com o dia de hoje)
def data_boa():
    return (date.today() + timedelta(days=15)).isoformat()


# o formulário certo
def formulario(**trocas):
    dados = {"nome": "Ana Teste", "email": "Ana@Gmail.com ", "celular": "(11) 90000-1111",
             "data": data_boa(), "quantidade": "50", "tema": "Aniversário", "observacoes": "Sem amendoim"}
    for chave in trocas:
        dados[chave] = trocas[chave]
    return dados


# troca as funções do banco e do e-mail pelas de mentira
# recentes: quantos pedidos esse e-mail já mandou hoje
# devolve um dicionário com o que foi guardado e os e-mails enviados
def preparar(monkeypatch, recentes=0):
    feito = {"criados": [], "emails": []}

    def contar(email):
        feito["consultas"] = email
        return recentes

    def criar(id_cliente, campos):
        feito["criados"].append((id_cliente, campos))
        return 12

    def enviar(destino, assunto, texto):
        feito["emails"].append({"destino": destino, "assunto": assunto, "texto": texto})

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(evento_model, "contar_solicitacoes_recentes", contar)
    monkeypatch.setattr(evento_model, "criar_solicitacao", criar)
    monkeypatch.setattr(email_simulado, "enviar", enviar)
    return feito


# a tela 

def test_visitante_sem_sessao_abre_a_tela(monkeypatch):
    preparar(monkeypatch)
    navegador = pegar_navegador()
    resposta = navegador.get("/evento")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Orçamento para eventos" in texto
    assert 'name="quantidade"' in texto
    assert "30 cupcakes" in texto

def test_tela_limita_as_datas_no_calendario(monkeypatch):
    preparar(monkeypatch)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.get("/evento"))
    primeira = (date.today() + timedelta(days=3)).isoformat()
    assert 'min="' + primeira + '"' in texto

def test_visitante_comeca_com_o_formulario_vazio(monkeypatch):
    preparar(monkeypatch)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/evento"))
    assert 'value="Ana Teste"' not in texto

def test_cliente_comeca_com_os_proprios_dados(monkeypatch):
    preparar(monkeypatch)
    contato = {"nome": "Ana Teste", "email": "ana@gmail.com", "celular": "11900001111"}
    monkeypatch.setattr(pedido_model, "buscar_contato_do_cliente", lambda id_cliente: contato)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/evento"))
    assert 'value="Ana Teste"' in texto
    assert 'value="ana@gmail.com"' in texto
    assert 'value="(11) 90000-1111"' in texto

def test_erro_ao_buscar_o_contato_nao_derruba_a_tela(monkeypatch):
    preparar(monkeypatch)
    monkeypatch.setattr(pedido_model, "buscar_contato_do_cliente", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/evento")
    assert resposta.status_code == 200


# enviar o pedido 

def test_pedido_certo_e_guardado_e_manda_pra_tela_de_enviado(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = entrar_como_visitante()
    resposta = navegador.post("/evento", data=formulario())
    assert resposta.status_code == 302
    assert "/evento/enviado" in resposta.headers["Location"]
    assert len(feito["criados"]) == 1

def test_visitante_guarda_sem_id_de_cliente(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = entrar_como_visitante()
    navegador.post("/evento", data=formulario())
    assert feito["criados"][0][0] is None

def test_cliente_guarda_com_o_proprio_id(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = entrar_como_cliente()
    navegador.post("/evento", data=formulario())
    assert feito["criados"][0][0] == 7

def test_dados_gravados_ja_vao_limpos(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = pegar_navegador()
    navegador.post("/evento", data=formulario())
    campos = feito["criados"][0][1]
    # e-mail em minúsculas e sem espaço, celular só com números, quantidade número, data de verdade
    assert campos["email"] == "ana@gmail.com"
    assert campos["celular"] == "11900001111"
    assert campos["quantidade"] == 50
    assert campos["data_evento"] == date.today() + timedelta(days=15)
    assert campos["tema"] == "Aniversário"
    assert campos["observacoes"] == "Sem amendoim"

def test_tema_e_observacoes_vazios_viram_nada_no_banco(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = pegar_navegador()
    navegador.post("/evento", data=formulario(tema="", observacoes=""))
    campos = feito["criados"][0][1]
    assert campos["tema"] is None
    assert campos["observacoes"] is None

def test_manda_e_mail_pra_loja_e_pra_quem_pediu(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = pegar_navegador()
    navegador.post("/evento", data=formulario())
    destinos = []
    for email in feito["emails"]:
        destinos.append(email["destino"])
    assert destinos == [evento_regras.EMAIL_DA_LOJA, "ana@gmail.com"]
    assert "#12" in feito["emails"][0]["assunto"]
    assert "#12" in feito["emails"][1]["assunto"]

def test_defeito_no_envio_do_e_mail_nao_desfaz_o_pedido(monkeypatch):
    feito = preparar(monkeypatch)
    monkeypatch.setattr(email_simulado, "enviar", erro_de_mentira)
    navegador = pegar_navegador()
    resposta = navegador.post("/evento", data=formulario())
    assert resposta.status_code == 302
    assert "/evento/enviado" in resposta.headers["Location"]
    assert len(feito["criados"]) == 1

def test_tela_de_enviado_mostra_o_protocolo_e_o_email(monkeypatch):
    preparar(monkeypatch)
    navegador = pegar_navegador()
    resposta = navegador.post("/evento", data=formulario(), follow_redirects=True)
    texto = pegar_texto(resposta)
    assert "Pedido de orçamento enviado!" in texto
    assert "#12" in texto
    assert "ana@gmail.com" in texto
    assert "2 dias úteis" in texto

def test_tela_de_enviado_sem_ter_enviado_volta_pro_formulario(monkeypatch):
    preparar(monkeypatch)
    navegador = pegar_navegador()
    resposta = navegador.get("/evento/enviado")
    assert resposta.status_code == 302
    assert "/evento" in resposta.headers["Location"]

# erros 

def test_abaixo_de_30_nao_grava_e_manda_comprar_pelo_carrinho(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/evento", data=formulario(quantidade="20")))
    assert "mínimo é de 30" in texto
    assert "é só comprar pelo carrinho" in texto
    assert feito["criados"] == []
    assert feito["emails"] == []

def test_com_30_nao_aparece_o_aviso_do_carrinho(monkeypatch):
    preparar(monkeypatch)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/evento", data=formulario(quantidade="30"), follow_redirects=True))
    assert "é só comprar pelo carrinho" not in texto

def test_pedido_errado_mostra_os_erros_e_nao_grava(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = pegar_navegador()
    dados = formulario(nome="", email="semarroba", celular="1", data="", quantidade="abc")
    texto = pegar_texto(navegador.post("/evento", data=dados))
    assert "Informe seu nome." in texto
    assert "E-mail inválido" in texto
    assert "Celular inválido" in texto
    assert "Informe a data do evento." in texto
    assert "Digite só números" in texto
    assert feito["criados"] == []

def test_pedido_errado_nem_pergunta_pro_banco(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = pegar_navegador()
    navegador.post("/evento", data=formulario(nome=""))
    assert "consultas" not in feito

def test_data_que_ja_passou_e_recusada(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = pegar_navegador()
    ontem = (date.today() - timedelta(days=1)).isoformat()
    texto = pegar_texto(navegador.post("/evento", data=formulario(data=ontem)))
    assert "dias de antecedência" in texto
    assert feito["criados"] == []

def test_erro_nao_apaga_o_que_a_pessoa_digitou(monkeypatch):
    preparar(monkeypatch)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/evento", data=formulario(quantidade="5", tema="Casamento")))
    assert 'value="Ana Teste"' in texto
    assert 'value="5"' in texto
    assert 'value="Casamento"' in texto
    assert "Sem amendoim" in texto

def test_limite_de_pedidos_por_dia(monkeypatch):
    feito = preparar(monkeypatch, recentes=3)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/evento", data=formulario()))
    assert "já mandou 3 pedidos hoje" in texto
    assert feito["criados"] == []
    assert feito["emails"] == []

def test_ate_2_pedidos_no_dia_ainda_passa(monkeypatch):
    feito = preparar(monkeypatch, recentes=2)
    navegador = pegar_navegador()
    navegador.post("/evento", data=formulario())
    assert len(feito["criados"]) == 1

def test_o_limite_olha_o_email_em_minusculas(monkeypatch):
    feito = preparar(monkeypatch)
    navegador = pegar_navegador()
    navegador.post("/evento", data=formulario())
    assert feito["consultas"] == "ana@gmail.com"

def test_erro_no_banco_ao_gravar(monkeypatch):
    feito = preparar(monkeypatch)
    monkeypatch.setattr(evento_model, "criar_solicitacao", erro_de_mentira)
    navegador = pegar_navegador()
    resposta = navegador.post("/evento", data=formulario())
    assert resposta.status_code == 200
    assert "Não foi possível enviar o pedido agora" in pegar_texto(resposta)
    assert feito["emails"] == []

def test_erro_no_banco_ao_contar_os_pedidos_do_dia(monkeypatch):
    feito = preparar(monkeypatch)
    monkeypatch.setattr(evento_model, "contar_solicitacoes_recentes", erro_de_mentira)
    navegador = pegar_navegador()
    resposta = navegador.post("/evento", data=formulario())
    assert resposta.status_code == 200
    assert "Não foi possível enviar o pedido agora" in pegar_texto(resposta)
    assert feito["criados"] == []


# aviso na vitrine 

def test_vitrine_tem_o_aviso_de_evento(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(produto_model, "listar_categorias", lambda *args: [])
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", lambda *args, **kwargs: [])
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/"))
    assert 'href="/evento"' in texto
    assert "Peça um orçamento a partir de 30 cupcakes" in texto
