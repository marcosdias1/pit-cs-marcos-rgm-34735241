# testes das regras do Meu perfil: dados da conta e endereços (cartão 20)


from models import perfil_regras


# um endereço certo, pra usar nos testes (cada teste troca só o que quer testar)
def conferir(apelido="Casa", cep="01001-000", rua="Praça da Sé", numero="10", complemento="",
             bairro="Sé", cidade="São Paulo", uf="SP"):
    return perfil_regras.conferir_endereco_do_perfil(apelido, cep, rua, numero, complemento,
                                                     bairro, cidade, uf)


# cep 

def test_cep_ganha_o_traco():
    assert perfil_regras.formatar_cep("01001000") == "01001-000"

def test_cep_que_nao_tem_8_numeros_volta_como_veio():
    assert perfil_regras.formatar_cep("123") == "123"


# celular 

def test_celular_de_11_numeros():
    assert perfil_regras.formatar_celular("11900001111") == "(11) 90000-1111"

def test_celular_de_10_numeros():
    assert perfil_regras.formatar_celular("1133334444") == "(11) 3333-4444"

def test_celular_que_ja_vem_com_enfeites_fica_igual():
    assert perfil_regras.formatar_celular("(11) 90000-1111") == "(11) 90000-1111"

def test_celular_estranho_volta_como_veio():
    assert perfil_regras.formatar_celular("123") == "123"
    assert perfil_regras.formatar_celular("abc") == "abc"


# cpf escondido 

def test_cpf_aparece_escondido():
    assert perfil_regras.mascarar_cpf("12345678909") == "***.456.789-**"

def test_cpf_mascarado_nao_tem_os_numeros_do_comeco_nem_do_fim():
    texto = perfil_regras.mascarar_cpf("12345678909")
    assert "123" not in texto
    assert "09" not in texto

def test_cpf_com_tamanho_estranho_volta_como_veio():
    assert perfil_regras.mascarar_cpf("123") == "123"


# conferência do endereço 

def test_endereco_certo_nao_tem_erro():
    assert conferir() == {}

def test_apelido_e_complemento_sao_opcionais():
    assert conferir(apelido="", complemento="") == {}

def test_cep_errado():
    assert "cep" in conferir(cep="123")

def test_rua_numero_bairro_cidade_obrigatorios():
    erros = conferir(rua="", numero="", bairro="", cidade="")
    assert "rua" in erros
    assert "numero" in erros
    assert "bairro" in erros
    assert "cidade" in erros

def test_uf_invalida():
    assert "uf" in conferir(uf="XX")

def test_apelido_muito_grande():
    assert "apelido" in conferir(apelido="a" * 31)
    assert "apelido" not in conferir(apelido="a" * 30)

def test_complemento_muito_grande():
    assert "complemento" in conferir(complemento="a" * 61)
    assert "complemento" not in conferir(complemento="a" * 60)


# nome e resumo 

def test_nome_do_endereco_usa_o_apelido():
    assert perfil_regras.nome_do_endereco("Casa") == "Casa"

def test_endereco_sem_apelido_se_chama_endereco():
    assert perfil_regras.nome_do_endereco(None) == "Endereço"
    assert perfil_regras.nome_do_endereco("") == "Endereço"

def test_resumo_sem_complemento():
    texto = perfil_regras.resumir_endereco("Rua A", "10", None, "Centro", "São Paulo", "SP", "01001000")
    assert texto == "Rua A, 10 - Centro, São Paulo/SP - CEP 01001-000"

def test_resumo_com_complemento():
    texto = perfil_regras.resumir_endereco("Rua A", "10", "apto 2", "Centro", "São Paulo", "SP", "01001000")
    assert texto == "Rua A, 10 - apto 2 - Centro, São Paulo/SP - CEP 01001-000"

def test_resumo_com_complemento_vazio_ignora_ele():
    texto = perfil_regras.resumir_endereco("Rua A", "10", "", "Centro", "São Paulo", "SP", "01001000")
    assert "-  -" not in texto
    assert texto.startswith("Rua A, 10 - Centro")


# quando pode excluir 

def test_endereco_comum_pode_ser_excluido():
    assert perfil_regras.motivo_para_nao_excluir(False, 3) == ""

def test_principal_com_outros_enderecos_nao_pode_ser_excluido():
    motivo = perfil_regras.motivo_para_nao_excluir(True, 2)
    assert "principal" in motivo

def test_principal_unico_pode_ser_excluido():
    assert perfil_regras.motivo_para_nao_excluir(True, 1) == ""

def test_limite_de_enderecos_e_5():
    assert perfil_regras.MAXIMO_DE_ENDERECOS == 5