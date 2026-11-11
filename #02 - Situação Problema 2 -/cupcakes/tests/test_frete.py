# testes do frete por região (cartão 10)
# eles usam as constantes da loja que estão no próprio frete.py (se trocar o endereço da loja lá, os testes continuam certos)

from decimal import Decimal
from models import frete


# pega uma sigla de estado diferente da sigla da loja
def outro_estado():
    if frete.LOJA_UF == "RJ":
        return "SP"
    return "RJ"

def test_mesmo_bairro_da_loja():
    resultado = frete.calcular_frete(frete.LOJA_BAIRRO, frete.LOJA_CIDADE, frete.LOJA_UF)
    assert resultado["valor"] == Decimal("5.00")
    assert resultado["minutos"] == 30
    assert resultado["regiao"] == "Mesmo bairro da loja"

def test_mesma_cidade_em_outro_bairro():
    resultado = frete.calcular_frete("Bairro Inventado", frete.LOJA_CIDADE, frete.LOJA_UF)
    assert resultado["valor"] == Decimal("7.50")
    assert resultado["minutos"] == 40
    assert resultado["regiao"] == "Mesma cidade da loja"

def test_outra_cidade_do_mesmo_estado():
    resultado = frete.calcular_frete(frete.LOJA_BAIRRO, "Cidade Inventada", frete.LOJA_UF)
    assert resultado["valor"] == Decimal("15.00")
    assert resultado["minutos"] == 70
    assert resultado["regiao"] == "Outra cidade do mesmo estado"

def test_outro_estado_nao_entrega():
    resultado = frete.calcular_frete(frete.LOJA_BAIRRO, frete.LOJA_CIDADE, outro_estado())
    assert resultado is None

def test_ignora_maiuscula_e_acento_na_cidade():
    # "SÃO PAULO" tem que ser igual a "São Paulo"
    cidade = frete.LOJA_CIDADE.upper()
    resultado = frete.calcular_frete("Bairro Inventado", cidade, frete.LOJA_UF)
    assert resultado["valor"] == Decimal("7.50")

def test_uf_com_espaco_e_minuscula():
    uf = " " + frete.LOJA_UF.lower() + " "
    resultado = frete.calcular_frete("Bairro Inventado", frete.LOJA_CIDADE, uf)
    assert resultado["valor"] == Decimal("7.50")

def test_textos_iguais_sem_acento_e_com_espaco_sobrando():
    assert frete.textos_iguais("São Paulo", "  sao paulo ") == True

def test_textos_diferentes():
    assert frete.textos_iguais("São Paulo", "Santos") == False
