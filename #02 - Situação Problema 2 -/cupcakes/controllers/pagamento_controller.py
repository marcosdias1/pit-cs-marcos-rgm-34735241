from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import pedido_model
from models import pagamento_simulado
from controllers.carrinho_controller import pegar_id_do_carrinho

# controller do pagamento e do pedido confirmado (telas 8 e 9)
# caso de uso do cartão 11 (o pedido só vira "Confirmado" depois que o pagamento é aprovado)


pagamento_bp = Blueprint("pagamento", __name__)


# função que confere se a pessoa pode ver esse pedido
# cliente: só os pedidos da conta dele
# visitante: só o pedido que ele mesmo criou nessa sessão
# (o número do pedido é uma sequência, então sem essa conferência qualquer um veria o pedido dos outros)
def pode_acessar(pedido):
    if pedido is None:
        return False

    # pedido de cliente: só o dono, e logado
    if pedido["id_cliente"] is not None:
        if session.get("tipo") == "cliente":
            return pedido["id_cliente"] == session.get("id_cliente")
        return False

    # pedido de visitante: quem criou nessa sessão, ou quem liberou na busca por número e e-mail
    if session.get("pedido_atual") == pedido["id"]:
        return True
    return pedido["id"] in session.get("pedidos_liberados", [])

# função que busca o pedido e já confere se a pessoa pode ver. Devolve o pedido ou None (se não existe, não é dela, ou deu erro no banco)
def pegar_pedido(numero):
    try:
        pedido = pedido_model.buscar_pedido_por_numero(numero)
    except Exception as e:
        print("ERRO AO BUSCAR O PEDIDO:", e)
        flash("Não foi possível abrir o pedido agora. Tente de novo em alguns minutos.", "erro")
        return None

    if pode_acessar(pedido) == False:
        flash("Pedido não encontrado.", "erro")
        return None

    return pedido


# TELA 8 - Pagamento (cartão 11)
@pagamento_bp.route("/pagamento/<int:numero>", methods=["GET", "POST"])
def pagar(numero):
    # quem não entrou nem escolheu ser visitante vai pro login
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    pedido = pegar_pedido(numero)
    if pedido is None:
        return redirect(url_for("carrinho.ver_carrinho"))

    # pedido cancelado não pode ser pago
    if pedido["status"] == "CANCELADO":
        flash("Esse pedido foi cancelado. Feche o pedido de novo.", "aviso")
        return redirect(url_for("carrinho.ver_carrinho"))

    # pedido que já foi pago vai direto pra tela de confirmado
    if pedido["status"] != "AGUARDANDO_PAGAMENTO":
        return redirect(url_for("pagamento.confirmado", numero=numero))

    erros = {}
    dados = {"nome": "", "validade": ""}
    abrir_cartao = False

    if request.method == "POST":
        forma = request.form.get("forma", "")
        resultado = None

        if forma == "PIX":
            resultado = pagamento_simulado.autorizar_pix()

        elif forma == "CARTAO_CREDITO":
            abrir_cartao = True
            numero_cartao = request.form.get("numero_cartao", "")
            dados["nome"] = request.form.get("nome", "").strip()
            dados["validade"] = request.form.get("validade", "").strip()
            cvv = request.form.get("cvv", "").strip()

            # confere os dados do cartão (o número e o cvv nunca voltam escritos pra tela)
            erros = pagamento_simulado.validar_cartao(numero_cartao, dados["nome"], dados["validade"],
                                                      cvv, date.today())
            if len(erros) == 0:
                resultado = pagamento_simulado.autorizar_cartao(numero_cartao)

        else:
            flash("Escolha como pagar: PIX ou cartão de crédito.", "erro")

        # se chegou na operadora (simulada), trata a resposta
        if resultado is not None:
            try:
                if resultado["aprovado"] == False:
                    # guarda a tentativa recusada e deixa a pessoa tentar de novo (o pedido continua esperando)
                    pedido_model.registrar_pagamento_recusado(pedido["id"], forma, pedido["total"],
                                                              resultado["codigo"])
                    flash("Pagamento recusado. Tente outro cartão ou PIX.", "erro")
                else:
                    # confere o cupom de novo (ele pode ter vencido desde a tela anterior)
                    mensagem = pedido_model.conferir_cupom_do_pedido(pedido, date.today())
                    if mensagem != "":
                        flash(mensagem + " Volte ao carrinho e feche o pedido de novo.", "erro")
                    else:
                        id_carrinho = pegar_id_do_carrinho()
                        mensagem = pedido_model.confirmar_pagamento(pedido["id"], id_carrinho, forma,
                                                                    pedido["total"], resultado["codigo"],
                                                                    session.get("id_cliente"))
                        if mensagem != "":
                            flash(mensagem, "erro")
                        else:
                            # deu tudo certo: o pedido está confirmado
                            session.pop("checkout", None)
                            return redirect(url_for("pagamento.confirmado", numero=numero))
            except Exception as e:
                print("ERRO NO PAGAMENTO:", e)
                flash("Não foi possível concluir o pagamento agora. Nada foi cobrado. Tente de novo em alguns minutos.", "erro")

    return render_template("pagamento.html", pedido=pedido, erros=erros, dados=dados,
                           abrir_cartao=abrir_cartao,
                           cartao_aprovado=pagamento_simulado.formatar_numero(pagamento_simulado.CARTAO_APROVADO),
                           cartao_recusado=pagamento_simulado.formatar_numero(pagamento_simulado.CARTAO_RECUSADO))


# TELA 9 - edido confirmados
@pagamento_bp.route("/pedido/<int:numero>/confirmado")
def confirmado(numero):
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    pedido = pegar_pedido(numero)
    if pedido is None:
        return redirect(url_for("carrinho.ver_carrinho"))

    if pedido["status"] == "CANCELADO":
        flash("Esse pedido foi cancelado.", "aviso")
        return redirect(url_for("carrinho.ver_carrinho"))

    # ainda não pagou: volta pro pagamento
    if pedido["status"] == "AGUARDANDO_PAGAMENTO":
        return redirect(url_for("pagamento.pagar", numero=numero))

    itens = []
    try:
        itens = pedido_model.listar_itens_do_pedido(pedido["id"])
    except Exception as e:
        print("ERRO AO LISTAR OS ITENS DO PEDIDO:", e)

    previsao = pedido_model.formatar_previsao(pedido["previsao_entrega"], datetime.now())
    eh_visitante = (session.get("tipo") != "cliente")

    return render_template("pedido_confirmado.html", pedido=pedido, itens=itens,
                           previsao=previsao, eh_visitante=eh_visitante)