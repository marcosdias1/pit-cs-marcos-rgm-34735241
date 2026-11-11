# testes das conferências do fechamento do pedido: endereço, contato do visitante, carrinho pronto e o total do pedido


from decimal import Decimal
from models import validacoes
from models import carrinho_model


# item de mentira do carrinho
def pegar_item(tipo, nome, quantidade, estoque, disponivel=True):
    item = {}
    item["tipo"] = tipo
    item["nome"] = nome
    item["quantidade"] = quantidade
    item["estoque"] = estoque
    item["disponivel"] = disponivel
    return item


# conferir o endereço 

def test_endereco_certo_nao_tem_erros():
    erros = validacoes.conferir_endereco("01001-000", "Praça da Sé", "100", "Sé", "São Paulo", "SP")
    assert len(erros) == 0

def test_endereco_vazio_tem_erro_em_todos_os_campos():
    erros = validacoes.conferir_endereco("", "", "", "", "", "")
    assert len(erros) == 6

def test_endereco_com_cep_curto():
    erros = validacoes.conferir_endereco("0100", "Praça da Sé", "100", "Sé", "São Paulo", "SP")
    assert len(erros) == 1
    assert "cep" in erros

def test_endereco_com_estado_que_nao_existe():
    erros = validacoes.conferir_endereco("01001-000", "Praça da Sé", "100", "Sé", "São Paulo", "XX")
    assert "uf" in erros


# conferir o contato do visitante

def test_contato_certo_nao_tem_erros():
    erros = validacoes.conferir_contato("Ana Souza", "ana@gmail.com", "(11) 90000-0001")
    assert len(erros) == 0

def test_contato_vazio_tem_tres_erros():
    erros = validacoes.conferir_contato("", "", "")
    assert len(erros) == 3

def test_contato_com_email_invalido():
    erros = validacoes.conferir_contato("Ana Souza", "anagmail.com", "11900000001")
    assert len(erros) == 1
    assert "email" in erros

def test_contato_com_celular_curto():
    erros = validacoes.conferir_contato("Ana Souza", "ana@gmail.com", "1190000")
    assert "celular" in erros


# carrinho pronto pra fechar o pedido 

def test_carrinho_certo_pode_fechar():
    itens = [pegar_item("CUPCAKE", "Chocolate", 2, 50), pegar_item("ADICIONAL", "Calda", 1, 100)]
    assert carrinho_model.conferir_carrinho(itens) == ""

def test_carrinho_vazio_nao_pode_fechar():
    assert carrinho_model.conferir_carrinho([]) == "Seu carrinho está vazio."

def test_so_adicional_nao_pode_fechar():
    itens = [pegar_item("ADICIONAL", "Calda", 1, 100)]
    assert carrinho_model.conferir_carrinho(itens) == "Escolha pelo menos um cupcake para fechar o pedido."

def test_item_sem_estoque_nao_pode_fechar():
    itens = [pegar_item("CUPCAKE", "Chocolate", 1, 0, False)]
    resultado = carrinho_model.conferir_carrinho(itens)
    assert resultado == "O item Chocolate está sem estoque. Tire ele do carrinho para continuar."

def test_quantidade_maior_que_o_estoque_nao_pode_fechar():
    itens = [pegar_item("CUPCAKE", "Chocolate", 5, 3)]
    resultado = carrinho_model.conferir_carrinho(itens)
    assert resultado == "Só temos 3 de Chocolate em estoque. Diminua a quantidade no carrinho."

def test_quantidade_igual_ao_estoque_pode_fechar():
    itens = [pegar_item("CUPCAKE", "Chocolate", 3, 3)]
    assert carrinho_model.conferir_carrinho(itens) == ""


# total do pedido: subtotal + frete - desconto

def test_total_com_frete_e_desconto():
    # 29,00 + 7,50 - 2,90 = 33,60
    total = carrinho_model.calcular_total(Decimal("29.00"), Decimal("7.50"), Decimal("2.90"))
    assert total == Decimal("33.60")

def test_total_sem_desconto():
    total = carrinho_model.calcular_total(Decimal("29.00"), Decimal("7.50"), Decimal("0.00"))
    assert total == Decimal("36.50")

def test_total_quando_o_desconto_e_o_subtotal_inteiro():
    # sobra só o frete
    total = carrinho_model.calcular_total(Decimal("10.00"), Decimal("5.00"), Decimal("10.00"))
    assert total == Decimal("5.00")

def test_total_nao_erra_os_centavos():
    total = carrinho_model.calcular_total(Decimal("0.10"), Decimal("0.20"), Decimal("0.00"))
    assert total == Decimal("0.30")
