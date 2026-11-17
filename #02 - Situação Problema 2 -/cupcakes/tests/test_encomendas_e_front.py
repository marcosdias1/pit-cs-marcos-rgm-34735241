from datetime import date, datetime
from app import app
from models import carrinho_model
from models import historico_model
from models import pedido_model
from models import evento_model

# testes das encomendas de evento em "Meus pedidos" (item 3)
# e dos arquivos de front que o pytest consegue conferir (olhinho da senha, CEP)
# o JavaScript em si não roda no pytest, então aqui eu só confiro o que está escrito nos arquivos


# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
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

def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")

def nada(id_pedido):
    pass


# troca as funções do banco da tela "Meus pedidos"
# devolve a lista com o que cada função foi chamada
def preparar(monkeypatch, pedidos, encomendas):
    chamadas = []

    def listar_pedidos(id_cliente, limite):
        return pedidos

    def listar_encomendas(id_cliente, limite):
        chamadas.append((id_cliente, limite))
        return encomendas

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(historico_model, "listar_pedidos_do_cliente", listar_pedidos)
    monkeypatch.setattr(evento_model, "listar_solicitacoes_do_cliente", listar_encomendas)
    monkeypatch.setattr(pedido_model, "atualizar_status_simulado", nada)
    return chamadas

def encomenda_de_mentira(numero, status, status_texto):
    encomenda = {}
    encomenda["numero"] = numero
    encomenda["status"] = status
    encomenda["status_texto"] = status_texto
    encomenda["data_evento_texto"] = "30/11/2026"
    encomenda["resumo"] = "50 cupcakes, tema Unicórnio"
    encomenda["data_texto"] = "08/11/2026 às 18:05"
    return encomenda


#  item 3: encomendas em Meus pedidos 

def test_encomenda_do_cliente_aparece_em_meus_pedidos(monkeypatch):
    chamadas = preparar(monkeypatch, [], [encomenda_de_mentira(12, "RECEBIDA", "Recebida, aguardando o orçamento")])
    navegador = entrar_como_cliente()
    resposta = navegador.get("/meus-pedidos")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Minhas encomendas para eventos" in texto
    assert "protocolo #12" in texto
    assert "Recebida, aguardando o orçamento" in texto
    assert "50 cupcakes, tema Unicórnio" in texto
    assert "30/11/2026" in texto
    # buscou as encomendas do cliente 7
    assert chamadas[0][0] == 7

def test_mostra_varias_encomendas_com_a_situacao_de_cada_uma(monkeypatch):
    lista = [encomenda_de_mentira(13, "ORCADA", "Orçamento enviado"),
             encomenda_de_mentira(12, "CANCELADA", "Cancelada")]
    preparar(monkeypatch, [], lista)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert "protocolo #13" in texto
    assert "protocolo #12" in texto
    assert "pedido-status-orcada" in texto
    assert "pedido-status-cancelada" in texto

def test_encomendas_aparecem_junto_com_os_pedidos_e_depois_deles(monkeypatch):
    pedido = {}
    pedido["id"] = 5
    pedido["numero"] = 10005
    pedido["status"] = "ENTREGUE"
    pedido["status_texto"] = "Entregue"
    pedido["total_texto"] = "R$ 36,50"
    pedido["data_texto"] = "08/11/2026 às 18:05"
    pedido["pode_acompanhar"] = True
    pedido["pode_cancelar"] = False
    pedido["itens"] = []
    pedido["itens_texto"] = "2x Chocolate"
    preparar(monkeypatch, [pedido], [encomenda_de_mentira(12, "RECEBIDA", "Recebida, aguardando o orçamento")])
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert "Pedido #10005" in texto
    assert texto.index("Pedido #10005") < texto.index("Minhas encomendas para eventos")

def test_sem_encomendas_a_parte_de_encomendas_nao_aparece(monkeypatch):
    preparar(monkeypatch, [], [])
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/meus-pedidos"))
    assert "Minhas encomendas para eventos" not in texto

def test_erro_nas_encomendas_nao_derruba_a_lista_de_pedidos(monkeypatch):
    preparar(monkeypatch, [], [])
    monkeypatch.setattr(evento_model, "listar_solicitacoes_do_cliente", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/meus-pedidos")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Você ainda não fez nenhum pedido." in texto
    assert "Não foi possível abrir as suas encomendas agora" in texto

def test_visitante_continua_sem_lista_de_encomendas(monkeypatch):
    # o orçamento pedido como visitante não tem lista (visitante não tem conta)
    chamadas = preparar(monkeypatch, [], [])
    navegador = pegar_navegador()
    navegador.get("/visitante")
    resposta = navegador.get("/meus-pedidos")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    assert chamadas == []

def test_tela_de_orcamento_enviado_aponta_pra_meus_pedidos_so_para_cliente():
    app.config["TESTING"] = True
    cliente = entrar_como_cliente()
    with cliente.session_transaction() as sessao:
        sessao["evento_enviado"] = {"numero": 12, "email": "ana@gmail.com"}
    # o carrinho é contado com o banco, então troca por uma função de mentira
    import pytest
    mp = pytest.MonkeyPatch()
    mp.setattr(carrinho_model, "contar_itens", contador_zero)
    try:
        texto = pegar_texto(cliente.get("/evento/enviado"))
        assert "Você também pode ver essa encomenda em" in texto

        visitante = pegar_navegador()
        visitante.get("/visitante")
        with visitante.session_transaction() as sessao:
            sessao["evento_enviado"] = {"numero": 13, "email": "visita@gmail.com"}
        texto = pegar_texto(visitante.get("/evento/enviado"))
        assert "Você também pode ver essa encomenda em" not in texto
    finally:
        mp.undo()


#  item 9: senha (o olho é o do próprio navegador) 
# o Marcos preferiu NÃO criar um botão próprio de mostrar a senha: fica o olho padrão do Edge
# então estes testes só garantem que ninguém colocou um botão por cima e que nada esconde o olho do navegador

def ler(caminho):
    return open(caminho, encoding="utf-8").read()

def test_os_campos_de_senha_continuam_simples():
    # o campo de senha é um input normal, sem botão próprio em volta
    for nome in ["login", "cadastro", "redefinir_senha"]:
        codigo = ler("templates/" + nome + ".html")
        assert 'type="password"' in codigo, nome
        assert "botao-olho" not in codigo, nome
        assert "caixa-senha" not in codigo, nome
        assert "senha.js" not in codigo, nome

def test_nao_existe_o_javascript_do_olhinho_proprio():
    import os
    assert os.path.exists("public/static/js/senha.js") == False

def test_o_css_nao_esconde_o_olho_do_navegador():
    # o Edge desenha o olho com o ::-ms-reveal. Se alguém colocar display: none nele, o olho some
    css = ler("public/static/css/style.css")
    assert "-ms-reveal" not in css
    assert "botao-olho" not in css


#  item 1: CEP 

def test_campo_de_cep_aceita_cep_com_ponto_e_traco_sem_cortar():
    # o cep com ponto e traço (01.001-000) tem 10 caracteres, e o campo cortava em 9
    for nome in ["cadastro", "checkout", "endereco_form"]:
        codigo = ler("templates/" + nome + ".html")
        assert 'id="cep" name="cep" placeholder="00000-000" maxlength="12"' in codigo, nome
        assert 'maxlength="9"' not in codigo, nome

def test_cep_js_esquece_o_ultimo_cep_quando_a_pessoa_apaga():
    codigo = ler("public/static/js/cep.js")
    # tem um trecho que zera o "último cep buscado" quando não tem 8 números
    trecho = codigo[codigo.index("if (cep.length != 8) {"):]
    trecho = trecho[:trecho.index("}")]
    assert 'ultimoCepBuscado = "";' in trecho

def test_cep_js_busca_de_novo_quando_o_endereco_foi_apagado():
    codigo = ler("public/static/js/cep.js")
    assert 'campoCidade.value != ""' in codigo
    assert "buscaEmAndamento" in codigo

def test_cep_js_deixa_o_cep_no_formato_certo_ao_sair_do_campo():
    codigo = ler("public/static/js/cep.js")
    assert "function arrumarCep()" in codigo
    assert 'addEventListener("blur", arrumarCep)' in codigo

def test_o_servidor_aceita_o_cep_digitado_de_qualquer_jeito():
    # o javascript limpa o cep, mas o servidor também precisa aceitar (quem desliga o javascript)
    from models import validacoes
    assert validacoes.validar_cep("01001000") == True
    assert validacoes.validar_cep("01001-000") == True
    assert validacoes.validar_cep("01.001-000") == True
    assert validacoes.validar_cep("01001 000") == True
    assert validacoes.validar_cep("01001-00") == False
    assert validacoes.validar_cep("0100100a") == False
