import secrets
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import carrinho_model
from models import validacoes

carrinho_bp = Blueprint("carrinho", __name__)


# função que transforma o texto do formulário em número (ou None se não for número)
# ex: "3" vira 3, "abc" vira None, "-1" vira None
def ler_numero(texto):
    if validacoes.so_tem_numeros(texto) == False:
        return None
    # número muito grande o banco não aceita
    if len(texto) > 9:
        return None
    return int(texto)


# função que descobre qual é o carrinho de quem está usando o site
# cliente logado: o carrinho fica ligado ao id do cliente
# visitante: o carrinho fica ligado a um código que eu guardo na sessão dele
def pegar_id_do_carrinho():
    if session.get("tipo") == "cliente":
        return carrinho_model.pegar_ou_criar_carrinho(session.get("id_cliente"), None)

    # visitante: se ainda não tem código, cria um
    if "id_sessao" not in session:
        session["id_sessao"] = secrets.token_hex(16)
        # sessão "permanente" não some quando fecha o navegador (cartão 05: não perder o carrinho)
        session.permanent = True
    return carrinho_model.pegar_ou_criar_carrinho(None, session["id_sessao"])


# TELA 6 - Carrinho de compras 
@carrinho_bp.route("/carrinho")
def ver_carrinho():
    # quem não entrou nem escolheu ser visitante vai pro login
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    itens = []
    adicionais = []
    erro = ""

    try:
        id_carrinho = pegar_id_do_carrinho()
        itens = carrinho_model.listar_itens(id_carrinho)
        adicionais = carrinho_model.listar_adicionais(id_carrinho)
    except Exception as e:
        print("ERRO AO ABRIR O CARRINHO:", e)
        erro = "Não foi possível abrir o carrinho agora. Tente de novo em alguns minutos."

    # só sugere adicional se tem pelo menos um cupcake no carrinho
    tem_cupcake = False
    for item in itens:
        if item["tipo"] == "CUPCAKE":
            tem_cupcake = True
    if tem_cupcake == False:
        adicionais = []

    subtotal = carrinho_model.calcular_subtotal(itens)
    subtotal_texto = carrinho_model.formatar_dinheiro(subtotal)

    return render_template("carrinho.html", itens=itens, adicionais=adicionais,
                           subtotal=subtotal_texto, erro=erro)


# Colocar no carrinho (cartões 05 e 06)
@carrinho_bp.route("/carrinho/adicionar", methods=["POST"])
def adicionar():
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    id_produto = ler_numero(request.form.get("id_produto", ""))
    quantidade = ler_numero(request.form.get("quantidade", "1"))

    # pra onde ir depois de adicionar (só aceito essas duas opções, qualquer outra vira "vitrine")
    voltar_para = request.form.get("voltar_para", "vitrine")
    if voltar_para != "carrinho":
        voltar_para = "vitrine"

    # onde mostrar o erro: na tela onde a pessoa estava
    # (de onde vem "vitrine" é a tela de detalhes, e de onde vem "carrinho" é o carrinho)
    if voltar_para == "carrinho":
        tela_do_erro = url_for("carrinho.ver_carrinho")
    elif id_produto is not None:
        tela_do_erro = url_for("vitrine.detalhe", id_cupcake=id_produto)
    else:
        tela_do_erro = url_for("vitrine.vitrine")

    if id_produto is None or id_produto == 0:
        flash("Produto inválido.", "erro")
        return redirect(tela_do_erro)

    if quantidade is None or quantidade < 1 or quantidade > 99:
        flash("Escolha uma quantidade entre 1 e 99.", "erro")
        return redirect(tela_do_erro)

    mensagem = ""
    try:
        id_carrinho = pegar_id_do_carrinho()
        mensagem = carrinho_model.adicionar_item(id_carrinho, id_produto, quantidade)
    except Exception as e:
        print("ERRO AO ADICIONAR NO CARRINHO:", e)
        mensagem = "Não foi possível adicionar agora. Tente de novo em alguns minutos."

    if mensagem != "":
        flash(mensagem, "erro")
        return redirect(tela_do_erro)

    flash("Adicionado ao carrinho!", "ok")
    if voltar_para == "carrinho":
        return redirect(url_for("carrinho.ver_carrinho"))
    return redirect(url_for("vitrine.vitrine"))


# Selecionar quantidade (cartão 07)
@carrinho_bp.route("/carrinho/alterar", methods=["POST"])
def alterar():
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    id_produto = ler_numero(request.form.get("id_produto", ""))
    acao = request.form.get("acao", "")

    mudanca = 0
    if acao == "mais":
        mudanca = 1
    if acao == "menos":
        mudanca = -1

    if id_produto is None or mudanca == 0:
        flash("Não entendi o que você quis fazer. Tente de novo.", "erro")
        return redirect(url_for("carrinho.ver_carrinho"))

    mensagem = ""
    try:
        id_carrinho = pegar_id_do_carrinho()
        mensagem = carrinho_model.alterar_quantidade(id_carrinho, id_produto, mudanca)
    except Exception as e:
        print("ERRO AO ALTERAR A QUANTIDADE:", e)
        mensagem = "Não foi possível alterar agora. Tente de novo em alguns minutos."

    if mensagem != "":
        flash(mensagem, "erro")
    return redirect(url_for("carrinho.ver_carrinho"))



# Tirar um item do carrinho (a lixeira, cartão 07)
@carrinho_bp.route("/carrinho/remover", methods=["POST"])
def remover():
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    id_produto = ler_numero(request.form.get("id_produto", ""))

    if id_produto is None:
        flash("Não entendi o que você quis fazer. Tente de novo.", "erro")
        return redirect(url_for("carrinho.ver_carrinho"))

    try:
        id_carrinho = pegar_id_do_carrinho()
        carrinho_model.remover_item(id_carrinho, id_produto)
    except Exception as e:
        print("ERRO AO REMOVER DO CARRINHO:", e)
        flash("Não foi possível remover agora. Tente de novo em alguns minutos.", "erro")

    return redirect(url_for("carrinho.ver_carrinho"))