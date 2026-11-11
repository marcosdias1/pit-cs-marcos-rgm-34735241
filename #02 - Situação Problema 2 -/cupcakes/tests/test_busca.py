from models import produto_model

# testes da busca (tirar acentos e filtrar a lista de cupcakes)
# esses testes NÃO mexem no banco, usam uma lista de mentira


# lista de cupcakes de mentira pra testar
def pegar_lista():
    lista = []
    lista.append({"id": 1, "nome": "Limão", "ingredientes": "farinha, suco de limão, açúcar, leite"})
    lista.append({"id": 2, "nome": "Queijo e Orégano", "ingredientes": "farinha, queijo, orégano, ovo"})
    lista.append({"id": 3, "nome": "Red Velvet", "ingredientes": "farinha, cacau, buttermilk, corante"})
    return lista

# pega só os ids do resultado, pra ficar fácil de comparar
def pegar_ids(lista):
    ids = []
    for cupcake in lista:
        ids.append(cupcake["id"])
    return ids


# tirar acentos 

def test_tirar_acentos_do_limao():
    assert produto_model.tirar_acentos("Limão") == "limao"

def test_tirar_acentos_e_deixar_minusculo():
    assert produto_model.tirar_acentos("ORÉGANO") == "oregano"

def test_tirar_acentos_do_cedilha():
    assert produto_model.tirar_acentos("Cupuaçu") == "cupuacu"


# filtrar pela busca 

def test_busca_ignora_acento_e_maiuscula():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "LIMAO")
    assert pegar_ids(resultado) == [1]

def test_busca_pelo_ingrediente():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "oregano")
    assert pegar_ids(resultado) == [2]

def test_busca_pelo_ingrediente_sem_acento():
    # no banco está "açúcar" e a pessoa digitou "acucar"
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "acucar")
    assert pegar_ids(resultado) == [1]

def test_busca_com_duas_palavras():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "red velvet")
    assert pegar_ids(resultado) == [3]

def test_busca_com_palavras_em_ordem_trocada():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "velvet red")
    assert pegar_ids(resultado) == [3]

def test_busca_com_pedaco_da_palavra():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "velv")
    assert pegar_ids(resultado) == [3]

def test_busca_que_aparece_em_todos():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "farinha")
    assert pegar_ids(resultado) == [1, 2, 3]

def test_busca_que_nao_acha_nada():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "pizza")
    assert resultado == []

def test_busca_vazia_devolve_tudo():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "")
    assert len(resultado) == 3

def test_busca_so_com_espacos_devolve_tudo():
    resultado = produto_model.filtrar_por_busca(pegar_lista(), "     ")
    assert len(resultado) == 3