# testes das rotas da recuperação de senha (cartão 19)

from app import app
from controllers import senha_controller
from models import carrinho_model
from models import email_simulado
from models import senha_model

# um cpf válido, um token com formato válido e outro com formato de lixo
CPF = "529.982.247-25"
TOKEN = "a" * 43


# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
    return navegador

def entrar_como_cliente():
    navegador = pegar_navegador()
    with navegador.session_transaction() as sessao:
        sessao["tipo"] = "cliente"
        sessao["id_cliente"] = 7
        sessao["nome"] = "Ana Teste"
    return navegador

def pegar_texto(resposta):
    return resposta.data.decode("utf-8")

def pegar_mensagens(navegador):
    with navegador.session_transaction() as sessao:
        lista = sessao.get("_flashes", [])
    textos = []
    for categoria, texto in lista:
        textos.append(categoria + ": " + texto)
    return textos

def contador_zero(id_cliente, id_sessao):
    return 0


# função que dá erro de propósito (o * faz ela aceitar qualquer quantidade de argumentos)
def erro_de_mentira(*args):
    raise Exception("o banco caiu (de mentira)")


# troca as funções do pedido de link pelas de mentira
# existe_conta: se True, o cpf "tem conta" e o model devolve um token
# devolve a lista de cpfs consultados e a lista de e-mails enviados
def preparar_pedido_de_link(monkeypatch, existe_conta):
    cpfs = []
    emails = []

    def criar_token(cpf):
        cpfs.append(cpf)
        if existe_conta == False:
            return None
        return {"nome": "Ana Teste", "email": "ana@gmail.com", "token": TOKEN}

    def enviar(destino, assunto, texto):
        emails.append({"destino": destino, "assunto": assunto, "texto": texto})

    monkeypatch.setattr(senha_model, "criar_token_de_recuperacao", criar_token)
    monkeypatch.setattr(email_simulado, "enviar", enviar)
    monkeypatch.setattr(senha_controller, "MOSTRAR_LINK_DE_SENHA_NA_TELA", False)
    return cpfs, emails


# ESQUECI MINHA SENHA 

def test_tela_esqueci_senha_abre():
    navegador = pegar_navegador()
    resposta = navegador.get("/esqueci-senha")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert 'name="cpf"' in texto
    assert "Enviar o link" in texto

def test_cliente_logado_nao_precisa_da_tela():
    navegador = entrar_como_cliente()
    resposta = navegador.get("/esqueci-senha")
    assert resposta.status_code == 302

def test_cpf_invalido_nem_pergunta_pro_banco(monkeypatch):
    cpfs, emails = preparar_pedido_de_link(monkeypatch, True)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/esqueci-senha", data={"cpf": "111.111.111-11"}))
    assert "CPF inválido" in texto
    assert cpfs == []
    assert emails == []

def test_cpf_com_conta_manda_o_email_com_o_link(monkeypatch):
    cpfs, emails = preparar_pedido_de_link(monkeypatch, True)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/esqueci-senha", data={"cpf": CPF}))
    assert "Se esse CPF tem conta, enviamos um link para o e-mail cadastrado." in texto
    # o cpf vai pro banco só com números
    assert cpfs == ["52998224725"]
    assert len(emails) == 1
    assert emails[0]["destino"] == "ana@gmail.com"
    assert "/redefinir-senha/" + TOKEN in emails[0]["texto"]
    assert "Ana Teste" in emails[0]["texto"]

def test_cpf_sem_conta_responde_igual_e_nao_manda_email(monkeypatch):
    cpfs, emails = preparar_pedido_de_link(monkeypatch, False)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/esqueci-senha", data={"cpf": CPF}))
    # a mesma resposta de quando tem conta (ninguém descobre quais cpfs têm conta)
    assert "Se esse CPF tem conta, enviamos um link para o e-mail cadastrado." in texto
    assert cpfs == ["52998224725"]
    assert emails == []

def test_a_tela_avisa_a_validade_do_link(monkeypatch):
    preparar_pedido_de_link(monkeypatch, True)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/esqueci-senha", data={"cpf": CPF}))
    assert "60 minutos" in texto
    assert "só pode ser usado uma vez" in texto

def test_link_nao_aparece_na_tela_fora_da_demonstracao(monkeypatch):
    preparar_pedido_de_link(monkeypatch, True)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/esqueci-senha", data={"cpf": CPF}))
    assert TOKEN not in texto
    assert "o e-mail é simulado e aparece no terminal" in texto

def test_link_aparece_na_tela_no_modo_de_demonstracao(monkeypatch):
    preparar_pedido_de_link(monkeypatch, True)
    monkeypatch.setattr(senha_controller, "MOSTRAR_LINK_DE_SENHA_NA_TELA", True)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/esqueci-senha", data={"cpf": CPF}))
    assert "/redefinir-senha/" + TOKEN in texto
    assert "Modo de demonstração" in texto

def test_modo_de_demonstracao_sem_conta_nao_mostra_link(monkeypatch):
    preparar_pedido_de_link(monkeypatch, False)
    monkeypatch.setattr(senha_controller, "MOSTRAR_LINK_DE_SENHA_NA_TELA", True)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/esqueci-senha", data={"cpf": CPF}))
    assert "/redefinir-senha/" not in texto

def test_erro_no_banco_ao_pedir_o_link(monkeypatch):
    preparar_pedido_de_link(monkeypatch, True)
    monkeypatch.setattr(senha_model, "criar_token_de_recuperacao", erro_de_mentira)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.post("/esqueci-senha", data={"cpf": CPF}))
    assert "Não foi possível enviar o link agora" in texto
    assert "Se esse CPF tem conta" not in texto

def test_erro_no_banco_nao_manda_email(monkeypatch):
    cpfs, emails = preparar_pedido_de_link(monkeypatch, True)
    monkeypatch.setattr(senha_model, "criar_token_de_recuperacao", erro_de_mentira)
    navegador = pegar_navegador()
    navegador.post("/esqueci-senha", data={"cpf": CPF})
    assert emails == []

def test_login_tem_o_link_esqueci_minha_senha():
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.get("/login"))
    assert 'href="/esqueci-senha"' in texto
    assert "Esqueci minha senha" in texto


# REDEFINIR A SENHA (link do e-mail) 
# troca o model pelas funções de mentira da tela de senha nova
# valido: se o token "vale" no banco. devolve a lista de trocas feitas
def preparar_redefinicao(monkeypatch, valido, trocou=True):
    trocas = []
    consultas = []

    def token_e_valido(token):
        consultas.append(token)
        return valido

    def trocar(token, nova_senha):
        trocas.append((token, nova_senha))
        return trocou

    monkeypatch.setattr(senha_model, "token_e_valido", token_e_valido)
    monkeypatch.setattr(senha_model, "trocar_senha_com_token", trocar)
    return trocas, consultas

def test_link_valido_mostra_o_formulario(monkeypatch):
    preparar_redefinicao(monkeypatch, True)
    navegador = pegar_navegador()
    resposta = navegador.get("/redefinir-senha/" + TOKEN)
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert 'name="senha"' in texto
    assert 'name="confirmacao"' in texto
    assert "Trocar a senha" in texto

def test_link_que_nao_vale_mais_mostra_a_mensagem(monkeypatch):
    preparar_redefinicao(monkeypatch, False)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.get("/redefinir-senha/" + TOKEN))
    assert "Esse link não vale mais" in texto
    assert 'name="senha"' not in texto
    assert "Pedir um link novo" in texto

def test_link_com_formato_de_lixo_nem_pergunta_pro_banco(monkeypatch):
    trocas, consultas = preparar_redefinicao(monkeypatch, True)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.get("/redefinir-senha/curto"))
    assert "Esse link não vale mais" in texto
    assert consultas == []

def test_erro_no_banco_ao_abrir_o_link(monkeypatch):
    preparar_redefinicao(monkeypatch, True)
    monkeypatch.setattr(senha_model, "token_e_valido", erro_de_mentira)
    navegador = pegar_navegador()
    texto = pegar_texto(navegador.get("/redefinir-senha/" + TOKEN))
    assert "Não foi possível abrir essa página agora" in texto

def test_cliente_logado_e_mandado_pra_vitrine(monkeypatch):
    preparar_redefinicao(monkeypatch, True)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/redefinir-senha/" + TOKEN)
    assert resposta.status_code == 302

def test_senha_nova_certa_troca_e_manda_pro_login(monkeypatch):
    trocas, consultas = preparar_redefinicao(monkeypatch, True)
    navegador = pegar_navegador()
    dados = {"senha": "Senha@Nova1", "confirmacao": "Senha@Nova1"}
    resposta = navegador.post("/redefinir-senha/" + TOKEN, data=dados)
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    assert trocas == [(TOKEN, "Senha@Nova1")]
    assert "ok: Senha trocada! Entre com a sua senha nova." in pegar_mensagens(navegador)

def test_senha_fraca_nao_troca(monkeypatch):
    trocas, consultas = preparar_redefinicao(monkeypatch, True)
    navegador = pegar_navegador()
    dados = {"senha": "fraca", "confirmacao": "fraca"}
    texto = pegar_texto(navegador.post("/redefinir-senha/" + TOKEN, data=dados))
    assert "A senha precisa ter no mínimo 8 caracteres" in texto
    assert trocas == []

def test_senha_sem_maiuscula_ou_sem_especial_nao_troca(monkeypatch):
    trocas, consultas = preparar_redefinicao(monkeypatch, True)
    navegador = pegar_navegador()
    navegador.post("/redefinir-senha/" + TOKEN, data={"senha": "senha@nova1", "confirmacao": "senha@nova1"})
    navegador.post("/redefinir-senha/" + TOKEN, data={"senha": "SenhaNova12", "confirmacao": "SenhaNova12"})
    assert trocas == []

def test_senha_aceita_com_8_caracteres(monkeypatch):
    trocas, consultas = preparar_redefinicao(monkeypatch, True)
    navegador = pegar_navegador()
    navegador.post("/redefinir-senha/" + TOKEN, data={"senha": "Senha@12", "confirmacao": "Senha@12"})
    assert len(trocas) == 1

def test_confirmacao_diferente_nao_troca(monkeypatch):
    trocas, consultas = preparar_redefinicao(monkeypatch, True)
    navegador = pegar_navegador()
    dados = {"senha": "Senha@Nova1", "confirmacao": "Senha@Nova2"}
    texto = pegar_texto(navegador.post("/redefinir-senha/" + TOKEN, data=dados))
    assert "As senhas não são iguais." in texto
    assert trocas == []

def test_post_em_link_que_nao_vale_nao_troca(monkeypatch):
    trocas, consultas = preparar_redefinicao(monkeypatch, False)
    navegador = pegar_navegador()
    dados = {"senha": "Senha@Nova1", "confirmacao": "Senha@Nova1"}
    texto = pegar_texto(navegador.post("/redefinir-senha/" + TOKEN, data=dados))
    assert "Esse link não vale mais" in texto
    assert trocas == []

def test_link_que_venceu_enquanto_a_pessoa_digitava(monkeypatch):
    # o link valia quando a tela abriu, mas na hora de gravar o banco diz que não vale mais
    trocas, consultas = preparar_redefinicao(monkeypatch, True, trocou=False)
    navegador = pegar_navegador()
    dados = {"senha": "Senha@Nova1", "confirmacao": "Senha@Nova1"}
    texto = pegar_texto(navegador.post("/redefinir-senha/" + TOKEN, data=dados))
    assert "Esse link não vale mais" in texto
    assert len(trocas) == 1

def test_erro_no_banco_ao_trocar_a_senha(monkeypatch):
    preparar_redefinicao(monkeypatch, True)
    monkeypatch.setattr(senha_model, "trocar_senha_com_token", erro_de_mentira)
    navegador = pegar_navegador()
    dados = {"senha": "Senha@Nova1", "confirmacao": "Senha@Nova1"}
    resposta = navegador.post("/redefinir-senha/" + TOKEN, data=dados)
    assert resposta.status_code == 200
    assert "Não foi possível trocar a senha agora" in pegar_texto(resposta)

def test_a_senha_nova_nao_volta_escrita_na_tela(monkeypatch):
    preparar_redefinicao(monkeypatch, True)
    navegador = pegar_navegador()
    dados = {"senha": "fraca", "confirmacao": "fraca"}
    texto = pegar_texto(navegador.post("/redefinir-senha/" + TOKEN, data=dados))
    assert 'value="fraca"' not in texto
