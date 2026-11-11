from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import validacoes
from models import cliente_model
from models import carrinho_model

# casos de uso dos cartões 16, 17 e 18


auth_bp = Blueprint("auth", __name__)

# função que passa o carrinho do visitante pra conta de quem acabou de entrar ou criar conta (o id_sessao_antiga é o código que o visitante tinha na sessão antes de a sessão ser limpa)
def juntar_carrinhos(id_sessao_antiga, id_cliente):
    movidos = 0
    if id_sessao_antiga is not None:
        try:
            movidos = carrinho_model.juntar_carrinho_do_visitante(id_sessao_antiga, id_cliente)
        except Exception as e:
            # se der erro aqui a pessoa entra do mesmo jeito, só o carrinho de visitante fica pra trás
            print("ERRO AO JUNTAR OS CARRINHOS:", e)

    if movidos > 0:
        flash("Os itens do seu carrinho foram mantidos.", "ok")


## TELA 1 - Login (cartão 16)
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # se o cliente já está logado, não precisa ver o login de novo
    if session.get("tipo") == "cliente":
        return redirect(url_for("vitrine.vitrine"))
    erros = {}
    dados = {}

    # só entra aqui quando a pessoa clicou no botão Entrar
    if request.method == "POST":
        dados = request.form
        cpf_digitado = request.form.get("cpf", "")
        senha = request.form.get("senha", "")

        # primeiro confere se o cpf é válido
        if validacoes.validar_cpf(cpf_digitado) == False:
            erros["cpf"] = "CPF inválido"
        else:
            if senha == "":
                erros["senha"] = "Digite sua senha."
            else:
                cpf = validacoes.tirar_enfeites(cpf_digitado)

                cliente = None
                deu_erro_no_banco = False
                try:
                    cliente = cliente_model.conferir_login(cpf, senha)
                except Exception as e:
                    print("ERRO NO LOGIN:", e)
                    deu_erro_no_banco = True

                if deu_erro_no_banco == True:
                    erros["geral"] = "Não foi possível entrar agora. Tente de novo em alguns minutos."
                else:
                    if cliente is None:
                        # não diz qual dos dois está errado, de propósito
                        erros["geral"] = "CPF ou senha incorretos"
                    else:
                        # guarda o código do carrinho de visitante antes de limpar a sessão
                        id_sessao_antiga = session.get("id_sessao")

                        # limpa a sessão antiga e guarda os dados de quem entrou
                        session.clear()
                        session["tipo"] = "cliente"
                        session["id_cliente"] = cliente["id"]
                        session["nome"] = cliente["nome"]
                        flash("Bem-vindo de volta, " + cliente["nome"] + "!", "ok")
                        juntar_carrinhos(id_sessao_antiga, cliente["id"])

                        return redirect(url_for("vitrine.vitrine"))

    return render_template("login.html", erros=erros, dados=dados)


## TELA 2 - Criar conta (cartão 17)
@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    erros = {}
    dados = {}

    if request.method == "POST":
        dados = request.form

        # pega tudo que a pessoa digitou (o strip tira espaços do começo e do fim)
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        celular = request.form.get("celular", "").strip()
        cpf_digitado = request.form.get("cpf", "").strip()
        senha = request.form.get("senha", "")
        cep = request.form.get("cep", "").strip()
        rua = request.form.get("rua", "").strip()
        numero = request.form.get("numero", "").strip()
        bairro = request.form.get("bairro", "").strip()
        cidade = request.form.get("cidade", "").strip()
        uf = request.form.get("uf", "").strip().upper()

        # confere tudo de uma vez
        erros = validacoes.conferir_cadastro(nome, email, celular, cpf_digitado, senha,
                                             cep, rua, numero, bairro, cidade, uf)

        # se não teve nenhum erro, tenta criar a conta
        if len(erros) == 0:
            cpf = validacoes.tirar_enfeites(cpf_digitado)
            celular = validacoes.tirar_enfeites(celular)
            cep = validacoes.tirar_enfeites(cep)

            try:
                cliente_existente = cliente_model.buscar_cliente_por_cpf(cpf)

                if cliente_existente is not None:
                    # regra do cartão 17: cpf que já existe vai pro login
                    flash("Esse CPF já tem conta. Entre com o seu CPF e a sua senha.", "aviso")
                    return redirect(url_for("auth.login"))
                else:
                    if cliente_model.email_ja_existe(email) == True:
                        erros["email"] = "Esse e-mail já está cadastrado."
                    else:
                        id_novo = cliente_model.criar_cliente(nome, email, celular, cpf, senha,
                                                              cep, rua, numero, bairro, cidade, uf)

                        # guarda o código do carrinho de visitante antes de limpar a sessão
                        id_sessao_antiga = session.get("id_sessao")

                        # já deixa a pessoa logada
                        session.clear()
                        session["tipo"] = "cliente"
                        session["id_cliente"] = id_novo
                        session["nome"] = nome
                        # avisa a vitrine pra mostrar o pop-up do cupom
                        session["mostrar_cupom"] = True
                        juntar_carrinhos(id_sessao_antiga, id_novo)
                        
                        return redirect(url_for("vitrine.vitrine"))

            except Exception as e:
                print("ERRO AO CRIAR CONTA:", e)
                erros["geral"] = "Não foi possível criar a conta agora. Tente de novo em alguns minutos."

    return render_template("cadastro.html", erros=erros, dados=dados)

## Modo visitante (cartão 18)
@auth_bp.route("/visitante")
def visitante():
    session.clear()
    session["tipo"] = "visitante"
    return redirect(url_for("vitrine.vitrine"))


# Sair da conta
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Você saiu da conta.", "ok")
    return redirect(url_for("auth.login"))