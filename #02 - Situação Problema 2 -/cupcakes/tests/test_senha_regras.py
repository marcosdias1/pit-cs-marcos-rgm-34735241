# testes das regras da recuperação de senha (cartão 19)

from models import senha_regras


# validade do link 

def test_o_link_vale_60_minutos():
    # regra do cartão 19: o link vale 1 hora
    assert senha_regras.MINUTOS_DE_VALIDADE == 60


# token novo 

def test_token_e_grande_e_so_tem_letras_e_numeros_do_link():
    token = senha_regras.gerar_token()
    assert len(token) >= 40
    for letra in token:
        assert letra in senha_regras.LETRAS_DO_TOKEN

def test_dois_tokens_nunca_sao_iguais():
    assert senha_regras.gerar_token() != senha_regras.gerar_token()

def test_token_novo_passa_na_conferencia_de_formato():
    assert senha_regras.token_parece_valido(senha_regras.gerar_token()) == True


# hash do token 

def test_hash_tem_64_letras_e_numeros():
    # a coluna token_hash do banco é CHAR(64)
    hash_do_token = senha_regras.hash_do_token("abc")
    assert len(hash_do_token) == 64
    for letra in hash_do_token:
        assert letra in "0123456789abcdef"

def test_mesmo_token_sempre_da_o_mesmo_hash():
    assert senha_regras.hash_do_token("abc") == senha_regras.hash_do_token("abc")

def test_tokens_diferentes_dao_hashes_diferentes():
    assert senha_regras.hash_do_token("abc") != senha_regras.hash_do_token("abd")

def test_o_hash_nao_e_o_proprio_token():
    token = senha_regras.gerar_token()
    assert senha_regras.hash_do_token(token) != token


# formato do token 

def test_token_curto_demais_nao_vale():
    assert senha_regras.token_parece_valido("abc") == False

def test_token_vazio_nao_vale():
    assert senha_regras.token_parece_valido("") == False

def test_token_grande_demais_nao_vale():
    assert senha_regras.token_parece_valido("a" * 101) == False

def test_token_com_simbolo_estranho_nao_vale():
    assert senha_regras.token_parece_valido("a" * 30 + "'; DROP TABLE") == False
    assert senha_regras.token_parece_valido("a" * 30 + " ") == False
    assert senha_regras.token_parece_valido("a" * 30 + "%") == False

def test_token_com_tamanho_limite_vale():
    assert senha_regras.token_parece_valido("a" * 20) == True
    assert senha_regras.token_parece_valido("a" * 100) == True
    assert senha_regras.token_parece_valido("a" * 19) == False


# e-mail 

def test_email_tem_o_nome_o_link_e_a_validade():
    assunto, texto = senha_regras.montar_email("Ana", "http://localhost:5000/redefinir-senha/xyz")
    assert "senha" in assunto.lower()
    assert "Olá, Ana!" in texto
    assert "http://localhost:5000/redefinir-senha/xyz" in texto
    assert "60 minutos" in texto
    assert "só pode ser usado uma vez" in texto

def test_email_avisa_que_pode_ignorar():
    assunto, texto = senha_regras.montar_email("Ana", "http://x/y")
    assert "ignore" in texto
