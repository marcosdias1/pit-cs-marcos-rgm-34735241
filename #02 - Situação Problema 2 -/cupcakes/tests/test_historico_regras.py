# testes das regras do histórico de compras e da recompra (cartão 15)

from datetime import datetime
from models import historico_regras


# texto do status 

def test_texto_de_cada_status():
    assert historico_regras.texto_do_status("CONFIRMADO") == "Pedido confirmado"
    assert historico_regras.texto_do_status("EM_PREPARO") == "Em preparo"
    assert historico_regras.texto_do_status("SAIU_PARA_ENTREGA") == "Saiu para entrega"
    assert historico_regras.texto_do_status("ENTREGUE") == "Entregue"
    assert historico_regras.texto_do_status("CANCELADO") == "Cancelado"
    assert historico_regras.texto_do_status("AGUARDANDO_PAGAMENTO") == "Aguardando pagamento"

def test_status_desconhecido_volta_como_veio():
    assert historico_regras.texto_do_status("OUTRO") == "OUTRO"


# botão Acompanhar 

def test_pedidos_andando_e_entregues_podem_ser_acompanhados():
    assert historico_regras.pode_acompanhar("CONFIRMADO") == True
    assert historico_regras.pode_acompanhar("EM_PREPARO") == True
    assert historico_regras.pode_acompanhar("SAIU_PARA_ENTREGA") == True
    assert historico_regras.pode_acompanhar("ENTREGUE") == True

def test_cancelado_e_nao_pago_nao_tem_acompanhamento():
    assert historico_regras.pode_acompanhar("CANCELADO") == False
    assert historico_regras.pode_acompanhar("AGUARDANDO_PAGAMENTO") == False


# pedido ainda andando 

def test_pedido_em_andamento():
    assert historico_regras.esta_em_andamento("CONFIRMADO") == True
    assert historico_regras.esta_em_andamento("EM_PREPARO") == True
    assert historico_regras.esta_em_andamento("SAIU_PARA_ENTREGA") == True

def test_pedido_que_terminou_nao_esta_em_andamento():
    assert historico_regras.esta_em_andamento("ENTREGUE") == False
    assert historico_regras.esta_em_andamento("CANCELADO") == False
    assert historico_regras.esta_em_andamento("AGUARDANDO_PAGAMENTO") == False


# data 

def test_formatar_data():
    data = datetime(2026, 11, 8, 18, 5, 0)
    assert historico_regras.formatar_data(data) == "08/11/2026 às 18:05"

def test_formatar_data_vazia():
    assert historico_regras.formatar_data(None) == ""


# resumo dos itens 

def test_resumo_de_um_item():
    itens = [{"nome": "Chocolate", "quantidade": 2}]
    assert historico_regras.resumir_itens(itens) == "2x Chocolate"

def test_resumo_de_tres_itens_mostra_todos():
    itens = [{"nome": "Chocolate", "quantidade": 2},
             {"nome": "Morango", "quantidade": 1},
             {"nome": "Baunilha", "quantidade": 3}]
    assert historico_regras.resumir_itens(itens) == "2x Chocolate, 1x Morango, 3x Baunilha"

def test_resumo_com_quatro_itens_fala_de_mais_um():
    itens = [{"nome": "A", "quantidade": 1}, {"nome": "B", "quantidade": 1},
             {"nome": "C", "quantidade": 1}, {"nome": "D", "quantidade": 1}]
    assert historico_regras.resumir_itens(itens) == "1x A, 1x B, 1x C e mais 1 item"

def test_resumo_com_muitos_itens_fala_de_mais_varios():
    itens = []
    for i in range(6):
        itens.append({"nome": "Item" + str(i), "quantidade": 1})
    assert historico_regras.resumir_itens(itens) == "1x Item0, 1x Item1, 1x Item2 e mais 3 itens"

def test_resumo_sem_itens_fica_vazio():
    assert historico_regras.resumir_itens([]) == ""

def test_resumo_aceita_outro_maximo():
    itens = [{"nome": "A", "quantidade": 1}, {"nome": "B", "quantidade": 1}]
    assert historico_regras.resumir_itens(itens, 1) == "1x A e mais 1 item"


# mensagens da recompra 

def test_mensagem_de_tudo_certo_com_um_item():
    ok, aviso = historico_regras.montar_mensagens_da_recompra(1, [])
    assert ok == "1 item foi para o carrinho. Os preços são os de hoje."
    assert aviso == ""

def test_mensagem_de_tudo_certo_com_varios_itens():
    ok, aviso = historico_regras.montar_mensagens_da_recompra(3, [])
    assert ok == "3 itens foram para o carrinho. Os preços são os de hoje."
    assert aviso == ""

def test_mensagem_quando_um_item_nao_foi():
    problemas = [{"nome": "Morango", "motivo": "Esse produto está sem estoque no momento."}]
    ok, aviso = historico_regras.montar_mensagens_da_recompra(2, problemas)
    assert "2 itens" in ok
    assert aviso == "Não deu para colocar no carrinho. Morango: Esse produto está sem estoque no momento."

def test_mensagem_quando_varios_itens_nao_foram():
    problemas = [{"nome": "A", "motivo": "Sem estoque."}, {"nome": "B", "motivo": "Só temos 1."}]
    ok, aviso = historico_regras.montar_mensagens_da_recompra(0, problemas)
    assert ok == ""
    assert aviso == "Não deu para colocar no carrinho. A: Sem estoque. B: Só temos 1."

def test_sem_nada_nao_tem_mensagem():
    ok, aviso = historico_regras.montar_mensagens_da_recompra(0, [])
    assert ok == ""
    assert aviso == ""

def test_limite_da_lista_e_20():
    assert historico_regras.LIMITE_DE_PEDIDOS == 20
