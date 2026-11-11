from models import acompanhamento

# testes das regras do acompanhamento do pedido (cartão 12): etapas, tempo e previsão
# eles usam os tempos que estão no próprio acompanhamento.py (se mudar os tempos de demonstração lá, os testes continuam certos)


# pega só os estados das etapas (feito, atual ou proximo), pra ficar fácil de comparar
def pegar_estados(status):
    estados = []
    for etapa in acompanhamento.montar_etapas(status):
        estados.append(etapa["estado"])
    return estados


# em que etapa o pedido deveria estar 

def test_logo_depois_de_confirmar_o_status_e_confirmado():
    assert acompanhamento.status_esperado(0) == "CONFIRMADO"

def test_no_segundo_em_que_comeca_o_preparo():
    segundos = acompanhamento.SEGUNDOS_DE_CADA_ETAPA["EM_PREPARO"]
    assert acompanhamento.status_esperado(segundos) == "EM_PREPARO"

def test_um_segundo_antes_do_preparo_ainda_e_confirmado():
    segundos = acompanhamento.SEGUNDOS_DE_CADA_ETAPA["EM_PREPARO"] - 1
    assert acompanhamento.status_esperado(segundos) == "CONFIRMADO"

def test_no_segundo_em_que_sai_pra_entrega():
    segundos = acompanhamento.SEGUNDOS_DE_CADA_ETAPA["SAIU_PARA_ENTREGA"]
    assert acompanhamento.status_esperado(segundos) == "SAIU_PARA_ENTREGA"

def test_um_segundo_antes_de_sair_ainda_esta_em_preparo():
    segundos = acompanhamento.SEGUNDOS_DE_CADA_ETAPA["SAIU_PARA_ENTREGA"] - 1
    assert acompanhamento.status_esperado(segundos) == "EM_PREPARO"

def test_no_segundo_da_entrega():
    segundos = acompanhamento.SEGUNDOS_DE_CADA_ETAPA["ENTREGUE"]
    assert acompanhamento.status_esperado(segundos) == "ENTREGUE"

def test_muito_tempo_depois_continua_entregue():
    assert acompanhamento.status_esperado(100000) == "ENTREGUE"

def test_os_tempos_das_etapas_crescem_na_ordem():
    # cada etapa tem que começar depois da anterior (senão o pedido andaria pra trás)
    anterior = -1
    for etapa in acompanhamento.ETAPAS:
        assert acompanhamento.SEGUNDOS_DE_CADA_ETAPA[etapa] > anterior
        anterior = acompanhamento.SEGUNDOS_DE_CADA_ETAPA[etapa]

def test_toda_etapa_tem_texto_descricao_tempo_e_estimativa():
    for etapa in acompanhamento.ETAPAS:
        assert etapa in acompanhamento.TEXTOS
        assert etapa in acompanhamento.DESCRICOES
        assert etapa in acompanhamento.SEGUNDOS_DE_CADA_ETAPA
        assert etapa in acompanhamento.QUANTO_FALTA


# posição da etapa 

def test_posicao_de_cada_etapa():
    assert acompanhamento.posicao_da_etapa("CONFIRMADO") == 0
    assert acompanhamento.posicao_da_etapa("EM_PREPARO") == 1
    assert acompanhamento.posicao_da_etapa("SAIU_PARA_ENTREGA") == 2
    assert acompanhamento.posicao_da_etapa("ENTREGUE") == 3

def test_status_fora_das_etapas_nao_tem_posicao():
    assert acompanhamento.posicao_da_etapa("CANCELADO") == -1
    assert acompanhamento.posicao_da_etapa("AGUARDANDO_PAGAMENTO") == -1


# lista de etapas pra tela 

def test_tem_4_etapas_com_os_textos_certos():
    etapas = acompanhamento.montar_etapas("CONFIRMADO")
    assert len(etapas) == 4
    assert etapas[0]["texto"] == "Pedido confirmado"
    assert etapas[1]["texto"] == "Em preparo"
    assert etapas[2]["texto"] == "Saiu para entrega"
    assert etapas[3]["texto"] == "Entregue"

def test_etapas_quando_acabou_de_confirmar():
    assert pegar_estados("CONFIRMADO") == ["atual", "proximo", "proximo", "proximo"]

def test_etapas_em_preparo():
    assert pegar_estados("EM_PREPARO") == ["feito", "atual", "proximo", "proximo"]

def test_etapas_saiu_para_entrega():
    assert pegar_estados("SAIU_PARA_ENTREGA") == ["feito", "feito", "atual", "proximo"]

def test_etapas_entregue_estao_todas_feitas():
    assert pegar_estados("ENTREGUE") == ["feito", "feito", "feito", "feito"]

def test_etapas_de_status_fora_do_fluxo_estao_todas_por_vir():
    assert pegar_estados("CANCELADO") == ["proximo", "proximo", "proximo", "proximo"]


# estimativa de minutos (muda quando o status muda) 

def test_estimativa_logo_depois_de_confirmar_e_o_tempo_todo():
    assert acompanhamento.estimar_minutos("CONFIRMADO", 40) == 40


def test_estimativa_em_preparo():
    assert acompanhamento.estimar_minutos("EM_PREPARO", 40) == 30

def test_estimativa_quando_saiu_pra_entrega():
    # 40% de 40 minutos é 16, e arredonda pra 15
    assert acompanhamento.estimar_minutos("SAIU_PARA_ENTREGA", 40) == 15

def test_estimativa_arredonda_de_5_em_5():
    # 40% de 30 minutos é 12, e arredonda pra 10
    assert acompanhamento.estimar_minutos("SAIU_PARA_ENTREGA", 30) == 10
    # 75% de 70 minutos é 52,5, e arredonda pra 55
    assert acompanhamento.estimar_minutos("EM_PREPARO", 70) == 55

def test_estimativa_nunca_e_menos_de_5_minutos_enquanto_nao_entregou():
    assert acompanhamento.estimar_minutos("SAIU_PARA_ENTREGA", 10) == 5

def test_estimativa_do_pedido_entregue_e_zero():
    assert acompanhamento.estimar_minutos("ENTREGUE", 40) == 0

def test_estimativa_de_status_fora_do_fluxo_e_zero():
    assert acompanhamento.estimar_minutos("CANCELADO", 40) == 0

def test_estimativa_sem_tempo_previsto_e_zero():
    assert acompanhamento.estimar_minutos("CONFIRMADO", 0) == 0


# frase da previsão 

def test_frase_da_previsao_enquanto_nao_entregou():
    frase = acompanhamento.frase_da_previsao("EM_PREPARO", 40, "")
    assert frase == "Previsão de entrega: cerca de 30 min."

def test_frase_quando_ja_entregou():
    frase = acompanhamento.frase_da_previsao("ENTREGUE", 40, "hoje às 19:40")
    assert frase == "Entregue hoje às 19:40."

def test_frase_entregue_sem_horario():
    assert acompanhamento.frase_da_previsao("ENTREGUE", 40, "") == "Entregue."

def test_frase_sem_tempo_previsto_fica_vazia():
    assert acompanhamento.frase_da_previsao("CONFIRMADO", 0, "") == ""
