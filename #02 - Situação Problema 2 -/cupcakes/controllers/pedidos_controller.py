
from flask import Blueprint, render_template, redirect, url_for, session, flash
from models import carrinho_model
from models import historico_model
from models import historico_regras
from models import pedido_model
from controllers.carrinho_controller import pegar_id_do_carrinho
from controllers.pagamento_controller import pegar_pedido

# controller do histórico de compras (tela 11 "Meus pedidos") e da recompra
# cartão 15 (histórico de compras e recompra)


pedidos_bp = Blueprint("pedidos", __name__)


# TELA 11 - Meus pedidos (cartão 15)
@pedidos_bp.route("/meus-pedidos")
def meus_pedidos():
    # quem não entrou nem escolheu ser visitante vai pro login
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    # o histórico é só de quem tem conta
    if session.get("tipo") != "cliente":
        flash("Entre na sua conta para ver o histórico de compras. "
              "Quem comprou como visitante acompanha o pedido pelo número e pelo e-mail.", "aviso")
        return redirect(url_for("auth.login"))

    id_cliente = session.get("id_cliente")
    pedidos = []
    erro = ""

    try:
        pedidos = historico_model.listar_pedidos_do_cliente(id_cliente, historico_regras.LIMITE_DE_PEDIDOS)

        # como o status é uma simulação (muda com o tempo), faz os pedidos andarem antes de mostrar a lista
        mudou_algum = False
        for pedido in pedidos:
            if historico_regras.esta_em_andamento(pedido["status"]):
                try:
                    pedido_model.atualizar_status_simulado(pedido["id"])
                    mudou_algum = True
                except Exception as e:
                    print("ERRO AO ATUALIZAR O STATUS DO PEDIDO", pedido["numero"], ":", e)

        # busca a lista de novo, já com os status atualizados
        if mudou_algum == True:
            pedidos = historico_model.listar_pedidos_do_cliente(id_cliente, historico_regras.LIMITE_DE_PEDIDOS)

    except Exception as e:
        print("ERRO AO LISTAR OS PEDIDOS:", e)
        erro = "Não foi possível abrir o histórico agora. Tente de novo em alguns minutos."

    return render_template("meus_pedidos.html", pedidos=pedidos, erro=erro,
                           limite=historico_regras.LIMITE_DE_PEDIDOS)


# Comprar de novo: coloca no carrinho os itens de um pedido antigo (cartão 15)
@pedidos_bp.route("/pedido/<int:numero>/comprar-de-novo", methods=["POST"])
def comprar_de_novo(numero):
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    if session.get("tipo") != "cliente":
        flash("Entre na sua conta para comprar de novo.", "aviso")
        return redirect(url_for("auth.login"))

    # confere se o pedido existe e se é dessa pessoa
    pedido = pegar_pedido(numero)
    if pedido is None:
        return redirect(url_for("pedidos.meus_pedidos"))

    if pedido["status"] == "AGUARDANDO_PAGAMENTO":
        flash("Esse pedido ainda não foi pago.", "aviso")
        return redirect(url_for("pagamento.pagar", numero=numero))

    itens = []
    id_carrinho = None
    try:
        itens = historico_model.listar_itens_para_recompra(pedido["id"])
        id_carrinho = pegar_id_do_carrinho()
    except Exception as e:
        print("ERRO AO PREPARAR A RECOMPRA:", e)
        flash("Não foi possível comprar de novo agora. Tente de novo em alguns minutos.", "erro")
        return redirect(url_for("pedidos.meus_pedidos"))

    # tenta colocar cada item no carrinho (a mesma função do botão "Adicionar" confere o estoque)
    quantos = 0
    problemas = []
    for item in itens:
        try:
            mensagem = carrinho_model.adicionar_item(id_carrinho, item["id_produto"], item["quantidade"])
        except Exception as e:
            print("ERRO AO COLOCAR NO CARRINHO NA RECOMPRA:", e)
            mensagem = "Não foi possível adicionar agora."

        if mensagem == "":
            quantos = quantos + 1
        else:
            problemas.append({"nome": item["nome"], "motivo": mensagem})

    mensagem_ok, mensagem_aviso = historico_regras.montar_mensagens_da_recompra(quantos, problemas)
    if mensagem_ok != "":
        flash(mensagem_ok, "ok")
    if mensagem_aviso != "":
        flash(mensagem_aviso, "aviso")

    # se nada foi pro carrinho, não adianta ir pra lá
    if quantos == 0:
        return redirect(url_for("pedidos.meus_pedidos"))
    return redirect(url_for("carrinho.ver_carrinho"))