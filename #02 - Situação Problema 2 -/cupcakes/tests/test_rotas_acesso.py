from app import app

# testes das rotas de acesso (login, cadastro e visitante)
# esses testes NÃO mexem no banco: só testam o que acontece antes de chegar nele


# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
    return navegador

def test_pagina_inicial_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/")
    # 302 quer dizer que redirecionou
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_tela_de_login_abre():
    navegador = pegar_navegador()
    resposta = navegador.get("/login")
    assert resposta.status_code == 200
    texto = resposta.data.decode("utf-8")
    assert "Continuar como visitante" in texto
    assert "Criar uma conta" in texto

def test_tela_de_cadastro_abre():
    navegador = pegar_navegador()
    resposta = navegador.get("/cadastro")
    assert resposta.status_code == 200

def test_login_com_cpf_invalido_mostra_erro_e_mantem_o_cpf():
    navegador = pegar_navegador()
    resposta = navegador.post("/login", data={"cpf": "111.111.111-11", "senha": "qualquer"})
    texto = resposta.data.decode("utf-8")
    assert resposta.status_code == 200
    assert "CPF inválido" in texto
    # o que a pessoa digitou não pode sumir
    assert "111.111.111-11" in texto

def test_login_sem_senha_pede_a_senha():
    navegador = pegar_navegador()
    resposta = navegador.post("/login", data={"cpf": "390.533.447-05", "senha": ""})
    texto = resposta.data.decode("utf-8")
    assert "Digite sua senha." in texto

def test_cadastro_com_senha_fraca_mostra_erro():
    navegador = pegar_navegador()
    dados = {
        "nome": "Ana Souza", "email": "ana@gmail.com", "celular": "11900000001",
        "cpf": "39053344705", "senha": "fraca", "cep": "01001000",
        "rua": "Rua das Flores", "numero": "10", "bairro": "Centro",
        "cidade": "São Paulo", "uf": "SP",
    }
    resposta = navegador.post("/cadastro", data=dados)
    texto = resposta.data.decode("utf-8")
    assert resposta.status_code == 200
    assert "A senha precisa ter no mínimo 8 caracteres" in texto
    assert "fraca" not in texto

def test_visitante_fica_marcado_na_sessao():
    navegador = pegar_navegador()
    resposta = navegador.get("/visitante")
    assert resposta.status_code == 302
    with navegador.session_transaction() as sessao:
        assert sessao["tipo"] == "visitante"

def test_logout_limpa_a_sessao():
    navegador = pegar_navegador()
    navegador.get("/visitante")
    navegador.get("/logout")
    with navegador.session_transaction() as sessao:
        assert "tipo" not in sessao