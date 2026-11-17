from datetime import date
from models import cancelamento_regras
from models import acompanhamento
from models import evento_regras

# testes das regras novas da rodada de melhorias (depois dos testes com os 5 colegas)
# cobre: cancelamento de pedido, aviso de saída do acompanhamento e textos das encomendas de evento

# cancelamento_regras

def test_pedido_confirmado_pode_cancelar():
    assert cancelamento_regras.pode_cancelar("CONFIRMADO") == True

def test_pedido_em_preparo_pode_cancelar():
    assert cancelamento_regras.pode_cancelar("EM_PREPARO") == True

def test_pedido_que_saiu_para_entrega_nao_pode_cancelar():
    assert cancelamento_regras.pode_cancelar("SAIU_PARA_ENTREGA") == False

def test_pedido_entregue_nao_pode_cancelar():
    assert cancelamento_regras.pode_cancelar("ENTREGUE") == False

def test_pedido_ja_cancelado_nao_pode_cancelar_de_novo():
    assert cancelamento_regras.pode_cancelar("CANCELADO") == False

def test_pedido_que_nao_foi_pago_nao_pode_cancelar():
    assert cancelamento_regras.pode_cancelar("AGUARDANDO_PAGAMENTO") == False

def test_status_desconhecido_nao_pode_cancelar():
    assert cancelamento_regras.pode_cancelar("QUALQUER_COISA") == False
    assert cancelamento_regras.pode_cancelar("") == False

def test_motivo_de_cada_status_que_nao_pode_cancelar():
    assert "saiu para entrega" in cancelamento_regras.motivo_de_nao_poder("SAIU_PARA_ENTREGA")
    assert "entregue" in cancelamento_regras.motivo_de_nao_poder("ENTREGUE")
    assert "já foi cancelado" in cancelamento_regras.motivo_de_nao_poder("CANCELADO")
    assert "ainda não foi pago" in cancelamento_regras.motivo_de_nao_poder("AGUARDANDO_PAGAMENTO")

def test_motivo_de_status_desconhecido_e_generico():
    assert cancelamento_regras.motivo_de_nao_poder("XYZ") == "Esse pedido não pode ser cancelado."

def test_todo_status_que_pode_cancelar_esta_na_lista_de_status_do_acompanhamento():
    # o cancelamento só vale pra quem está andando na linha do tempo
    for status in cancelamento_regras.STATUS_QUE_PODEM_CANCELAR:
        assert status in acompanhamento.ETAPAS

def test_mensagem_de_cancelado_tem_o_numero_e_avisa_que_o_pagamento_e_de_demonstracao():
    texto = cancelamento_regras.mensagem_de_cancelado(10050)
    assert "#10050" in texto
    assert "estoque" in texto
    assert "demonstração" in texto


# aviso "vamos avisar quando sair para entrega" (item 17) ----------

def test_aviso_de_saida_aparece_antes_de_sair_para_entrega():
    assert acompanhamento.vai_avisar_saida("CONFIRMADO") == True
    assert acompanhamento.vai_avisar_saida("EM_PREPARO") == True

def test_aviso_de_saida_some_depois_que_saiu():
    assert acompanhamento.vai_avisar_saida("SAIU_PARA_ENTREGA") == False
    assert acompanhamento.vai_avisar_saida("ENTREGUE") == False
    assert acompanhamento.vai_avisar_saida("CANCELADO") == False


#  textos das encomendas de evento (item 3)

def test_texto_da_situacao_da_encomenda():
    assert evento_regras.texto_do_status_da_encomenda("RECEBIDA") == "Recebida, aguardando o orçamento"
    assert evento_regras.texto_do_status_da_encomenda("ORCADA") == "Orçamento enviado"
    assert evento_regras.texto_do_status_da_encomenda("CANCELADA") == "Cancelada"

def test_situacao_desconhecida_da_encomenda_volta_ela_mesma():
    assert evento_regras.texto_do_status_da_encomenda("OUTRA") == "OUTRA"

def test_data_do_evento_escrita_com_dia_mes_e_ano():
    assert evento_regras.formatar_data_do_evento(date(2026, 11, 30)) == "30/11/2026"
    assert evento_regras.formatar_data_do_evento(date(2027, 1, 5)) == "05/01/2027"

def test_data_do_evento_vazia_vira_texto_vazio():
    assert evento_regras.formatar_data_do_evento(None) == ""

def test_resumo_da_encomenda_com_tema():
    assert evento_regras.resumir_encomenda(50, "Unicórnio") == "50 cupcakes, tema Unicórnio"

def test_resumo_da_encomenda_sem_tema():
    assert evento_regras.resumir_encomenda(30, None) == "30 cupcakes"
    assert evento_regras.resumir_encomenda(30, "") == "30 cupcakes"
