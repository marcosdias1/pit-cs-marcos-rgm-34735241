# testes do pagamento simulado (cartão 11): número, validade, operadora de mentira e previsão

from datetime import date, datetime
from models import pagamento_simulado
from models import pedido_model

# "hoje" fixo, assim o teste não muda com o passar dos dias
HOJE = date(2026, 11, 3)


# limpar e formatar o número 

def test_limpar_numero_tira_espaco_e_traco():
    assert pagamento_simulado.limpar_numero("4111 1111-1111 1111") == "4111111111111111"

def test_formatar_numero_de_16_digitos():
    assert pagamento_simulado.formatar_numero("4111111111111111") == "4111 1111 1111 1111"

def test_formatar_numero_de_15_digitos():
    assert pagamento_simulado.formatar_numero("378282246310005") == "3782 8224 6310 005"


# ler a validade 

def test_validade_com_ano_de_2_numeros():
    assert pagamento_simulado.ler_validade("12/35") == (12, 2035)

def test_validade_com_ano_de_4_numeros():
    assert pagamento_simulado.ler_validade("12/2035") == (12, 2035)

def test_validade_com_espacos_e_mes_de_um_numero():
    assert pagamento_simulado.ler_validade(" 1 / 35 ") == (1, 2035)

def test_validade_com_mes_que_nao_existe():
    assert pagamento_simulado.ler_validade("13/35") is None
    assert pagamento_simulado.ler_validade("00/35") is None

def test_validade_com_formato_errado():
    assert pagamento_simulado.ler_validade("1235") is None
    assert pagamento_simulado.ler_validade("12/3") is None
    assert pagamento_simulado.ler_validade("ab/cd") is None
    assert pagamento_simulado.ler_validade("123/35") is None
    assert pagamento_simulado.ler_validade("") is None


# conferir os dados do cartão 

def test_cartao_com_tudo_certo_nao_tem_erros():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "Ana Teste", "12/35", "123", HOJE)
    assert len(erros) == 0

def test_cartao_com_numero_comprido_demais():
    # 20 números (o máximo é 19)
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111 1111", "Ana Teste", "12/35", "123", HOJE)
    assert erros == {"numero": "Número do cartão inválido."}

def test_cartao_com_letra_no_numero():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 111a", "Ana Teste", "12/35", "123", HOJE)
    assert "numero" in erros

def test_cartao_com_numero_curto():
    erros = pagamento_simulado.validar_cartao("4111", "Ana Teste", "12/35", "123", HOJE)
    assert "numero" in erros

def test_cartao_sem_nome():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "   ", "12/35", "123", HOJE)
    assert "nome" in erros

def test_cartao_vencido_no_mes_passado():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "Ana Teste", "10/26", "123", HOJE)
    assert erros == {"validade": "Cartão vencido."}

def test_cartao_vencido_no_ano_passado():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "Ana Teste", "12/25", "123", HOJE)
    assert erros == {"validade": "Cartão vencido."}

def test_cartao_que_vence_neste_mes_ainda_vale():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "Ana Teste", "11/26", "123", HOJE)
    assert len(erros) == 0

def test_cartao_com_validade_em_formato_errado():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "Ana Teste", "1235", "123", HOJE)
    assert "validade" in erros

def test_cartao_com_validade_muito_distante():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "Ana Teste", "12/99", "123", HOJE)
    assert "validade" in erros

def test_cvv_de_4_numeros_vale():
    erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "Ana Teste", "12/35", "1234", HOJE)
    assert len(erros) == 0

def test_cvv_invalido():
    for cvv in ["12", "12345", "abc", ""]:
        erros = pagamento_simulado.validar_cartao("4111 1111 1111 1111", "Ana Teste", "12/35", cvv, HOJE)
        assert "cvv" in erros

def test_cartao_tudo_vazio_tem_erro_nos_4_campos():
    erros = pagamento_simulado.validar_cartao("", "", "", "", HOJE)
    assert len(erros) == 4


# a operadora de mentira 

def test_cartao_de_teste_e_aprovado():
    resultado = pagamento_simulado.autorizar_cartao(pagamento_simulado.CARTAO_APROVADO)
    assert resultado["aprovado"] == True
    assert resultado["codigo"].startswith("SIM-")

def test_cartao_de_teste_e_recusado():
    resultado = pagamento_simulado.autorizar_cartao(pagamento_simulado.CARTAO_RECUSADO)
    assert resultado["aprovado"] == False
    assert "recusado" in resultado["motivo"]

def test_cartao_recusado_com_espacos_no_numero_tambem_e_recusado():
    resultado = pagamento_simulado.autorizar_cartao("4000 0000 0000 0002")
    assert resultado["aprovado"] == False

def test_outro_cartao_valido_e_aprovado():
    resultado = pagamento_simulado.autorizar_cartao("378282246310005")
    assert resultado["aprovado"] == True

def test_cada_pagamento_tem_um_codigo_diferente():
    codigo1 = pagamento_simulado.autorizar_cartao(pagamento_simulado.CARTAO_APROVADO)["codigo"]
    codigo2 = pagamento_simulado.autorizar_cartao(pagamento_simulado.CARTAO_APROVADO)["codigo"]
    assert codigo1 != codigo2

def test_pix_sempre_e_aprovado():
    resultado = pagamento_simulado.autorizar_pix()
    assert resultado["aprovado"] == True
    assert resultado["codigo"].startswith("SIM-PIX-")


# previsão de entrega 

def test_previsao_para_hoje():
    previsao = datetime(2026, 11, 3, 19, 40)
    agora = datetime(2026, 11, 3, 18, 50)
    assert pedido_model.formatar_previsao(previsao, agora) == "hoje às 19:40"

def test_previsao_para_outro_dia():
    previsao = datetime(2026, 11, 4, 9, 15)
    agora = datetime(2026, 11, 3, 23, 50)
    assert pedido_model.formatar_previsao(previsao, agora) == "04/11 às 09:15"

def test_sem_previsao():
    assert pedido_model.formatar_previsao(None, datetime(2026, 11, 3, 18, 50)) == ""
