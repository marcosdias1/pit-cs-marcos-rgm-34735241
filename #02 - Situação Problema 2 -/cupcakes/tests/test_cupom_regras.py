# testes das regras do cupom (cartão 09): validade, uso único, primeira compra e desconto


from datetime import date
from decimal import Decimal
from models import cupom_regras

# "hoje" fixo, assim o teste não muda com o passar dos dias
HOJE = date(2026, 11, 3)


# cupom de mentira: 10% de desconto, vale pra qualquer pessoa, até 2030
def pegar_cupom():
    cupom = {}
    cupom["id"] = 1
    cupom["id_cliente"] = None
    cupom["codigo"] = "PROMO10"
    cupom["tipo"] = "PERCENTUAL"
    cupom["valor"] = Decimal("10.00")
    cupom["valido_de"] = date(2026, 1, 1)
    cupom["valido_ate"] = date(2030, 12, 31)
    cupom["uso_unico"] = False
    cupom["primeira_compra"] = False
    cupom["ativo"] = True
    return cupom


# validar o cupom 

def test_cupom_valido_pra_visitante():
    resultado = cupom_regras.validar_cupom(pegar_cupom(), HOJE, None, False, False)
    assert resultado == ""

def test_cupom_que_nao_existe():
    resultado = cupom_regras.validar_cupom(None, HOJE, None, False, False)
    assert resultado == "Cupom não encontrado."

def test_cupom_desativado_e_como_se_nao_existisse():
    cupom = pegar_cupom()
    cupom["ativo"] = False
    resultado = cupom_regras.validar_cupom(cupom, HOJE, None, False, False)
    assert resultado == "Cupom não encontrado."

def test_cupom_vencido():
    cupom = pegar_cupom()
    cupom["valido_ate"] = date(2025, 1, 31)
    resultado = cupom_regras.validar_cupom(cupom, HOJE, None, False, False)
    assert resultado == "Esse cupom está vencido."

def test_cupom_valido_ate_hoje_ainda_vale():
    cupom = pegar_cupom()
    cupom["valido_ate"] = HOJE
    resultado = cupom_regras.validar_cupom(cupom, HOJE, None, False, False)
    assert resultado == ""

def test_cupom_que_ainda_nao_comecou():
    cupom = pegar_cupom()
    cupom["valido_de"] = date(2026, 12, 1)
    resultado = cupom_regras.validar_cupom(cupom, HOJE, None, False, False)
    assert resultado == "Esse cupom só começa a valer em 01/12/2026."

def test_cupom_pessoal_de_outra_conta():
    cupom = pegar_cupom()
    cupom["id_cliente"] = 5
    resultado = cupom_regras.validar_cupom(cupom, HOJE, 7, False, False)
    assert resultado == "Esse cupom é de outra conta."

def test_cupom_pessoal_pro_visitante_nao_vale():
    cupom = pegar_cupom()
    cupom["id_cliente"] = 5
    resultado = cupom_regras.validar_cupom(cupom, HOJE, None, False, False)
    assert resultado == "Esse cupom é de outra conta."

def test_cupom_pessoal_pro_dono_vale():
    cupom = pegar_cupom()
    cupom["id_cliente"] = 7
    resultado = cupom_regras.validar_cupom(cupom, HOJE, 7, False, False)
    assert resultado == ""


# uso único 

def test_uso_unico_pro_visitante_pede_conta():
    cupom = pegar_cupom()
    cupom["uso_unico"] = True
    resultado = cupom_regras.validar_cupom(cupom, HOJE, None, False, False)
    assert "só vale para quem tem conta" in resultado

def test_uso_unico_que_ja_foi_usado():
    cupom = pegar_cupom()
    cupom["uso_unico"] = True
    resultado = cupom_regras.validar_cupom(cupom, HOJE, 7, True, True)
    assert resultado == "Esse cupom já foi usado."

def test_uso_unico_que_ainda_nao_foi_usado():
    cupom = pegar_cupom()
    cupom["uso_unico"] = True
    resultado = cupom_regras.validar_cupom(cupom, HOJE, 7, False, True)
    assert resultado == ""


# primeira compra 

def test_primeira_compra_pro_visitante_pede_conta():
    cupom = pegar_cupom()
    cupom["primeira_compra"] = True
    resultado = cupom_regras.validar_cupom(cupom, HOJE, None, False, False)
    assert "primeira compra" in resultado

def test_primeira_compra_de_quem_ja_comprou():
    cupom = pegar_cupom()
    cupom["primeira_compra"] = True
    resultado = cupom_regras.validar_cupom(cupom, HOJE, 7, False, True)
    assert resultado == "Esse cupom vale só na primeira compra."

def test_primeira_compra_de_quem_nunca_comprou():
    cupom = pegar_cupom()
    cupom["primeira_compra"] = True
    resultado = cupom_regras.validar_cupom(cupom, HOJE, 7, False, False)
    assert resultado == ""

def test_cupom_de_boas_vindas_completo():
    # o cupom de 15 reais: pessoal, uso único e primeira compra
    cupom = pegar_cupom()
    cupom["id_cliente"] = 7
    cupom["tipo"] = "VALOR_FIXO"
    cupom["valor"] = Decimal("15.00")
    cupom["uso_unico"] = True
    cupom["primeira_compra"] = True
    assert cupom_regras.validar_cupom(cupom, HOJE, 7, False, False) == ""
    assert cupom_regras.validar_cupom(cupom, HOJE, 7, False, True) != ""


# calcular o desconto 

def test_desconto_de_valor_fixo():
    cupom = pegar_cupom()
    cupom["tipo"] = "VALOR_FIXO"
    cupom["valor"] = Decimal("15.00")
    assert cupom_regras.calcular_desconto(cupom, Decimal("50.00")) == Decimal("15.00")

def test_desconto_fixo_nunca_passa_do_subtotal():
    cupom = pegar_cupom()
    cupom["tipo"] = "VALOR_FIXO"
    cupom["valor"] = Decimal("15.00")
    assert cupom_regras.calcular_desconto(cupom, Decimal("10.00")) == Decimal("10.00")

def test_desconto_percentual():
    # 10% de 29,00
    assert cupom_regras.calcular_desconto(pegar_cupom(), Decimal("29.00")) == Decimal("2.90")

def test_desconto_percentual_arredonda_pra_cima_na_metade():
    # 10% de 12,35 é 1,235 e arredonda pra 1,24
    assert cupom_regras.calcular_desconto(pegar_cupom(), Decimal("12.35")) == Decimal("1.24")

def test_desconto_de_100_por_cento_e_o_subtotal_inteiro():
    cupom = pegar_cupom()
    cupom["valor"] = Decimal("100.00")
    assert cupom_regras.calcular_desconto(cupom, Decimal("29.00")) == Decimal("29.00")

def test_sem_cupom_nao_tem_desconto():
    assert cupom_regras.calcular_desconto(None, Decimal("29.00")) == Decimal("0.00")
