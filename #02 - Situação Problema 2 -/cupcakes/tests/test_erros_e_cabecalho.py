import os
from app import app
from models import carrinho_model

# testes das páginas de erro em português (item 4) e do cabeçalho novo (itens 2, 5 e 7)

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

def carrinho_com_3_itens(id_cliente, id_sessao):
    return 3

def contador_zero(id_cliente, id_sessao):
    return 0


# páginas de erro (item 4) 

def test_pagina_que_nao_existe_mostra_erro_em_portugues():
    navegador = pegar_navegador()
    resposta = navegador.get("/essa-pagina-nao-existe")
    texto = pegar_texto(resposta)
    # o código de status continua 404 (o navegador e o google precisam saber que não existe)
    assert resposta.status_code == 404
    assert "Página não encontrada" in texto
    # antes aparecia o texto em inglês do Flask
    assert "Not Found" not in texto
    assert "The requested URL" not in texto

def test_pagina_de_erro_tem_botao_voltar_e_link_pra_vitrine():
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.get("/essa-pagina-nao-existe"))
    assert "Voltar" in texto
    assert "history.back()" in texto
    assert 'href="/"' in texto
    assert "Ir para a vitrine" in texto

def test_pagina_de_erro_usa_o_mesmo_estilo_do_site():
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.get("/essa-pagina-nao-existe"))
    assert "/static/css/style.css" in texto
    assert "Cupcakes" in texto

def test_arquivo_estatico_que_nao_existe_tambem_da_404():
    navegador = pegar_navegador()
    resposta = navegador.get("/static/js/nao_existe.js")
    assert resposta.status_code == 404

def test_pagina_de_erro_nao_depende_do_banco(monkeypatch):
    # se o banco caiu, a página de erro tem que abrir mesmo assim (ela não conta o carrinho)
    def erro_de_mentira(*args):
        raise Exception("o banco caiu (de mentira)")

    monkeypatch.setattr(carrinho_model, "contar_itens", erro_de_mentira)
    navegador = pegar_navegador()
    resposta = navegador.get("/essa-pagina-nao-existe")
    assert resposta.status_code == 404
    assert "Página não encontrada" in pegar_texto(resposta)

def test_metodo_nao_permitido_mostra_erro_em_portugues():
    # /login só aceita get e post, então o delete cai no erro 405
    navegador = pegar_navegador()
    resposta = navegador.delete("/login")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 405
    assert "Ação não permitida" in texto
    assert "Method Not Allowed" not in texto

def test_erro_interno_mostra_pagina_em_portugues_sem_mostrar_o_erro(monkeypatch):
    # força uma tela a quebrar de verdade. Com TESTING ligado o flask deixa o erro subir,
    # então aqui eu desligo só nesse teste (o monkeypatch liga de novo no fim)
    def quebrar():
        raise Exception("segredo do erro: senha=123")

    monkeypatch.setitem(app.config, "TESTING", False)
    monkeypatch.setitem(app.view_functions, "vitrine.vitrine", quebrar)
    navegador = app.test_client()
    resposta = navegador.get("/")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 500
    assert "Algo deu errado" in texto
    # o detalhe do erro não pode vazar pra tela
    assert "segredo do erro" not in texto
    assert "Traceback" not in texto
    assert "Internal Server Error" not in texto


# cabeçalho: um arquivo só (_topo.html) 

TELAS_COM_O_TOPO_COMPLETO = [
    "acompanhar_busca", "acompanhar_pedido", "carrinho", "checkout", "detalhe", "endereco_form",
    "evento_enviado", "evento_form", "meus_pedidos", "pagamento", "pedido_confirmado", "perfil", "vitrine",
]

def test_todas_as_telas_puxam_o_cabecalho_do_arquivo_unico():
    for nome in TELAS_COM_O_TOPO_COMPLETO:
        codigo = open("templates/" + nome + ".html", encoding="utf-8").read()
        assert '{% include "_topo.html" %}' in codigo, nome
        # e não sobrou cabeçalho copiado (senão a mudança não aparece nessa tela)
        assert 'class="topo"' not in codigo, nome
        assert "🛒" not in codigo, nome


# cabeçalho do visitante (item 2) 

def test_visitante_ve_o_link_acompanhar_pedido_no_topo(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert "Visitante" in texto
    assert 'href="/acompanhar/ultimo"' in texto
    assert "Acompanhar pedido" in texto

def test_visitante_nao_ve_meus_pedidos_nem_meu_perfil(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert 'href="/meus-pedidos"' not in texto
    assert "Meu perfil" not in texto

def test_cliente_ve_meus_pedidos_e_nao_ve_acompanhar_pedido(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert "Olá, Ana Teste" in texto
    assert 'href="/meus-pedidos"' in texto
    assert 'href="/acompanhar/ultimo"' not in texto


# carrinho com ícone e número num círculo (item 7) 

def test_carrinho_do_topo_tem_icone_desenhado_e_nao_emoji(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", carrinho_com_3_itens)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert "icone-carrinho" in texto
    assert "<svg" in texto
    assert "🛒" not in texto
    assert 'aria-label="Carrinho, 3 itens"' in texto
    assert 'qtd-carrinho">3<' in texto

def test_o_numero_do_carrinho_tem_cor_diferente_do_fundo_do_topo():
    css = open("public/static/css/style.css", encoding="utf-8").read()
    # o topo é rosa (#e75480) e o círculo do número é amarelo
    pedaco = css[css.index(".qtd-carrinho {"):]
    pedaco = pedaco[:pedaco.index("}")]
    assert "background-color: #ffd23f" in pedaco
    assert "border-radius" in pedaco

def test_icone_do_carrinho_e_maior_que_o_emoji_antigo():
    # o ícone é um svg de 30 pixels e a área de toque do link é de pelo menos 44 pixels
    codigo = open("templates/_topo.html", encoding="utf-8").read()
    assert 'width="30" height="30"' in codigo
    css = open("public/static/css/style.css", encoding="utf-8").read()
    pedaco = css[css.index(".link-carrinho {"):]
    pedaco = pedaco[:pedaco.index("}")]
    assert "height: 44px" in pedaco


# barra de baixo ("ilha") no celular (item 5) 

def test_visitante_tem_a_barra_de_baixo_com_vitrine_acompanhar_e_entrar(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert 'class="barra-ilha"' in texto
    assert "Vitrine" in texto
    assert "Acompanhar" in texto
    assert "Entrar" in texto

def test_cliente_tem_a_barra_de_baixo_com_pedidos_perfil_e_sair(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/acompanhar"))
    barra = texto[texto.index('class="barra-ilha"'):]
    assert "Pedidos" in barra
    assert "Perfil" in barra
    assert "Sair" in barra
    assert 'href="/meus-pedidos"' in barra

def test_barra_marca_a_tela_onde_a_pessoa_esta(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/acompanhar"))
    barra = texto[texto.index('class="barra-ilha"'):]
    # na tela de acompanhar, o item "Acompanhar" é o que fica marcado
    assert barra.count("item-ilha-ativo") == 1
    marcado = barra[barra.index("item-ilha-ativo"):]
    assert "Acompanhar" in marcado[:200]

def test_css_esconde_os_links_do_topo_no_celular_e_a_barra_no_computador():
    css = open("public/static/css/style.css", encoding="utf-8").read()
    # os links do topo começam escondidos (celular) e aparecem a partir de 768 pixels
    assert ".links-topo {\r\n    display: none;" in css or ".links-topo {\n    display: none;" in css
    # a barra de baixo some a partir de 768 pixels
    ultimo_bloco = css[css.rindex("@media (min-width: 768px)"):]
    assert ".barra-ilha" in ultimo_bloco
    assert "display: none" in ultimo_bloco
    # no celular o conteúdo ganha espaço embaixo, pra barra não tapar o fim da página
    assert "@media (max-width: 767px)" in css
