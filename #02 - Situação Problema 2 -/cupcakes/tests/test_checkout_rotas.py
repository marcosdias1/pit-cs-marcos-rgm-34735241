# testes das rotas do fechamento do pedido e do carrinho do visitante que acompanha o login

from decimal import Decimal
from datetime import date
from app import app
from models import carrinho_model
from models import cliente_model
from models import pedido_model
from models import produto_model
from models import frete


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


# dados de mentira 

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


# 2 chocolates (12,00 cada) e 1 calda (5,00) = subtotal de 29,00
def itens_com_cupcake(id_carrinho):
    lista = []
    lista.append(item_de_mentira(3, "Chocolate", "CUPCAKE", "12.00", 2, 50))
    lista.append(item_de_mentira(9, "Calda de chocolate", "ADICIONAL", "5.00", 1, 100))
    return lista

def itens_vazio(id_carrinho):
    return []

def itens_so_adicional(id_carrinho):
    return [item_de_mentira(9, "Calda de chocolate", "ADICIONAL", "5.00", 1, 100)]

def itens_sem_estoque(id_carrinho):
    return [item_de_mentira(3, "Chocolate", "CUPCAKE", "12.00", 1, 0)]

def itens_passando_do_estoque(id_carrinho):
    return [item_de_mentira(3, "Chocolate", "CUPCAKE", "12.00", 5, 3)]

def adicionais_nenhum(id_carrinho):
    return []

def carrinho_numero_1(id_cliente, id_sessao):
    return 1

def contador_zero(id_cliente, id_sessao):
    return 0

def endereco_nenhum(id_cliente):
    return None


# endereço da conta: na mesma cidade da loja, mas em outro bairro (frete de 7,50)
def endereco_da_conta(id_cliente):
    endereco = {}
    endereco["cep"] = "01001-000"
    endereco["rua"] = "Praça da Sé"
    endereco["numero"] = "100"
    endereco["bairro"] = "Bairro Inventado"
    endereco["cidade"] = frete.LOJA_CIDADE
    endereco["uf"] = frete.LOJA_UF
    return endereco

def contato_da_conta(id_cliente):
    return {"nome": "Ana Teste", "email": "ana@gmail.com", "celular": "11900000001"}

def sem_cupom(id_cliente, codigo, subtotal, hoje):
    return (None, "")   

def pegar_cupom(tipo, valor, codigo):
    cupom = {}
    cupom["id"] = 1
    cupom["id_cliente"] = None
    cupom["codigo"] = codigo
    cupom["tipo"] = tipo
    cupom["valor"] = Decimal(valor)
    cupom["valido_de"] = date(2026, 1, 1)
    cupom["valido_ate"] = date(2030, 12, 31)
    cupom["uso_unico"] = False
    cupom["primeira_compra"] = False
    cupom["ativo"] = True
    return cupom

# cupom de 10% (desconto de 2,90 em 29,00)
def cupom_de_10_por_cento(id_cliente, codigo, subtotal, hoje):
    return (pegar_cupom("PERCENTUAL", "10.00", "PROMO10"), "")

# cupom de 15 reais que entra sozinho (o desconto do cpf)
def cupom_do_cpf(id_cliente, codigo, subtotal, hoje):
    return (pegar_cupom("VALOR_FIXO", "15.00", "BEMVINDO15-7"), "")

def cupom_vencido(id_cliente, codigo, subtotal, hoje):
    return (None, "Esse cupom está vencido.")


# função que dá erro de propósito (o * faz ela aceitar qualquer quantidade de argumentos)
def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")


# troca as funções do banco pelas de mentira (carrinho com 29,00, sem cupom e sem endereço salvo)
def deixar_checkout_de_mentira(monkeypatch):
    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", carrinho_numero_1)
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_com_cupcake)
    monkeypatch.setattr(carrinho_model, "listar_adicionais", adicionais_nenhum)
    monkeypatch.setattr(pedido_model, "escolher_cupom", sem_cupom)
    monkeypatch.setattr(pedido_model, "buscar_endereco_principal", endereco_nenhum)
    monkeypatch.setattr(pedido_model, "buscar_contato_do_cliente", contato_da_conta)

def deixar_vitrine_de_mentira(monkeypatch):
    def categorias():
        return []

    def cupcakes(id_categoria, busca):
        return []

    monkeypatch.setattr(produto_model, "listar_categorias", categorias)
    monkeypatch.setattr(produto_model, "listar_cupcakes_filtrados", cupcakes)

# o que o visitante preenche: mesma cidade da loja, outro bairro (frete de 7,50)
def formulario_do_visitante():
    dados = {}
    dados["cep"] = "01001-000"
    dados["rua"] = "Praça da Sé"
    dados["numero"] = "100"
    dados["bairro"] = "Bairro Inventado"
    dados["cidade"] = frete.LOJA_CIDADE
    dados["uf"] = frete.LOJA_UF
    dados["nome"] = "Visitante Teste"
    dados["email"] = "visita@gmail.com"
    dados["celular"] = "(11) 90000-0001"
    dados["cupom"] = ""
    return dados


# acesso e carrinho 

def test_checkout_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/checkout")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_carrinho_tem_o_botao_de_fechar_pedido(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/carrinho"))
    assert 'href="/checkout"' in texto
    assert "Fechar pedido" in texto

def test_checkout_com_carrinho_vazio_volta_pro_carrinho(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_vazio)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/checkout")
    assert resposta.status_code == 302
    assert "/carrinho" in resposta.headers["Location"]

def test_checkout_so_com_adicional_pede_um_cupcake(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_so_adicional)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/checkout", follow_redirects=True))
    assert "Escolha pelo menos um cupcake" in texto

def test_checkout_com_item_sem_estoque_volta_pro_carrinho(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_sem_estoque)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/checkout", follow_redirects=True))
    assert "O item Chocolate está sem estoque" in texto

def test_checkout_com_quantidade_maior_que_o_estoque_volta_pro_carrinho(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_passando_do_estoque)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/checkout", follow_redirects=True))
    assert "Só temos 3 de Chocolate em estoque" in texto

def test_checkout_com_erro_no_banco_volta_pro_carrinho(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", erro_de_mentira)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/checkout", follow_redirects=True))
    assert "Não foi possível abrir o fechamento do pedido" in texto


# abrir a tela 

def test_visitante_ve_os_campos_de_contato_e_o_subtotal(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    resposta = navegador.get("/checkout")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert 'name="email"' in texto
    assert "R$ 29,00" in texto
    assert "informe o endereço" in texto
    # ao abrir a tela ainda não pode aparecer erro nenhum
    assert "CEP inválido" not in texto
    assert "Informe a rua" not in texto

def test_cliente_ve_o_endereco_da_conta_e_o_frete(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "buscar_endereco_principal", endereco_da_conta)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/checkout"))
    assert 'value="Praça da Sé"' in texto
    # o contato vem da conta, então não tem campo de e-mail
    assert "Ana Teste" in texto
    assert 'name="email"' not in texto
    # 29,00 + 7,50 de frete
    assert "R$ 7,50" in texto
    assert "R$ 36,50" in texto

def test_endereco_salvo_com_erro_no_banco_deixa_preencher_na_mao(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "buscar_endereco_principal", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/checkout")
    assert resposta.status_code == 200
    assert "Não foi possível buscar o seu endereço salvo" in pegar_texto(resposta)


# frete 

def test_frete_da_mesma_cidade(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.post("/checkout", data=formulario_do_visitante()))
    assert "R$ 7,50" in texto
    assert "Mesma cidade da loja" in texto
    assert "cerca de 40 min" in texto
    assert "R$ 36,50" in texto

def test_frete_de_outra_cidade_do_mesmo_estado(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cidade"] = "Cidade Inventada"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "R$ 15,00" in texto
    # 29,00 + 15,00
    assert "R$ 44,00" in texto

def test_frete_de_outro_estado_nao_entrega(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    if frete.LOJA_UF == "RJ":
        dados["uf"] = "SP"
    else:
        dados["uf"] = "RJ"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "Ainda não entregamos nessa região" in texto
    assert "informe o endereço" in texto


# erros do formulário 

def test_post_com_cep_invalido_mostra_o_erro(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cep"] = "123"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "CEP inválido" in texto

def test_post_sem_bairro_nao_calcula_o_frete(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["bairro"] = ""
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "Informe o bairro." in texto
    assert "informe o endereço" in texto
    assert "a calcular" in texto

def test_post_visitante_com_email_invalido(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["email"] = "semarroba"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "E-mail inválido" in texto

def test_post_cliente_nao_precisa_informar_contato(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_cliente()
    dados = formulario_do_visitante()
    dados["nome"] = ""
    dados["email"] = ""
    dados["celular"] = ""
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "Informe seu nome." not in texto
    assert "E-mail inválido" not in texto
    assert "R$ 7,50" in texto


# cupom 

def test_cupom_valido_diminui_o_total(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "escolher_cupom", cupom_de_10_por_cento)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cupom"] = "promo10"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "Desconto (PROMO10)" in texto
    assert "R$ 2,90" in texto
    # 29,00 + 7,50 - 2,90
    assert "R$ 33,60" in texto

def test_cupom_do_cpf_entra_sozinho(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "escolher_cupom", cupom_do_cpf)
    monkeypatch.setattr(pedido_model, "buscar_endereco_principal", endereco_da_conta)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/checkout"))
    assert "Desconto do seu CPF aplicado automaticamente" in texto
    assert "BEMVINDO15-7" in texto
    # 29,00 + 7,50 - 15,00
    assert "R$ 21,50" in texto

def test_cupom_invalido_mostra_o_motivo_e_nao_desconta(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "escolher_cupom", cupom_vencido)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cupom"] = "VENCIDO5"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "Esse cupom está vencido." in texto
    assert "Desconto (" not in texto
    assert "R$ 36,50" in texto

def test_cupom_digitado_vai_pro_model_em_maiusculas(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    recebidos = []

    def falso(id_cliente, codigo, subtotal, hoje):
        recebidos.append((id_cliente, codigo, subtotal))
        return (None, "")

    monkeypatch.setattr(pedido_model, "escolher_cupom", falso)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cupom"] = "  promo10 "
    navegador.post("/checkout", data=dados)
    # visitante não tem id, o código vai em maiúsculas e sem espaço, e o subtotal é 29,00
    assert recebidos[0] == (None, "PROMO10", Decimal("29.00"))

def test_cliente_passa_o_proprio_id_pro_cupom(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    recebidos = []

    def falso(id_cliente, codigo, subtotal, hoje):
        recebidos.append(id_cliente)
        return (None, "")

    monkeypatch.setattr(pedido_model, "escolher_cupom", falso)
    navegador = entrar_como_cliente()
    navegador.get("/checkout")
    assert recebidos[0] == 7

def test_erro_no_banco_ao_conferir_o_cupom_nao_derruba_a_pagina(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "escolher_cupom", erro_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.post("/checkout", data=formulario_do_visitante())
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Não foi possível conferir o cupom" in texto
    assert "R$ 36,50" in texto


# dados guardados na sessão (a parte 2 usa)

def test_dados_validos_ficam_guardados_na_sessao(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    navegador.post("/checkout", data=formulario_do_visitante())
    with navegador.session_transaction() as sessao:
        assert sessao["checkout"]["rua"] == "Praça da Sé"
        assert sessao["checkout"]["email"] == "visita@gmail.com"

def test_dados_com_erro_nao_ficam_guardados(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cep"] = "123"
    navegador.post("/checkout", data=dados)
    with navegador.session_transaction() as sessao:
        assert "checkout" not in sessao

def test_cupom_invalido_nao_vai_pra_sessao(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "escolher_cupom", cupom_vencido)
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cupom"] = "VENCIDO5"
    navegador.post("/checkout", data=dados)
    with navegador.session_transaction() as sessao:
        assert sessao["checkout"]["cupom"] == ""

def test_dados_guardados_voltam_a_aparecer_ao_abrir_de_novo(monkeypatch):
    deixar_checkout_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    navegador.post("/checkout", data=formulario_do_visitante())
    texto = pegar_texto(navegador.get("/checkout"))
    assert 'value="Praça da Sé"' in texto
    assert 'value="visita@gmail.com"' in texto
    assert "R$ 36,50" in texto


# o carrinho do visitante acompanha quando ele entra na conta 

def test_login_junta_o_carrinho_do_visitante(monkeypatch):
    chamadas = []

    def juntar(id_sessao, id_cliente):
        chamadas.append((id_sessao, id_cliente))
        return 2

    def login_de_mentira(cpf, senha):
        return {"id": 7, "nome": "Ana Teste"}

    monkeypatch.setattr(carrinho_model, "juntar_carrinho_do_visitante", juntar)
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(cliente_model, "conferir_login", login_de_mentira)
    deixar_vitrine_de_mentira(monkeypatch)

    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["id_sessao"] = "codigo-do-visitante"

    dados = {"cpf": "390.533.447-05", "senha": "Cupcake@123"}
    resposta = navegador.post("/login", data=dados, follow_redirects=True)
    texto = pegar_texto(resposta)

    # o model recebeu o código do visitante e o id da conta
    assert chamadas == [("codigo-do-visitante", 7)]
    assert "Os itens do seu carrinho foram mantidos." in texto
    with navegador.session_transaction() as sessao:
        assert sessao["id_cliente"] == 7
        # o código do visitante não fica mais na sessão
        assert "id_sessao" not in sessao

def test_login_sem_carrinho_de_visitante_nao_junta_nada(monkeypatch):
    chamadas = []

    def juntar(id_sessao, id_cliente):
        chamadas.append((id_sessao, id_cliente))
        return 0

    def login_de_mentira(cpf, senha):
        return {"id": 7, "nome": "Ana Teste"}

    monkeypatch.setattr(carrinho_model, "juntar_carrinho_do_visitante", juntar)
    monkeypatch.setattr(cliente_model, "conferir_login", login_de_mentira)

    navegador = pegar_navegador()
    dados = {"cpf": "390.533.447-05", "senha": "Cupcake@123"}
    resposta = navegador.post("/login", data=dados)
    assert resposta.status_code == 302
    assert chamadas == []

def test_erro_ao_juntar_o_carrinho_nao_impede_o_login(monkeypatch):
    def login_de_mentira(cpf, senha):
        return {"id": 7, "nome": "Ana Teste"}

    monkeypatch.setattr(carrinho_model, "juntar_carrinho_do_visitante", erro_de_mentira)
    monkeypatch.setattr(cliente_model, "conferir_login", login_de_mentira)

    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["id_sessao"] = "codigo-do-visitante"

    dados = {"cpf": "390.533.447-05", "senha": "Cupcake@123"}
    resposta = navegador.post("/login", data=dados)
    assert resposta.status_code == 302
    with navegador.session_transaction() as sessao:
        assert sessao["tipo"] == "cliente"

def test_cadastro_junta_o_carrinho_do_visitante(monkeypatch):
    chamadas = []

    def juntar(id_sessao, id_cliente):
        chamadas.append((id_sessao, id_cliente))
        return 1

    def sem_cliente(cpf):
        return None

    def email_livre(email):
        return False

    def criar_de_mentira(*args):
        return 8

    monkeypatch.setattr(carrinho_model, "juntar_carrinho_do_visitante", juntar)
    monkeypatch.setattr(cliente_model, "buscar_cliente_por_cpf", sem_cliente)
    monkeypatch.setattr(cliente_model, "email_ja_existe", email_livre)
    monkeypatch.setattr(cliente_model, "criar_cliente", criar_de_mentira)

    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["id_sessao"] = "codigo-do-visitante"

    dados = {
        "nome": "Ana Souza", "email": "ana@gmail.com", "celular": "11900000001",
        "cpf": "39053344705", "senha": "Cupcake@123", "cep": "01001000",
        "rua": "Praça da Sé", "numero": "100", "bairro": "Sé",
        "cidade": "São Paulo", "uf": "SP",
    }
    resposta = navegador.post("/cadastro", data=dados)
    assert resposta.status_code == 302
    assert chamadas == [("codigo-do-visitante", 8)]


