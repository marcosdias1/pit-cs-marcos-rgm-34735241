# controller do orçamento de evento (grandes encomendas)
# cartão 08: mínimo de 30 cupcakes; abaixo disso a pessoa é orientada a comprar pelo carrinho

from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import validacoes
from models import pedido_model
from models import perfil_regras
from models import evento_regras
from models import evento_model
from models import email_simulado

evento_bp = Blueprint("evento", __name__)

# os campos do formulário
CAMPOS = ["nome", "email", "celular", "data", "quantidade", "tema", "observacoes"]


# função que cria os dados do formulário todos vazios
def dados_vazios():
    dados = {}
    for campo in CAMPOS:
        dados[campo] = ""
    return dados


# função que pega o que a pessoa digitou no formulário, já sem espaço sobrando
def ler_formulario():
    dados = {}
    for campo in CAMPOS:
        dados[campo] = request.form.get(campo, "").strip()
    dados["email"] = dados["email"].lower()
    return dados


# TELA 13 - Pedir orçamento de evento (cartão 08)
# qualquer pessoa pode pedir, tenha conta ou não
@evento_bp.route("/evento", methods=["GET", "POST"])
def pedir_orcamento():
    eh_cliente = (session.get("tipo") == "cliente")
    id_cliente = None
    if eh_cliente == True:
        id_cliente = session.get("id_cliente")

    hoje = date.today()
    dados = dados_vazios()
    erros = {}
    erro_geral = ""
    abaixo_do_minimo = False

    if request.method == "GET" and eh_cliente == True:
        # cliente com conta já começa com o nome, o e-mail e o celular dele
        try:
            contato = pedido_model.buscar_contato_do_cliente(id_cliente)
            if contato is not None:
                dados["nome"] = contato["nome"]
                dados["email"] = contato["email"]
                dados["celular"] = perfil_regras.formatar_celular(contato["celular"])
        except Exception as e:
            print("ERRO AO BUSCAR O CONTATO:", e)

    if request.method == "POST":
        dados = ler_formulario()
        erros = evento_regras.conferir_pedido_de_evento(dados["nome"], dados["email"], dados["celular"],
                                                        dados["data"], dados["quantidade"], dados["tema"],
                                                        dados["observacoes"], hoje)
        abaixo_do_minimo = evento_regras.quantidade_abaixo_do_minimo(dados["quantidade"])

        if len(erros) == 0:
            # prepara os dados pra gravar (tema e observações vazios viram "nada" no banco)
            campos = {}
            campos["nome"] = dados["nome"]
            campos["email"] = dados["email"]
            campos["celular"] = validacoes.tirar_enfeites(dados["celular"])
            campos["data_evento"] = evento_regras.ler_data(dados["data"])
            campos["quantidade"] = int(dados["quantidade"])
            campos["tema"] = None
            if dados["tema"] != "":
                campos["tema"] = dados["tema"]
            campos["observacoes"] = None
            if dados["observacoes"] != "":
                campos["observacoes"] = dados["observacoes"]

            try:
                recentes = evento_model.contar_solicitacoes_recentes(campos["email"])
                if recentes >= evento_regras.MAXIMO_POR_DIA:
                    erro_geral = "Esse e-mail já mandou " + str(evento_regras.MAXIMO_POR_DIA) + " pedidos hoje. Aguarde a nossa resposta."
                else:
                    numero = evento_model.criar_solicitacao(id_cliente, campos)

                    # os e-mails são simulados (a loja e quem pediu recebem).
                    # se der erro aqui o pedido já está guardado, então não desfaz nada
                    try:
                        assunto, texto = evento_regras.montar_email_para_a_loja(numero, campos)
                        email_simulado.enviar(evento_regras.EMAIL_DA_LOJA, assunto, texto)
                        assunto, texto = evento_regras.montar_email_para_o_cliente(numero, campos)
                        email_simulado.enviar(campos["email"], assunto, texto)
                    except Exception as e:
                        print("ERRO AO ENVIAR O E-MAIL DO ORÇAMENTO:", e)

                    # guarda na sessão pra tela de "enviado" mostrar o protocolo
                    session["evento_enviado"] = {"numero": numero, "email": campos["email"]}
                    return redirect(url_for("evento.enviado"))

            except Exception as e:
                print("ERRO AO GUARDAR O ORÇAMENTO:", e)
                erro_geral = "Não foi possível enviar o pedido agora. Tente de novo em alguns minutos."

    return render_template("evento_form.html", dados=dados, erros=erros, erro_geral=erro_geral,
                           abaixo_do_minimo=abaixo_do_minimo,
                           minimo=evento_regras.MINIMO_DE_UNIDADES,
                           data_minima=evento_regras.primeira_data_aceita(hoje).isoformat(),
                           data_maxima=evento_regras.ultima_data_aceita(hoje).isoformat(),
                           antecedencia=evento_regras.DIAS_DE_ANTECEDENCIA)


# Tela de "pedido enviado"
@evento_bp.route("/evento/enviado")
def enviado():
    guardado = session.get("evento_enviado")
    if guardado is None:
        return redirect(url_for("evento.pedir_orcamento"))

    return render_template("evento_enviado.html", numero=guardado["numero"], email=guardado["email"],
                           prazo=evento_regras.PRAZO_DE_RESPOSTA)