# testes das regras do orçamento de evento (cartão 08)

from datetime import date
from models import evento_regras

# "hoje" fixo, pra os testes darem sempre o mesmo resultado
HOJE = date(2026, 11, 8)


# um pedido certo, pra usar nos testes (cada teste troca só o que quer testar)
def conferir(nome="Ana Teste", email="ana@gmail.com", celular="(11) 90000-1111", data_texto="2026-11-20", quantidade_texto="50", tema="", observacoes=""):
    return evento_regras.conferir_pedido_de_evento(nome, email, celular, data_texto, quantidade_texto, tema, observacoes, HOJE)

def campos_de_mentira(tema="Aniversário", observacoes="Sem amendoim"):
    campos = {}
    campos["nome"] = "Ana Teste"
    campos["email"] = "ana@gmail.com"
    campos["celular"] = "11900001111"
    campos["data_evento"] = date(2026, 11, 20)
    campos["quantidade"] = 50
    campos["tema"] = tema
    campos["observacoes"] = observacoes
    return campos


# números do cartão 

def test_o_minimo_do_cartao_08_e_30():
    assert evento_regras.MINIMO_DE_UNIDADES == 30


# ler a data 

def test_ler_data_no_formato_do_navegador():
    assert evento_regras.ler_data("2026-11-20") == date(2026, 11, 20)

def test_ler_data_no_formato_brasileiro():
    assert evento_regras.ler_data("20/11/2026") == date(2026, 11, 20)

def test_ler_data_vazia_ou_estranha():
    assert evento_regras.ler_data("") is None
    assert evento_regras.ler_data("amanhã") is None
    assert evento_regras.ler_data("20-11") is None

def test_ler_data_que_nao_existe():
    assert evento_regras.ler_data("2026-02-30") is None
    assert evento_regras.ler_data("31/04/2026") is None

def test_formatar_data():
    assert evento_regras.formatar_data(date(2026, 11, 5)) == "05/11/2026"

def test_primeira_e_ultima_data_aceita():
    assert evento_regras.primeira_data_aceita(HOJE) == date(2026, 11, 11)
    assert evento_regras.ultima_data_aceita(HOJE) == date(2027, 11, 8)


# quantidade abaixo do mínimo 

def test_abaixo_do_minimo():
    assert evento_regras.quantidade_abaixo_do_minimo("29") == True
    assert evento_regras.quantidade_abaixo_do_minimo("1") == True
    assert evento_regras.quantidade_abaixo_do_minimo("0") == True

def test_no_minimo_ou_acima_nao_e_abaixo():
    assert evento_regras.quantidade_abaixo_do_minimo("30") == False
    assert evento_regras.quantidade_abaixo_do_minimo("500") == False

def test_texto_que_nao_e_numero_nao_e_abaixo_do_minimo():
    assert evento_regras.quantidade_abaixo_do_minimo("") == False
    assert evento_regras.quantidade_abaixo_do_minimo("abc") == False
    assert evento_regras.quantidade_abaixo_do_minimo("-5") == False
    assert evento_regras.quantidade_abaixo_do_minimo("12345678") == False


# pedido certo 

def test_pedido_certo_nao_tem_erro():
    assert conferir() == {}

def test_tema_e_observacoes_sao_opcionais():
    assert conferir(tema="", observacoes="") == {}


# contato 

def test_contato_com_erros():
    erros = conferir(nome="", email="semarroba", celular="123")
    assert "nome" in erros
    assert "email" in erros
    assert "celular" in erros


# data do evento 

def test_data_vazia():
    assert "data" in conferir(data_texto="")

def test_data_que_nao_existe():
    assert "data" in conferir(data_texto="2026-02-30")

def test_data_que_ja_passou():
    assert "data" in conferir(data_texto="2026-11-01")

def test_data_de_hoje_e_amanha_nao_tem_antecedencia():
    assert "data" in conferir(data_texto="2026-11-08")
    assert "data" in conferir(data_texto="2026-11-09")
    assert "data" in conferir(data_texto="2026-11-10")

def test_primeira_data_com_antecedencia_vale():
    # 3 dias depois de 8/11 é 11/11
    assert "data" not in conferir(data_texto="2026-11-11")

def test_mensagem_da_data_diz_a_primeira_data_aceita():
    erros = conferir(data_texto="2026-11-09")
    assert "3 dias de antecedência" in erros["data"]
    assert "11/11/2026" in erros["data"]

def test_data_dentro_de_um_ano_vale():
    assert "data" not in conferir(data_texto="2027-11-08")

def test_data_depois_de_um_ano_nao_vale():
    assert "data" in conferir(data_texto="2027-11-09")

def test_data_no_formato_brasileiro_vale():
    assert "data" not in conferir(data_texto="20/11/2026")


# quantidade 

def test_29_cupcakes_nao_vale_e_manda_comprar_pelo_carrinho():
    erros = conferir(quantidade_texto="29")
    assert "quantidade" in erros
    assert "mínimo é de 30" in erros["quantidade"]
    assert "carrinho" in erros["quantidade"]

def test_30_cupcakes_vale():
    assert "quantidade" not in conferir(quantidade_texto="30")

def test_1000_cupcakes_vale_e_1001_nao():
    assert "quantidade" not in conferir(quantidade_texto="1000")
    assert "quantidade" in conferir(quantidade_texto="1001")

def test_quantidade_que_nao_e_numero():
    assert "quantidade" in conferir(quantidade_texto="")
    assert "quantidade" in conferir(quantidade_texto="abc")
    assert "quantidade" in conferir(quantidade_texto="5.5")
    assert "quantidade" in conferir(quantidade_texto="-30")

def test_quantidade_gigante_nao_quebra():
    assert "quantidade" in conferir(quantidade_texto="9" * 40)


# tema e observações 

def test_tema_com_100_letras_vale_e_101_nao():
    assert "tema" not in conferir(tema="a" * 100)
    assert "tema" in conferir(tema="a" * 101)

def test_observacoes_com_500_letras_valem_e_501_nao():
    assert "observacoes" not in conferir(observacoes="a" * 500)
    assert "observacoes" in conferir(observacoes="a" * 501)

def test_varios_erros_aparecem_juntos():
    erros = conferir(nome="", data_texto="", quantidade_texto="5", tema="a" * 101)
    assert "nome" in erros
    assert "data" in erros
    assert "quantidade" in erros
    assert "tema" in erros


# e-mails 

def test_email_da_loja_tem_todos_os_dados():
    assunto, texto = evento_regras.montar_email_para_a_loja(12, campos_de_mentira())
    assert "#12" in assunto
    assert "50 cupcakes" in assunto
    assert "Ana Teste" in texto
    assert "ana@gmail.com" in texto
    assert "11900001111" in texto
    assert "20/11/2026" in texto
    assert "Tema: Aniversário" in texto
    assert "Observações: Sem amendoim" in texto
    assert "2 dias úteis" in texto

def test_email_da_loja_nao_fala_de_tema_e_observacoes_vazios():
    assunto, texto = evento_regras.montar_email_para_a_loja(12, campos_de_mentira(None, None))
    assert "Tema:" not in texto
    assert "Observações:" not in texto

def test_email_do_cliente_tem_o_protocolo_e_o_prazo():
    assunto, texto = evento_regras.montar_email_para_o_cliente(12, campos_de_mentira())
    assert "#12" in assunto
    assert "Olá, Ana Teste!" in texto
    assert "50 cupcakes" in texto
    assert "20/11/2026" in texto
    assert "protocolo é #12" in texto
    assert "2 dias úteis" in texto
