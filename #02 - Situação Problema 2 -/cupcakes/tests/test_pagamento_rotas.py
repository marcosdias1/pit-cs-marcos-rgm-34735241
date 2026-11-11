# testes das rotas do pagamento: "Ir para o pagamento", tela de pagamento (PIX e cartão) e pedido confirmado

from decimal import Decimal
from datetime import date, datetime, timedelta
from app import app
from models import carrinho_model
from models import pedido_model
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

# visitante que já criou o pedido 50 (é o pedido de mentira dos testes)
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

def adicionais_nenhum(id_carrinho):
    return []

def carrinho_numero_1(id_cliente, id_sessao):
    return 1

def contador_zero(id_cliente, id_sessao):
    return 0

def endereco_nenhum(id_cliente):
    return None

def contato_da_conta(id_cliente):
    return {"nome": "Ana Teste", "email": "ana@gmail.com", "celular": "11900000001"}

def contato_nenhum(id_cliente):
    return None

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

def cupom_de_10_por_cento(id_cliente, codigo, subtotal, hoje):
    return (pegar_cupom("PERCENTUAL", "10.00", "PROMO10"), "")


def cupom_vencido(id_cliente, codigo, subtotal, hoje):
    return (None, "Esse cupom está vencido.")

def cupom_do_pedido_ok(pedido, hoje):
    return ""

# função que dá erro de propósito (o * faz ela aceitar qualquer quantidade de argumentos)
def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")

# o pedido 50 (número 10050). id_cliente None é pedido de visitante
def pedido_de_mentira(id_cliente, status):
    pedido = {}
    pedido["id"] = 50
    pedido["numero"] = 10050
    pedido["id_cliente"] = id_cliente
    pedido["status"] = status
    pedido["subtotal"] = Decimal("29.00")
    pedido["frete"] = Decimal("7.50")
    pedido["desconto"] = Decimal("0.00")
    pedido["total"] = Decimal("36.50")
    pedido["subtotal_texto"] = "R$ 29,00"
    pedido["frete_texto"] = "R$ 7,50"
    pedido["desconto_texto"] = "R$ 0,00"
    pedido["total_texto"] = "R$ 36,50"
    pedido["tem_desconto"] = False
    pedido["data_hora"] = datetime.now()
    pedido["previsao_entrega"] = datetime.now() + timedelta(minutes=40)
    pedido["nome_contato"] = "Visitante Teste"
    pedido["email_contato"] = "visita@gmail.com"
    pedido["id_cupom"] = None
    pedido["forma"] = "PIX"
    return pedido

def itens_do_pedido_de_mentira(id_pedido):
    lista = []
    lista.append({"nome": "Chocolate", "quantidade": 2, "subtotal_texto": "R$ 24,00"})
    lista.append({"nome": "Calda de chocolate", "quantidade": 1, "subtotal_texto": "R$ 5,00"})
    return lista

# troca o "buscar pedido" por uma função que sempre devolve o pedido que eu quiser
def usar_pedido(monkeypatch, pedido):
    def buscar(numero):
        return pedido

    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", buscar)

# troca as funções do banco pelas de mentira (carrinho com 29,00, sem cupom e sem endereço salvo)
def deixar_tudo_de_mentira(monkeypatch):
    monkeypatch.setattr(carrinho_model, "pegar_ou_criar_carrinho", carrinho_numero_1)
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(carrinho_model, "listar_itens", itens_com_cupcake)
    monkeypatch.setattr(carrinho_model, "listar_adicionais", adicionais_nenhum)
    monkeypatch.setattr(pedido_model, "escolher_cupom", sem_cupom)
    monkeypatch.setattr(pedido_model, "buscar_endereco_principal", endereco_nenhum)
    monkeypatch.setattr(pedido_model, "buscar_contato_do_cliente", contato_da_conta)
    monkeypatch.setattr(pedido_model, "conferir_cupom_do_pedido", cupom_do_pedido_ok)
    monkeypatch.setattr(pedido_model, "listar_itens_do_pedido", itens_do_pedido_de_mentira)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "AGUARDANDO_PAGAMENTO"))

# troca uma função do pedido por uma que anota com o que foi chamada
# (devolve a lista de chamadas pra gente conferir no teste)
def espionar(monkeypatch, nome_da_funcao, retorno):
    chamadas = []

    def falso(*args):
        chamadas.append(args)
        return retorno

    monkeypatch.setattr(pedido_model, nome_da_funcao, falso)
    return chamadas

# o que o visitante preenche no fechamento: mesma cidade da loja, outro bairro (frete de 7,50)
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
    dados["acao"] = "pagar"
    return dados

def dados_do_cartao(numero):
    dados = {}
    dados["forma"] = "CARTAO_CREDITO"
    dados["numero_cartao"] = numero
    dados["nome"] = "Ana Teste"
    dados["validade"] = "12/35"
    dados["cvv"] = "123"
    return dados


# IR PARA O PAGAMENTO (cria o pedido) 

def test_botao_ir_para_o_pagamento_aparece(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/checkout"))
    assert "Ir para o pagamento" in texto
    assert 'name="acao" value="pagar"' in texto

def test_ir_para_o_pagamento_cria_o_pedido_e_vai_pra_tela_de_pagamento(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_visitante()
    resposta = navegador.post("/checkout", data=formulario_do_visitante())

    assert resposta.status_code == 302
    assert "/pagamento/10050" in resposta.headers["Location"]
    assert len(chamadas) == 1

    # o que o model recebeu: (id_cliente, contato, endereco, itens, subtotal, frete, desconto, total, id_cupom, id_antigo)
    recebido = chamadas[0]
    assert recebido[0] is None
    assert recebido[1]["email"] == "visita@gmail.com"
    assert recebido[1]["celular"] == "11900000001"
    assert recebido[2]["cep"] == "01001000"
    assert recebido[2]["rua"] == "Praça da Sé"
    assert len(recebido[3]) == 2
    assert recebido[4] == Decimal("29.00")
    assert recebido[5]["valor"] == Decimal("7.50")
    assert recebido[6] == Decimal("0.00")
    assert recebido[7] == Decimal("36.50")
    assert recebido[8] is None
    assert recebido[9] is None

    # o visitante guarda qual é o pedido dele
    with navegador.session_transaction() as sessao:
        assert sessao["pedido_atual"] == 50

def test_ir_para_o_pagamento_com_cupom_manda_o_id_e_o_desconto(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "escolher_cupom", cupom_de_10_por_cento)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cupom"] = "promo10"
    navegador.post("/checkout", data=dados)

    recebido = chamadas[0]
    # desconto de 10% de 29,00 e total de 29,00 + 7,50 - 2,90
    assert recebido[6] == Decimal("2.90")
    assert recebido[7] == Decimal("33.60")
    assert recebido[8] == 1

def test_so_calcular_nao_cria_pedido(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    del dados["acao"]
    resposta = navegador.post("/checkout", data=dados)
    assert resposta.status_code == 200
    assert chamadas == []

def test_ir_para_o_pagamento_com_endereco_invalido_nao_cria_pedido(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cep"] = "123"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "Corrija os campos marcados em vermelho" in texto
    assert "CEP inválido" in texto
    assert chamadas == []

def test_ir_para_o_pagamento_com_cupom_invalido_nao_cria_pedido(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "escolher_cupom", cupom_vencido)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    dados["cupom"] = "VENCIDO5"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "Corrija o cupom" in texto
    assert chamadas == []

def test_ir_para_o_pagamento_fora_da_area_de_entrega_nao_cria_pedido(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_visitante()
    dados = formulario_do_visitante()
    if frete.LOJA_UF == "RJ":
        dados["uf"] = "SP"
    else:
        dados["uf"] = "RJ"
    texto = pegar_texto(navegador.post("/checkout", data=dados))
    assert "Ainda não entregamos nessa região" in texto
    assert chamadas == []

def test_ir_para_o_pagamento_cancela_o_pedido_anterior_que_nao_foi_pago(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 49
    navegador.post("/checkout", data=formulario_do_visitante())
    # o último argumento é o pedido antigo
    assert chamadas[0][9] == 49

def test_cliente_usa_o_contato_da_conta_no_pedido(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_cliente()
    dados = formulario_do_visitante()
    dados["nome"] = ""
    dados["email"] = ""
    dados["celular"] = ""
    resposta = navegador.post("/checkout", data=dados)
    assert resposta.status_code == 302
    assert chamadas[0][0] == 7
    assert chamadas[0][1]["email"] == "ana@gmail.com"

def test_cliente_sem_contato_nao_cria_pedido(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "buscar_contato_do_cliente", contato_nenhum)
    chamadas = espionar(monkeypatch, "criar_pedido", {"id": 50, "numero": 10050})
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.post("/checkout", data=formulario_do_visitante()))
    assert "Não foi possível buscar o seu contato" in texto
    assert chamadas == []

def test_erro_no_banco_ao_criar_o_pedido_mostra_mensagem(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "criar_pedido", erro_de_mentira)
    navegador = entrar_como_visitante()
    resposta = navegador.post("/checkout", data=formulario_do_visitante())
    assert resposta.status_code == 200
    assert "Não foi possível criar o pedido agora" in pegar_texto(resposta)


# TELA DE PAGAMENTO: acesso 

def test_pagamento_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/pagamento/10050")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_pagamento_de_pedido_que_nao_existe(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, None)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pagamento/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_visitante_nao_ve_pedido_que_nao_e_dele(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 51
    texto = pegar_texto(navegador.get("/pagamento/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto
    assert "Total a pagar" not in texto

def test_visitante_sem_pedido_na_sessao_nao_ve_nada(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/pagamento/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_cliente_nao_ve_pedido_de_outro_cliente(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(8, "AGUARDANDO_PAGAMENTO"))
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/pagamento/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_cliente_nao_ve_pedido_de_visitante(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/pagamento/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_visitante_nao_ve_pedido_de_cliente(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(7, "AGUARDANDO_PAGAMENTO"))
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pagamento/10050", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_pedido_ja_pago_vai_pra_tela_de_confirmado(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "CONFIRMADO"))
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pagamento/10050")
    assert resposta.status_code == 302
    assert "/pedido/10050/confirmado" in resposta.headers["Location"]

def test_pedido_cancelado_nao_pode_ser_pago(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "CANCELADO"))
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pagamento/10050", follow_redirects=True))
    assert "Esse pedido foi cancelado" in texto

def test_erro_no_banco_ao_abrir_o_pagamento(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "buscar_pedido_por_numero", erro_de_mentira)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pagamento/10050", follow_redirects=True))
    assert "Não foi possível abrir o pedido agora" in texto


# TELA DE PAGAMENTO: o que aparece 

def test_visitante_ve_o_total_o_pix_e_o_botao_de_confirmar(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pagamento/10050")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Total a pagar" in texto
    assert "R$ 36,50" in texto
    assert "QR Code do PIX" in texto
    assert 'name="forma" value="PIX"' in texto

def test_pix_tem_so_um_botao_de_confirmar_pagamento(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pagamento/10050"))
    assert texto.count('<button type="submit" class="botao botao-destaque">Confirmar pagamento</button>') == 1

def test_cartoes_de_teste_aparecem_pro_visitante(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pagamento/10050"))
    assert "4111 1111 1111 1111" in texto
    assert "4000 0000 0000 0002" in texto
    assert "nenhum pagamento é de verdade" in texto

def test_cartoes_de_teste_aparecem_pro_cliente(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(7, "AGUARDANDO_PAGAMENTO"))
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/pagamento/10050"))
    assert "4111 1111 1111 1111" in texto
    assert "4000 0000 0000 0002" in texto

def test_tela_de_pagamento_tem_o_formulario_do_cartao(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pagamento/10050"))
    assert 'name="numero_cartao"' in texto
    assert 'name="validade"' in texto
    assert 'name="cvv"' in texto
    assert 'data-abrir="0"' in texto


# PAGAR COM PIX 

def test_pix_confirma_o_pagamento_e_vai_pro_pedido_confirmado(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "confirmar_pagamento", "")
    navegador = entrar_como_visitante_com_pedido()
    with navegador.session_transaction() as sessao:
        sessao["checkout"] = {"rua": "Praça da Sé"}

    resposta = navegador.post("/pagamento/10050", data={"forma": "PIX"})
    assert resposta.status_code == 302
    assert "/pedido/10050/confirmado" in resposta.headers["Location"]

    # (id do pedido, carrinho, forma, valor, código, id do cliente)
    assert len(chamadas) == 1
    recebido = chamadas[0]
    assert recebido[0] == 50
    assert recebido[1] == 1
    assert recebido[2] == "PIX"
    assert recebido[3] == Decimal("36.50")
    assert recebido[4].startswith("SIM-PIX-")
    assert recebido[5] is None

    # os dados do fechamento saem da sessão
    with navegador.session_transaction() as sessao:
        assert "checkout" not in sessao

def test_pix_do_cliente_passa_o_id_do_cliente(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(7, "AGUARDANDO_PAGAMENTO"))
    chamadas = espionar(monkeypatch, "confirmar_pagamento", "")
    navegador = entrar_como_cliente()
    navegador.post("/pagamento/10050", data={"forma": "PIX"})
    assert chamadas[0][5] == 7

def test_pix_mostra_o_problema_que_veio_do_model(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    espionar(monkeypatch, "confirmar_pagamento", "Um dos itens acabou no estoque agora há pouco.")
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.post("/pagamento/10050", data={"forma": "PIX"})
    assert resposta.status_code == 200
    assert "Um dos itens acabou no estoque" in pegar_texto(resposta)

def test_pix_com_cupom_que_nao_vale_mais_nao_confirma(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)

    def cupom_vencido_no_pedido(pedido, hoje):
        return "Esse cupom está vencido."

    monkeypatch.setattr(pedido_model, "conferir_cupom_do_pedido", cupom_vencido_no_pedido)
    chamadas = espionar(monkeypatch, "confirmar_pagamento", "")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.post("/pagamento/10050", data={"forma": "PIX"}))
    assert "Esse cupom está vencido." in texto
    assert "Volte ao carrinho" in texto
    assert chamadas == []

def test_erro_no_banco_ao_confirmar_nao_cobra_nada(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "confirmar_pagamento", erro_de_mentira)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.post("/pagamento/10050", data={"forma": "PIX"})
    assert resposta.status_code == 200
    assert "Nada foi cobrado" in pegar_texto(resposta)

def test_nao_paga_pedido_de_outra_pessoa(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "confirmar_pagamento", "")
    navegador = entrar_como_visitante()
    with navegador.session_transaction() as sessao:
        sessao["pedido_atual"] = 51
    navegador.post("/pagamento/10050", data={"forma": "PIX"})
    assert chamadas == []

def test_pedido_ja_pago_nao_paga_de_novo(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "CONFIRMADO"))
    chamadas = espionar(monkeypatch, "confirmar_pagamento", "")
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.post("/pagamento/10050", data={"forma": "PIX"})
    assert resposta.status_code == 302
    assert chamadas == []

def test_pagar_sem_escolher_a_forma(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "confirmar_pagamento", "")
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.post("/pagamento/10050", data={"forma": "boleto"}))
    assert "Escolha como pagar" in texto
    assert chamadas == []


# PAGAR COM CARTÃO 

def test_cartao_aprovado_confirma_o_pagamento(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    chamadas = espionar(monkeypatch, "confirmar_pagamento", "")
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.post("/pagamento/10050", data=dados_do_cartao("4111 1111 1111 1111"))
    assert resposta.status_code == 302
    assert "/pedido/10050/confirmado" in resposta.headers["Location"]
    assert chamadas[0][2] == "CARTAO_CREDITO"
    assert chamadas[0][4].startswith("SIM-")

def test_cartao_recusado_guarda_a_tentativa_e_nao_confirma(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    confirmar = espionar(monkeypatch, "confirmar_pagamento", "")
    recusar = espionar(monkeypatch, "registrar_pagamento_recusado", None)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.post("/pagamento/10050", data=dados_do_cartao("4000 0000 0000 0002"))
    texto = pegar_texto(resposta)

    assert resposta.status_code == 200
    assert "Pagamento recusado. Tente outro cartão ou PIX." in texto
    assert confirmar == []
    # (id do pedido, forma, valor, código)
    assert len(recusar) == 1
    assert recusar[0][0] == 50
    assert recusar[0][1] == "CARTAO_CREDITO"
    assert recusar[0][2] == Decimal("36.50")
    # o pedido continua esperando e dá pra tentar de novo (o formulário continua na tela)
    assert 'name="numero_cartao"' in texto
    assert 'data-abrir="1"' in texto

def test_depois_de_recusado_o_cartao_aprovado_funciona(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    confirmar = espionar(monkeypatch, "confirmar_pagamento", "")
    espionar(monkeypatch, "registrar_pagamento_recusado", None)
    navegador = entrar_como_visitante_com_pedido()
    navegador.post("/pagamento/10050", data=dados_do_cartao("4000 0000 0000 0002"))
    resposta = navegador.post("/pagamento/10050", data=dados_do_cartao("4111 1111 1111 1111"))
    assert resposta.status_code == 302
    assert len(confirmar) == 1

def test_cartao_com_numero_invalido_nao_chega_na_operadora(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    confirmar = espionar(monkeypatch, "confirmar_pagamento", "")
    recusar = espionar(monkeypatch, "registrar_pagamento_recusado", None)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.post("/pagamento/10050", data=dados_do_cartao("5555 5555 5555")))
    assert "Número do cartão inválido." in texto
    assert confirmar == []
    assert recusar == []
    # o nome volta preenchido, mas o número e o cvv nunca voltam escritos
    assert 'value="Ana Teste"' in texto
    assert "5555 5555 5555" not in texto
    assert 'data-abrir="1"' in texto

def test_cartao_vencido_mostra_o_erro(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante_com_pedido()
    dados = dados_do_cartao("4111 1111 1111 1111")
    dados["validade"] = "01/20"
    texto = pegar_texto(navegador.post("/pagamento/10050", data=dados))
    assert "Cartão vencido." in texto

def test_cartao_com_cvv_invalido_mostra_o_erro(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante_com_pedido()
    dados = dados_do_cartao("4111 1111 1111 1111")
    dados["cvv"] = "12"
    texto = pegar_texto(navegador.post("/pagamento/10050", data=dados))
    assert "CVV inválido" in texto

def test_erro_no_banco_ao_guardar_a_recusa_nao_derruba_a_pagina(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    monkeypatch.setattr(pedido_model, "registrar_pagamento_recusado", erro_de_mentira)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.post("/pagamento/10050", data=dados_do_cartao("4000 0000 0000 0002"))
    assert resposta.status_code == 200
    assert "Nada foi cobrado" in pegar_texto(resposta)


# PEDIDO CONFIRMADO 

def test_confirmado_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/pedido/10050/confirmado")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_confirmado_mostra_o_numero_os_itens_e_o_total(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "CONFIRMADO"))
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pedido/10050/confirmado")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Pedido confirmado!" in texto
    assert "#10050" in texto
    assert "2x Chocolate" in texto
    assert "R$ 24,00" in texto
    assert "R$ 36,50" in texto
    assert "Previsão de entrega" in texto
    assert "Pago com" in texto

def test_confirmado_mostra_o_desconto_quando_tem(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    pedido = pedido_de_mentira(None, "CONFIRMADO")
    pedido["tem_desconto"] = True
    pedido["desconto_texto"] = "R$ 2,90"
    usar_pedido(monkeypatch, pedido)
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050/confirmado"))
    assert "Desconto" in texto
    assert "R$ 2,90" in texto

def test_confirmado_sem_desconto_nao_mostra_a_linha_de_desconto(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "CONFIRMADO"))
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050/confirmado"))
    assert "Desconto" not in texto

def test_visitante_ve_o_aviso_do_e_mail_e_o_cliente_nao(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "CONFIRMADO"))
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050/confirmado"))
    assert "visita@gmail.com" in texto

    usar_pedido(monkeypatch, pedido_de_mentira(7, "CONFIRMADO"))
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/pedido/10050/confirmado"))
    assert "Guarde o número do pedido" not in texto

def test_confirmado_de_pedido_que_ainda_nao_foi_pago_volta_pro_pagamento(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pedido/10050/confirmado")
    assert resposta.status_code == 302
    assert "/pagamento/10050" in resposta.headers["Location"]

def test_confirmado_de_pedido_de_outra_pessoa(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(8, "CONFIRMADO"))
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/pedido/10050/confirmado", follow_redirects=True))
    assert "Pedido não encontrado." in texto

def test_confirmado_de_pedido_cancelado(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "CANCELADO"))
    navegador = entrar_como_visitante_com_pedido()
    texto = pegar_texto(navegador.get("/pedido/10050/confirmado", follow_redirects=True))
    assert "Esse pedido foi cancelado" in texto

def test_confirmado_com_erro_ao_listar_os_itens_abre_mesmo_assim(monkeypatch):
    deixar_tudo_de_mentira(monkeypatch)
    usar_pedido(monkeypatch, pedido_de_mentira(None, "CONFIRMADO"))
    monkeypatch.setattr(pedido_model, "listar_itens_do_pedido", erro_de_mentira)
    navegador = entrar_como_visitante_com_pedido()
    resposta = navegador.get("/pedido/10050/confirmado")
    assert resposta.status_code == 200
    assert "Pedido confirmado!" in pegar_texto(resposta)
