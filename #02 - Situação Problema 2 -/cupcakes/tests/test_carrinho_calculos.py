from decimal import Decimal
from models import carrinho_model


# lista de itens de mentira: 2 cupcakes de 12,00 e 1 adicional de 5,00
def pegar_itens():
    itens = []
    itens.append({"preco_unitario": Decimal("12.00"), "quantidade": 2})
    itens.append({"preco_unitario": Decimal("5.00"), "quantidade": 1})
    return itens


# formatar dinheiro 

def test_formatar_dinheiro_simples():
    assert carrinho_model.formatar_dinheiro(Decimal("12")) == "R$ 12,00"

def test_formatar_dinheiro_com_centavos():
    assert carrinho_model.formatar_dinheiro(Decimal("5.5")) == "R$ 5,50"

def test_formatar_dinheiro_com_milhar():
    assert carrinho_model.formatar_dinheiro(Decimal("1234.5")) == "R$ 1.234,50"

def test_formatar_dinheiro_zero():
    assert carrinho_model.formatar_dinheiro(Decimal("0")) == "R$ 0,00"

def test_formatar_dinheiro_aceita_numero_inteiro():
    assert carrinho_model.formatar_dinheiro(12) == "R$ 12,00"


# subtotal 

def test_subtotal_do_carrinho():
    # 2 x 12,00 + 1 x 5,00 = 29,00
    assert carrinho_model.calcular_subtotal(pegar_itens()) == Decimal("29.00")

def test_subtotal_do_carrinho_vazio():
    assert carrinho_model.calcular_subtotal([]) == Decimal("0.00")

def test_subtotal_nao_erra_os_centavos():
    # com float, 0.10 + 0.10 + 0.10 dá 0.30000000000000004. com Decimal dá certo
    itens = [{"preco_unitario": Decimal("0.10"), "quantidade": 3}]
    assert carrinho_model.calcular_subtotal(itens) == Decimal("0.30")

def test_subtotal_com_varias_unidades():
    itens = [{"preco_unitario": Decimal("12.00"), "quantidade": 10}]
    assert carrinho_model.calcular_subtotal(itens) == Decimal("120.00")