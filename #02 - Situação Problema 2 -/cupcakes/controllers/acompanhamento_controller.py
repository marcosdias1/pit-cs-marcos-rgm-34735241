from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import pedido_model
from models import acompanhamento
from models import validacoes
from controllers.pagamento_controller import pode_acessar, pegar_pedido

# controller do acompanhamento do pedido (tela 10) e da busca por número e e-mail
# cartão 12 (acompanhar o pedido) e cartão 18 (o visitante acompanha pelo número e pelo e-mail)


acompanhamento_bp = Blueprint("acompanhamento", __name__)


# função que monta o dicionário que a tela (e o json) usa
def montar_dados(numero, status, minutos_previstos, entregue_em):
    # o texto de quando entregou (ex: "hoje às 19:40"), só se já entregou
    quando_entregou = pedido_model.formatar_previsao(entregue_em, datetime.now())

    dados = {}
    dados["numero"] = numero
    dados["status"] = status
    dados["status_texto"] = acompanhamento.TEXTOS.get(status, status)
    dados["descricao"] = acompanhamento.DESCRICOES.get(status, "")
    dados["etapas"] = acompanhamento.montar_etapas(status)
    dados["previsao"] = acompanhamento.frase_da_previsao(status, minutos_previstos, quando_entregou)
    dados["entregue"] = (status == "ENTREGUE")
    return dados

# função que faz o pedido andar (simulação) e monta os dados da tela com o status novo. Se o banco falhar, dá erro (quem chamou trata)
def montar_acompanhamento(pedido):
    pedido_model.atualizar_status_simulado(pedido["id"])

    # busca o pedido de novo, já com o status atualizado
    atual = pedido_model.buscar_pedido_por_numero(pedido["numero"])
    historico = pedido_model.listar_historico_do_pedido(atual["id"])

    # descobre quando foi confirmado e quando foi entregue
    confirmado_em = None
    entregue_em = None
    for registro in historico:
        if registro["status"] == "CONFIRMADO" and confirmado_em is None:
            confirmado_em = registro["data_hora"]
        if registro["status"] == "ENTREGUE":
            entregue_em = registro["data_hora"]

    # o tempo previsto é a diferença entre a previsão de entrega e a hora da confirmação
    minutos_previstos = 0
    if confirmado_em is not None and atual["previsao_entrega"] is not None:
        diferenca = atual["previsao_entrega"] - confirmado_em
        minutos_previstos = int(diferenca.total_seconds() / 60)

    return montar_dados(atual["numero"], atual["status"], minutos_previstos, entregue_em)


# TELA 10 - Acompanhar Pedido (cartão 12)
@acompanhamento_bp.route("/pedido/<int:numero>")
def acompanhar(numero):
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    pedido = pegar_pedido(numero)
    if pedido is None:
        return redirect(url_for("carrinho.ver_carrinho"))

    # ainda não pagou: volta pro pagamento
    if pedido["status"] == "AGUARDANDO_PAGAMENTO":
        return redirect(url_for("pagamento.pagar", numero=numero))

    if pedido["status"] == "CANCELADO":
        flash("Esse pedido foi cancelado.", "aviso")
        return redirect(url_for("carrinho.ver_carrinho"))

    aviso = ""
    try:
        dados = montar_acompanhamento(pedido)
    except Exception as e:
        print("ERRO NO ACOMPANHAMENTO:", e)
        aviso = "Não foi possível atualizar o status agora. Estamos mostrando a última informação que temos."
        dados = montar_dados(pedido["numero"], pedido["status"], 0, None)

    itens = []
    try:
        itens = pedido_model.listar_itens_do_pedido(pedido["id"])
    except Exception as e:
        print("ERRO AO LISTAR OS ITENS DO PEDIDO:", e)

    return render_template("acompanhar_pedido.html", dados=dados, pedido=pedido, itens=itens, aviso=aviso)


# rota que devolve o status em json (o javascript da tela chama ela de tempos em tempos pra atualizar sem recarregar a página)
@acompanhamento_bp.route("/api/pedido/<int:numero>/status")
def api_status(numero):
    if "tipo" not in session:
        return jsonify({"erro": "Entre ou continue como visitante."}), 401

    try:
        pedido = pedido_model.buscar_pedido_por_numero(numero)
    except Exception as e:
        print("ERRO NA API DE STATUS:", e)
        return jsonify({"erro": "Não foi possível buscar o pedido agora."}), 500

    # quem não pode ver o pedido recebe o mesmo "não encontrado" de quem pediu um pedido que não existe
    if pode_acessar(pedido) == False:
        return jsonify({"erro": "Pedido não encontrado."}), 404

    if pedido["status"] == "AGUARDANDO_PAGAMENTO" or pedido["status"] == "CANCELADO":
        return jsonify({"erro": "Esse pedido não está sendo entregue."}), 409

    try:
        dados = montar_acompanhamento(pedido)
    except Exception as e:
        print("ERRO NA API DE STATUS:", e)
        return jsonify({"erro": "Não foi possível atualizar o status agora."}), 500

    return jsonify(dados)


# BUSCAR PEDIDO por n. ou e-mail (cartão 18: o visitante acompanha sem ter conta)
@acompanhamento_bp.route("/acompanhar", methods=["GET", "POST"])
def buscar():
    erros = {}
    dados = {"numero": "", "email": ""}
    erro_geral = ""

    if request.method == "POST":
        # o # na frente do número é aceito (ex: #10002)
        numero_texto = request.form.get("numero", "").strip().replace("#", "")
        email = request.form.get("email", "").strip().lower()
        dados["numero"] = numero_texto
        dados["email"] = email

        if validacoes.so_tem_numeros(numero_texto) == False or len(numero_texto) > 9:
            erros["numero"] = "Digite só os números do pedido. Exemplo: 10002"
        if validacoes.validar_email(email) == False:
            erros["email"] = "E-mail inválido. Exemplo: nome@gmail.com"

        if len(erros) == 0:
            pedido = None
            deu_erro_no_banco = False
            try:
                pedido = pedido_model.buscar_pedido_por_numero(int(numero_texto))
            except Exception as e:
                print("ERRO AO BUSCAR O PEDIDO:", e)
                deu_erro_no_banco = True

            if deu_erro_no_banco == True:
                erro_geral = "Não foi possível buscar o pedido agora. Tente de novo em alguns minutos."
            else:
                # só acha pedido de visitante (quem tem conta entra na conta), que já foi pago, e com o e-mail certo
                achou = False
                if pedido is not None:
                    if pedido["id_cliente"] is None and pedido["email_contato"].lower() == email:
                        if pedido["status"] != "AGUARDANDO_PAGAMENTO" and pedido["status"] != "CANCELADO":
                            achou = True

                if achou == False:
                    # a mesma mensagem pra qualquer motivo (assim ninguém descobre quais pedidos existem)
                    erro_geral = "Não encontramos um pedido com esse número e e-mail."
                else:
                    # libera esse pedido pra essa sessão (guarda no máximo os 10 últimos)
                    liberados = session.get("pedidos_liberados", [])
                    if pedido["id"] not in liberados:
                        liberados.append(pedido["id"])
                    session["pedidos_liberados"] = liberados[-10:]

                    if "tipo" not in session:
                        session["tipo"] = "visitante"
                    return redirect(url_for("acompanhamento.acompanhar", numero=pedido["numero"]))

    return render_template("acompanhar_busca.html", erros=erros, dados=dados, erro_geral=erro_geral)