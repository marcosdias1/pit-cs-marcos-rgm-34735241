from models import validacoes

# testes das funções de validação (cpf, senha, email, celular e cadastro)
# pra rodar: pytest


# cpf 
def test_cpf_valido_com_pontos():
    resultado = validacoes.validar_cpf("390.533.447-05")
    assert resultado == True

def test_cpf_valido_sem_pontos():
    resultado = validacoes.validar_cpf("39053344705")
    assert resultado == True

def test_cpf_com_digito_errado():
    # troquei o último número de 5 pra 6
    resultado = validacoes.validar_cpf("39053344706")
    assert resultado == False

def test_cpf_todos_iguais():
    resultado = validacoes.validar_cpf("11111111111")
    assert resultado == False

def test_cpf_curto():
    resultado = validacoes.validar_cpf("123456789")
    assert resultado == False

def test_cpf_com_letra():
    resultado = validacoes.validar_cpf("3905334470a")
    assert resultado == False

def test_cpf_vazio():
    resultado = validacoes.validar_cpf("")
    assert resultado == False


# senha 
def test_senha_boa():
    resultado = validacoes.validar_senha("Cupcake@123")
    assert resultado == True

def test_senha_com_exatamente_9_caracteres():
    # mais de 8 quer dizer 9 ou mais
    resultado = validacoes.validar_senha("Cupcake@1")
    assert resultado == True

def test_senha_com_7_caracteres_nao_vale():
    resultado = validacoes.validar_senha("Cupca@1")
    assert resultado == False

def test_senha_com_exatamente_8_caracteres_vale():
    resultado = validacoes.validar_senha("Cupcak@1")
    assert resultado == True

def test_senha_sem_maiuscula():
    resultado = validacoes.validar_senha("cupcake@123")
    assert resultado == False

def test_senha_sem_caractere_especial():
    resultado = validacoes.validar_senha("Cupcake1234")
    assert resultado == False


# email, celular e cep 
def test_email_valido():
    assert validacoes.validar_email("ana@gmail.com") == True

def test_email_sem_arroba():
    assert validacoes.validar_email("anagmail.com") == False

def test_email_sem_ponto_depois_do_arroba():
    assert validacoes.validar_email("ana@gmail") == False

def test_celular_valido_com_enfeites():
    assert validacoes.validar_celular("(11) 90000-0001") == True

def test_celular_curto():
    assert validacoes.validar_celular("1190000") == False

def test_cep_valido():
    assert validacoes.validar_cep("01001-000") == True

def test_cep_curto():
    assert validacoes.validar_cep("0100") == False

# cadastro inteiro 
def test_cadastro_tudo_certo_nao_tem_erros():
    erros = validacoes.conferir_cadastro("Ana Souza", "ana@gmail.com", "(11) 90000-0001",
                                         "390.533.447-05", "Cupcake@123", "01001-000",
                                         "Rua das Flores", "10", "Centro", "São Paulo", "SP")
    assert len(erros) == 0

def test_cadastro_tudo_vazio_tem_erros():
    erros = validacoes.conferir_cadastro("", "", "", "", "", "", "", "", "", "", "")
    # tem que dar erro em todos os 11 campos
    assert len(erros) == 11

def test_cadastro_com_senha_fraca_so_erra_a_senha():
    erros = validacoes.conferir_cadastro("Ana Souza", "ana@gmail.com", "11900000001",
                                         "39053344705", "123", "01001000",
                                         "Rua das Flores", "10", "Centro", "São Paulo", "SP")
    assert len(erros) == 1
    assert "senha" in erros