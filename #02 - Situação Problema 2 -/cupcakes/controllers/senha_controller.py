from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from config import MOSTRAR_LINK_DE_SENHA_NA_TELA
from models import validacoes
from models import senha_model
from models import senha_regras
from models import email_simulado

# controller da recuperação de senha (telas 3 e 3b)
# cartão 19: o link chega por e-mail, vale 1 hora e só pode ser usado uma vez


senha_bp = Blueprint("senha", __name__)

# TELA 3 - Esqueci minha senha: a pessoa informa o CPF e recebe o link por e-mail
@senha_bp.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():
    # quem já está logado não precisa disso
    if session.get("tipo") == "cliente":
        return redirect(url_for("vitrine.vitrine"))

    cpf_digitado = ""
    erro = ""
    enviado = False
    link_demonstracao = ""

    if request.method == "POST":
        cpf_digitado = request.form.get("cpf", "").strip()

        if validacoes.validar_cpf(cpf_digitado) == False:
            erro = "CPF inválido"
        else:
            cpf = validacoes.tirar_enfeites(cpf_digitado)
            try:
                resultado = senha_model.criar_token_de_recuperacao(cpf)
                enviado = True

                # só manda o e-mail se existe conta
                # (a tela responde igual existindo ou não, assim ninguém descobre quais CPFs têm conta)
                if resultado is not None:
                    link = url_for("senha.redefinir", token=resultado["token"], _external=True)
                    assunto, texto = senha_regras.montar_email(resultado["nome"], link)
                    email_simulado.enviar(resultado["email"], assunto, texto)

                    # só na demonstração: mostra o link na tela (quem testa o site não vê o terminal)
                    if MOSTRAR_LINK_DE_SENHA_NA_TELA == True:
                        link_demonstracao = link

            except Exception as e:
                print("ERRO AO CRIAR O LINK DE SENHA:", e)
                enviado = False
                erro = "Não foi possível enviar o link agora. Tente de novo em alguns minutos."

    return render_template("esqueci_senha.html", cpf=cpf_digitado, erro=erro, enviado=enviado,
                           link_demonstracao=link_demonstracao,
                           minutos=senha_regras.MINUTOS_DE_VALIDADE)


# TELA 3b - Escolher a senha nova (a pessoa chega aqui pelo link do e-mail)
@senha_bp.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir(token):
    if session.get("tipo") == "cliente":
        return redirect(url_for("vitrine.vitrine"))

    # situação do link: "ok" (pode trocar), "invalido" (usado, vencido ou lixo) ou "erro" (banco fora do ar)
    situacao = "ok"
    if senha_regras.token_parece_valido(token) == False:
        situacao = "invalido"
    else:
        try:
            if senha_model.token_e_valido(token) == False:
                situacao = "invalido"
        except Exception as e:
            print("ERRO AO CONFERIR O LINK DE SENHA:", e)
            situacao = "erro"

    erros = {}

    if situacao == "ok" and request.method == "POST":
        senha = request.form.get("senha", "")
        confirmacao = request.form.get("confirmacao", "")

        if validacoes.validar_senha(senha) == False:
            erros["senha"] = "A senha precisa ter no mínimo 8 caracteres, uma letra maiúscula e um caractere especial."
        elif senha != confirmacao:
            erros["confirmacao"] = "As senhas não são iguais."

        if len(erros) == 0:
            try:
                trocou = senha_model.trocar_senha_com_token(token, senha)
                if trocou == True:
                    flash("Senha trocada! Entre com a sua senha nova.", "ok")
                    return redirect(url_for("auth.login"))
                # o link foi usado ou venceu enquanto a pessoa digitava
                situacao = "invalido"
            except Exception as e:
                print("ERRO AO TROCAR A SENHA:", e)
                erros["geral"] = "Não foi possível trocar a senha agora. Tente de novo em alguns minutos."

    return render_template("redefinir_senha.html", situacao=situacao, erros=erros)