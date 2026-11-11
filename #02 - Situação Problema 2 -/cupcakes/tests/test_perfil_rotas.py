# testes das rotas do Meu perfil: dados da conta e endereços (cartão 20)

from app import app
from models import carrinho_model
from models import perfil_model


# cria um "navegador de mentira" pra fazer os testes
def pegar_navegador():
    app.config["TESTING"] = True
    navegador = app.test_client()
    return navegador

def entrar_como_visitante():
    navegador = pegar_navegador()
    navegador.get("/visitante")
    return navegador


# cliente logado de mentira (id 7)
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


# dados de mentira 

def cliente_de_mentira():
    return {"nome": "Ana Teste", "email": "ana@gmail.com", "celular": "11900001111", "cpf": "12345678909"}


def endereco_de_mentira(id_endereco, principal, apelido="Casa"):
    endereco = {}
    endereco["id"] = id_endereco
    endereco["apelido"] = apelido
    endereco["cep"] = "01001000"
    endereco["rua"] = "Praça da Sé"
    endereco["numero"] = "10"
    endereco["complemento"] = None
    endereco["bairro"] = "Sé"
    endereco["cidade"] = "São Paulo"
    endereco["uf"] = "SP"
    endereco["principal"] = principal
    endereco["nome"] = apelido or "Endereço"
    endereco["resumo"] = "Praça da Sé, 10 - Sé, São Paulo/SP - CEP 01001-000"
    return endereco


# o formulário de endereço certo
def formulario_de_endereco():
    return {"apelido": "Trabalho", "cep": "01001-000", "rua": "Praça da Sé", "numero": "10",
            "complemento": "", "bairro": "Sé", "cidade": "São Paulo", "uf": "SP"}


# troca as funções do banco pelas de mentira
# enderecos: a lista que o cliente "tem". devolve um dicionário com as chamadas que o controller fez
def preparar(monkeypatch, enderecos, cliente="padrao", email_em_uso=False):
    chamadas = {"atualizar": [], "criar": [], "substituir": [], "principal": [], "excluir": [], "contar": []}

    if cliente == "padrao":
        cliente = cliente_de_mentira()

    def buscar_dados(id_cliente):
        return cliente

    def listar(id_cliente):
        return enderecos

    def em_uso(email, id_cliente):
        return email_em_uso

    def atualizar(id_cliente, nome, email, celular):
        chamadas["atualizar"].append((id_cliente, nome, email, celular))

    def contar(id_cliente):
        chamadas["contar"].append(id_cliente)
        return len(enderecos)

    def buscar_endereco(id_cliente, id_endereco):
        for endereco in enderecos:
            if endereco["id"] == id_endereco:
                return endereco
        return None

    def criar(id_cliente, campos):
        chamadas["criar"].append((id_cliente, campos))

    def substituir(id_cliente, id_endereco, campos):
        chamadas["substituir"].append((id_cliente, id_endereco, campos))
        return buscar_endereco(id_cliente, id_endereco) is not None

    def definir_principal(id_cliente, id_endereco):
        chamadas["principal"].append((id_cliente, id_endereco))
        return buscar_endereco(id_cliente, id_endereco) is not None

    def excluir(id_cliente, id_endereco):
        chamadas["excluir"].append((id_cliente, id_endereco))
        return True

    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    monkeypatch.setattr(perfil_model, "buscar_dados_do_cliente", buscar_dados)
    monkeypatch.setattr(perfil_model, "listar_enderecos", listar)
    monkeypatch.setattr(perfil_model, "email_em_uso_por_outro", em_uso)
    monkeypatch.setattr(perfil_model, "atualizar_dados", atualizar)
    monkeypatch.setattr(perfil_model, "contar_enderecos", contar)
    monkeypatch.setattr(perfil_model, "buscar_endereco", buscar_endereco)
    monkeypatch.setattr(perfil_model, "criar_endereco", criar)
    monkeypatch.setattr(perfil_model, "substituir_endereco", substituir)
    monkeypatch.setattr(perfil_model, "definir_principal", definir_principal)
    monkeypatch.setattr(perfil_model, "excluir_endereco", excluir)
    return chamadas


DOIS_ENDERECOS = [endereco_de_mentira(1, True, "Casa"), endereco_de_mentira(2, False, "Trabalho")]


# quem pode entrar 

def test_perfil_sem_entrar_manda_pro_login():
    navegador = pegar_navegador()
    resposta = navegador.get("/perfil")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]

def test_visitante_nao_tem_perfil(monkeypatch):
    preparar(monkeypatch, [])
    navegador = entrar_como_visitante()
    resposta = navegador.get("/perfil", follow_redirects=True)
    assert "Entre na sua conta para ver o seu perfil." in pegar_texto(resposta)

def test_visitante_nao_mexe_em_endereco(monkeypatch):
    chamadas = preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_visitante()
    navegador.post("/perfil/endereco/1/excluir")
    navegador.post("/perfil/endereco/1/principal")
    navegador.post("/perfil/endereco/novo", data=formulario_de_endereco())
    assert chamadas["excluir"] == []
    assert chamadas["principal"] == []
    assert chamadas["criar"] == []


# tela do perfil 

def test_perfil_mostra_os_dados_da_conta(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert 'value="Ana Teste"' in texto
    assert 'value="ana@gmail.com"' in texto
    assert 'value="(11) 90000-1111"' in texto

def test_cpf_aparece_escondido_e_nao_pode_ser_editado(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/perfil"))
    assert "***.456.789-**" in texto
    assert "12345678909" not in texto
    assert 'name="cpf"' not in texto

def test_perfil_lista_os_enderecos(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/perfil"))
    assert "Casa" in texto
    assert "Trabalho" in texto
    assert "Praça da Sé, 10" in texto
    assert texto.count("Principal</span>") == 1

def test_so_o_endereco_que_nao_e_principal_tem_o_botao_tornar_principal(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/perfil"))
    assert texto.count("Tornar principal") == 1
    assert 'action="/perfil/endereco/2/principal"' in texto
    assert 'action="/perfil/endereco/1/principal"' not in texto

def test_cada_endereco_tem_editar_e_excluir(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/perfil"))
    assert 'href="/perfil/endereco/1/editar"' in texto
    assert 'href="/perfil/endereco/2/editar"' in texto
    assert 'action="/perfil/endereco/1/excluir"' in texto
    assert 'action="/perfil/endereco/2/excluir"' in texto

def test_excluir_e_tornar_principal_sao_formularios_post(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/perfil"))
    assert texto.count('method="POST"') >= 3

def test_sem_enderecos_mostra_mensagem(monkeypatch):
    preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/perfil"))
    assert "Você não tem nenhum endereço guardado" in texto
    assert "Adicionar endereço" in texto

def test_com_5_enderecos_some_o_botao_de_adicionar(monkeypatch):
    cinco = []
    for i in range(5):
        cinco.append(endereco_de_mentira(i + 1, i == 0))
    preparar(monkeypatch, cinco)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/perfil"))
    assert "Adicionar endereço" not in texto
    assert "Você já tem 5 endereços" in texto

def test_perfil_avisa_que_pagamento_salvo_nao_existe(monkeypatch):
    preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/perfil"))
    assert "Formas de pagamento salvas ainda não estão disponíveis" in texto

def test_erro_no_banco_ao_abrir_o_perfil(monkeypatch):
    preparar(monkeypatch, [])
    monkeypatch.setattr(perfil_model, "listar_enderecos", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil")
    assert resposta.status_code == 200
    assert "Não foi possível abrir o seu perfil agora" in pegar_texto(resposta)

def test_conta_que_nao_existe_mais_sai_da_sessao(monkeypatch):
    preparar(monkeypatch, [], cliente=None)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil")
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]
    with navegador.session_transaction() as sessao:
        assert "tipo" not in sessao

def test_perfil_pergunta_so_dos_dados_do_cliente_logado(monkeypatch):
    chamadas = preparar(monkeypatch, [])
    perguntas = []
    def buscar_dados(id_cliente):
        perguntas.append(id_cliente)
        return cliente_de_mentira()

    monkeypatch.setattr(perfil_model, "buscar_dados_do_cliente", buscar_dados)
    navegador = entrar_como_cliente()
    navegador.get("/perfil")
    assert perguntas == [7]


# trocar os dados da conta 

def test_trocar_os_dados_com_tudo_certo(monkeypatch):
    chamadas = preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    dados = {"nome": "Ana Maria", "email": "ANA.NOVA@gmail.com ", "celular": "(21) 98888-7777"}
    resposta = navegador.post("/perfil", data=dados)
    assert resposta.status_code == 302
    # e-mail em minúsculas e celular só com números
    assert chamadas["atualizar"] == [(7, "Ana Maria", "ana.nova@gmail.com", "21988887777")]
    assert "ok: Seus dados foram atualizados." in pegar_mensagens(navegador)
    with navegador.session_transaction() as sessao:
        assert sessao["nome"] == "Ana Maria"

def test_dados_errados_mostram_os_erros_e_nao_gravam(monkeypatch):
    chamadas = preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    dados = {"nome": "", "email": "semarroba", "celular": "123"}
    texto = pegar_texto(navegador.post("/perfil", data=dados))
    assert "Informe seu nome." in texto
    assert "E-mail inválido" in texto
    assert "Celular inválido" in texto
    assert chamadas["atualizar"] == []

def test_dados_errados_nao_perdem_o_que_foi_digitado(monkeypatch):
    preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    dados = {"nome": "Ana Maria", "email": "semarroba", "celular": "(21) 98888-7777"}
    texto = pegar_texto(navegador.post("/perfil", data=dados))
    assert 'value="Ana Maria"' in texto
    assert 'value="semarroba"' in texto

def test_email_de_outra_pessoa_nao_pode(monkeypatch):
    chamadas = preparar(monkeypatch, [], email_em_uso=True)
    navegador = entrar_como_cliente()
    dados = {"nome": "Ana", "email": "outra@gmail.com", "celular": "11900001111"}
    texto = pegar_texto(navegador.post("/perfil", data=dados))
    assert "Esse e-mail já está cadastrado." in texto
    assert chamadas["atualizar"] == []

def test_erro_no_banco_ao_salvar_os_dados(monkeypatch):
    preparar(monkeypatch, [])
    monkeypatch.setattr(perfil_model, "atualizar_dados", erro_de_mentira)
    navegador = entrar_como_cliente()
    dados = {"nome": "Ana", "email": "ana@gmail.com", "celular": "11900001111"}
    resposta = navegador.post("/perfil", data=dados)
    assert resposta.status_code == 200
    assert "Não foi possível salvar agora" in pegar_texto(resposta)

def test_cpf_enviado_no_formulario_e_ignorado(monkeypatch):
    # quem tentar mandar um cpf novo pelo formulário não consegue trocar (a função nem recebe cpf)
    chamadas = preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    dados = {"nome": "Ana", "email": "ana@gmail.com", "celular": "11900001111", "cpf": "00000000000"}
    navegador.post("/perfil", data=dados)
    assert len(chamadas["atualizar"][0]) == 4
    assert "00000000000" not in chamadas["atualizar"][0]


# endereço novo 

def test_tela_de_endereco_novo_abre_vazia(monkeypatch):
    preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil/endereco/novo")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Novo endereço" in texto
    assert 'name="cep"' in texto
    assert 'name="complemento"' in texto
    # o javascript do cep está na tela
    assert "cep.js" in texto

def test_endereco_novo_certo_e_guardado(monkeypatch):
    chamadas = preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/novo", data=formulario_de_endereco())
    assert resposta.status_code == 302
    assert "/perfil" in resposta.headers["Location"]
    id_cliente, campos = chamadas["criar"][0]
    assert id_cliente == 7
    # o cep vai só com números
    assert campos["cep"] == "01001000"
    assert campos["apelido"] == "Trabalho"
    # complemento vazio vira "nada" no banco
    assert campos["complemento"] is None
    assert "ok: Endereço guardado." in pegar_mensagens(navegador)

def test_apelido_vazio_vira_nada_no_banco(monkeypatch):
    chamadas = preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    dados = formulario_de_endereco()
    dados["apelido"] = ""
    dados["complemento"] = "Apto 12"
    navegador.post("/perfil/endereco/novo", data=dados)
    campos = chamadas["criar"][0][1]
    assert campos["apelido"] is None
    assert campos["complemento"] == "Apto 12"

def test_uf_minuscula_e_aceita(monkeypatch):
    chamadas = preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    dados = formulario_de_endereco()
    dados["uf"] = "sp"
    navegador.post("/perfil/endereco/novo", data=dados)
    assert chamadas["criar"][0][1]["uf"] == "SP"

def test_endereco_novo_errado_mostra_erros_e_nao_grava(monkeypatch):
    chamadas = preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    dados = formulario_de_endereco()
    dados["cep"] = "123"
    dados["rua"] = ""
    texto = pegar_texto(navegador.post("/perfil/endereco/novo", data=dados))
    assert "CEP inválido" in texto
    assert "Informe a rua." in texto
    assert chamadas["criar"] == []
    # e o que estava certo continua nos campos
    assert 'value="Trabalho"' in texto

def test_nao_deixa_passar_do_limite_de_enderecos(monkeypatch):
    cinco = []
    for i in range(5):
        cinco.append(endereco_de_mentira(i + 1, i == 0))
    chamadas = preparar(monkeypatch, cinco)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/novo", data=formulario_de_endereco())
    assert resposta.status_code == 302
    assert chamadas["criar"] == []
    assert "Você já tem 5 endereços" in pegar_mensagens(navegador)[0]

def test_tela_de_endereco_novo_tambem_respeita_o_limite(monkeypatch):
    cinco = []
    for i in range(5):
        cinco.append(endereco_de_mentira(i + 1, i == 0))
    preparar(monkeypatch, cinco)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil/endereco/novo")
    assert resposta.status_code == 302

def test_erro_no_banco_ao_guardar_o_endereco(monkeypatch):
    preparar(monkeypatch, [])
    monkeypatch.setattr(perfil_model, "criar_endereco", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/novo", data=formulario_de_endereco())
    assert resposta.status_code == 200
    assert "Não foi possível guardar o endereço agora" in pegar_texto(resposta)

def test_erro_ao_contar_os_enderecos(monkeypatch):
    preparar(monkeypatch, [])
    monkeypatch.setattr(perfil_model, "contar_enderecos", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil/endereco/novo")
    assert resposta.status_code == 302


# editar endereço 

def test_tela_de_editar_vem_preenchida(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil/endereco/1/editar")
    texto = pegar_texto(resposta)
    assert resposta.status_code == 200
    assert "Editar endereço" in texto
    assert 'value="Casa"' in texto
    assert 'value="01001-000"' in texto
    assert 'value="Praça da Sé"' in texto
    assert 'action="/perfil/endereco/1/editar"' in texto

def test_editar_endereco_que_nao_existe(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil/endereco/99/editar")
    assert resposta.status_code == 302
    assert "erro: Endereço não encontrado." in pegar_mensagens(navegador)

def test_nao_edita_endereco_de_outra_pessoa(monkeypatch):
    # o buscar_endereco de mentira só acha os endereços da lista, como o de verdade só acha os do cliente
    chamadas = preparar(monkeypatch, [])
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/1/editar", data=formulario_de_endereco())
    assert resposta.status_code == 302
    assert chamadas["substituir"] == []

def test_editar_certo_troca_o_endereco(monkeypatch):
    chamadas = preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/2/editar", data=formulario_de_endereco())
    assert resposta.status_code == 302
    id_cliente, id_endereco, campos = chamadas["substituir"][0]
    assert id_cliente == 7
    assert id_endereco == 2
    assert campos["cep"] == "01001000"
    assert "ok: Endereço atualizado." in pegar_mensagens(navegador)

def test_editar_errado_mostra_erros_e_nao_grava(monkeypatch):
    chamadas = preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    dados = formulario_de_endereco()
    dados["numero"] = ""
    texto = pegar_texto(navegador.post("/perfil/endereco/1/editar", data=dados))
    assert "Informe o número." in texto
    assert chamadas["substituir"] == []

def test_editar_quando_o_endereco_some_no_meio(monkeypatch):
    # existia quando a tela abriu, mas na hora de gravar o banco diz que não existe mais
    chamadas = preparar(monkeypatch, DOIS_ENDERECOS)
    monkeypatch.setattr(perfil_model, "substituir_endereco", lambda a, b, c: False)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/1/editar", data=formulario_de_endereco())
    assert resposta.status_code == 302
    assert "erro: Endereço não encontrado." in pegar_mensagens(navegador)

def test_erro_no_banco_ao_editar(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    monkeypatch.setattr(perfil_model, "substituir_endereco", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/1/editar", data=formulario_de_endereco())
    assert resposta.status_code == 200
    assert "Não foi possível guardar o endereço agora" in pegar_texto(resposta)

def test_erro_no_banco_ao_abrir_a_edicao(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    monkeypatch.setattr(perfil_model, "buscar_endereco", erro_de_mentira)
    navegador = entrar_como_cliente()
    resposta = navegador.get("/perfil/endereco/1/editar")
    assert resposta.status_code == 302


# endereço principal 

def test_tornar_principal(monkeypatch):
    chamadas = preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/2/principal")
    assert resposta.status_code == 302
    assert chamadas["principal"] == [(7, 2)]
    assert "ok: Pronto!" in pegar_mensagens(navegador)[0]

def test_tornar_principal_endereco_que_nao_existe(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    navegador.post("/perfil/endereco/99/principal")
    assert "erro: Endereço não encontrado." in pegar_mensagens(navegador)

def test_erro_no_banco_ao_tornar_principal(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    monkeypatch.setattr(perfil_model, "definir_principal", erro_de_mentira)
    navegador = entrar_como_cliente()
    navegador.post("/perfil/endereco/2/principal")
    assert "Não foi possível alterar agora" in pegar_mensagens(navegador)[0]

def test_tornar_principal_por_get_nao_existe():
    navegador = entrar_como_cliente()
    assert navegador.get("/perfil/endereco/2/principal").status_code == 405


# excluir endereço 

def test_excluir_endereco_comum(monkeypatch):
    chamadas = preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    resposta = navegador.post("/perfil/endereco/2/excluir")
    assert resposta.status_code == 302
    assert chamadas["excluir"] == [(7, 2)]
    assert "ok: Endereço excluído." in pegar_mensagens(navegador)

def test_endereco_principal_nao_e_excluido_se_tem_outros(monkeypatch):
    chamadas = preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    navegador.post("/perfil/endereco/1/excluir")
    assert chamadas["excluir"] == []
    assert "O endereço principal não pode ser excluído" in pegar_mensagens(navegador)[0]

def test_unico_endereco_principal_pode_ser_excluido(monkeypatch):
    chamadas = preparar(monkeypatch, [endereco_de_mentira(1, True)])
    navegador = entrar_como_cliente()
    navegador.post("/perfil/endereco/1/excluir")
    assert chamadas["excluir"] == [(7, 1)]

def test_excluir_endereco_que_nao_existe(monkeypatch):
    chamadas = preparar(monkeypatch, DOIS_ENDERECOS)
    navegador = entrar_como_cliente()
    navegador.post("/perfil/endereco/99/excluir")
    assert chamadas["excluir"] == []
    assert "erro: Endereço não encontrado." in pegar_mensagens(navegador)

def test_erro_no_banco_ao_excluir(monkeypatch):
    preparar(monkeypatch, DOIS_ENDERECOS)
    monkeypatch.setattr(perfil_model, "excluir_endereco", erro_de_mentira)
    navegador = entrar_como_cliente()
    navegador.post("/perfil/endereco/2/excluir")
    assert "Não foi possível excluir agora" in pegar_mensagens(navegador)[0]

def test_excluir_por_get_nao_existe():
    navegador = entrar_como_cliente()
    assert navegador.get("/perfil/endereco/2/excluir").status_code == 405


# link "Meu perfil" no cabeçalho 

def test_cabecalho_do_cliente_tem_o_link_meu_perfil(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_cliente()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert 'href="/perfil"' in texto
    assert "Meu perfil" in texto

def test_cabecalho_do_visitante_nao_tem_o_link_meu_perfil(monkeypatch):
    monkeypatch.setattr(carrinho_model, "contar_itens", contador_zero)
    navegador = entrar_como_visitante()
    texto = pegar_texto(navegador.get("/acompanhar"))
    assert 'href="/perfil"' not in texto
