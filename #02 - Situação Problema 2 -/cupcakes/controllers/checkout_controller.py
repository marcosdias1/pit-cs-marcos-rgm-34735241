from datetime import date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import carrinho_model
from models import pedido_model
from models import validacoes
from models import frete
from models import cupom_regras
from controllers.carrinho_controller import pegar_id_do_carrinho

# controller do fechamento do pedido (tela 7)
# casos de uso dos cartões 10 (frete), 09 (cupom) e 18 (visitante informa o e-mail)


checkout_bp = Blueprint("checkout", __name__)

# os campos do formulário (lista pra pegar todos de uma vez)
CAMPOS = ["cep", "rua", "numero", "bairro", "cidade", "uf", "nome", "email", "celular", "cupom"]


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
    dados["uf"] = dados["uf"].upper()
    dados["email"] = dados["email"].lower()
    # o código do cupom é sempre em maiúsculas e tem no máximo 30 letras
    dados["cupom"] = dados["cupom"].upper()[:30]
    return dados


# função que monta o que já vem preenchido quando a pessoa abre a tela - 1º o que ela já tinha digitado (guardado na sessão), 2º o endereço principal da conta
def dados_iniciais(id_cliente):
    dados = dados_vazios()

    guardado = session.get("checkout")
    if guardado is not None:
        for campo in CAMPOS:
            dados[campo] = guardado.get(campo, "")
        return dados

    if id_cliente is not None:
        endereco = pedido_model.buscar_endereco_principal(id_cliente)
        if endereco is not None:
            for campo in ["cep", "rua", "numero", "bairro", "cidade", "uf"]:
                dados[campo] = endereco[campo]

    return dados


# TELA 7 - Fechar pedido (cartão 10)
@checkout_bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    # quem não entrou nem escolheu ser visitante vai pro login
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    eh_cliente = (session.get("tipo") == "cliente")
    id_cliente = None
    if eh_cliente == True:
        id_cliente = session.get("id_cliente")

    #  1) confere o carrinho 
    itens = []
    try:
        id_carrinho = pegar_id_do_carrinho()
        itens = carrinho_model.listar_itens(id_carrinho)
    except Exception as e:
        print("ERRO AO ABRIR O FECHAMENTO DO PEDIDO:", e)
        flash("Não foi possível abrir o fechamento do pedido agora. Tente de novo em alguns minutos.", "erro")
        return redirect(url_for("carrinho.ver_carrinho"))

    # se tem algum problema no carrinho (vazio, sem cupcake, sem estoque), volta pra lá
    problema = carrinho_model.conferir_carrinho(itens)
    if problema != "":
        flash(problema, "erro")
        return redirect(url_for("carrinho.ver_carrinho"))

    subtotal = carrinho_model.calcular_subtotal(itens)

    #  2) pega os dados da tela 
    erro_geral = ""
    if request.method == "POST":
        dados = ler_formulario()
    else:
        dados = dados_vazios()
        try:
            dados = dados_iniciais(id_cliente)
        except Exception as e:
            print("ERRO AO BUSCAR O ENDEREÇO SALVO:", e)
            erro_geral = "Não foi possível buscar o seu endereço salvo. Preencha o endereço abaixo."

    # o contato do cliente logado vem da conta dele
    contato = None
    if eh_cliente == True:
        try:
            contato = pedido_model.buscar_contato_do_cliente(id_cliente)
        except Exception as e:
            print("ERRO AO BUSCAR O CONTATO:", e)

    #  3) confere o endereço (e o contato, se for visitante) 
    erros = validacoes.conferir_endereco(dados["cep"], dados["rua"], dados["numero"],
                                         dados["bairro"], dados["cidade"], dados["uf"])
    if eh_cliente == False:
        erros_do_contato = validacoes.conferir_contato(dados["nome"], dados["email"], dados["celular"])
        for campo in erros_do_contato:
            erros[campo] = erros_do_contato[campo]

    #  4) calcula o frete 
    frete_info = None
    sem_entrega = False
    if "bairro" not in erros and "cidade" not in erros and "uf" not in erros:
        frete_info = frete.calcular_frete(dados["bairro"], dados["cidade"], dados["uf"])
        if frete_info is None:
            sem_entrega = True

    #  5) confere o cupom 
    cupom = None
    cupom_erro = ""
    desconto = Decimal("0.00")
    try:
        resposta = pedido_model.escolher_cupom(id_cliente, dados["cupom"], subtotal, date.today())
        cupom = resposta[0]
        cupom_erro = resposta[1]
    except Exception as e:
        print("ERRO AO CONFERIR O CUPOM:", e)
        cupom_erro = "Não foi possível conferir o cupom agora. Tente de novo em alguns minutos."

    if cupom is not None:
        desconto = cupom_regras.calcular_desconto(cupom, subtotal)

    #  6) monta o resumo (subtotal + frete - desconto) 
    resumo = {}
    resumo["subtotal"] = carrinho_model.formatar_dinheiro(subtotal)
    resumo["frete"] = ""
    resumo["regiao"] = ""
    resumo["minutos"] = 0
    resumo["total"] = ""
    resumo["tem_cupom"] = (cupom is not None)
    resumo["cupom_codigo"] = ""
    resumo["cupom_automatico"] = False
    resumo["desconto"] = carrinho_model.formatar_dinheiro(desconto)

    if cupom is not None:
        resumo["cupom_codigo"] = cupom["codigo"]
        # se a pessoa não digitou nada, o cupom entrou sozinho (o desconto do cpf)
        if dados["cupom"] == "":
            resumo["cupom_automatico"] = True

    if frete_info is not None:
        resumo["frete"] = carrinho_model.formatar_dinheiro(frete_info["valor"])
        resumo["regiao"] = frete_info["regiao"]
        resumo["minutos"] = frete_info["minutos"]
        total = carrinho_model.calcular_total(subtotal, frete_info["valor"], desconto)
        resumo["total"] = carrinho_model.formatar_dinheiro(total)

    #  7) guarda os dados na sessão (a parte 2 usa pra criar o pedido) 
    if request.method == "POST" and len(erros) == 0 and frete_info is not None:
        guardar = dict(dados)
        # cupom que não pode ser usado não vai pra sessão
        if cupom_erro != "":
            guardar["cupom"] = ""
        session["checkout"] = guardar

    #  8) se clicou em "Ir para o pagamento", cria o pedido e vai pro pagamento (cartão 11) 
    if request.method == "POST" and request.form.get("acao", "") == "pagar":
        contato_do_pedido = None
        if eh_cliente == True:
            # o contato do cliente vem da conta dele
            contato_do_pedido = contato
        else:
            contato_do_pedido = {}
            contato_do_pedido["nome"] = dados["nome"]
            contato_do_pedido["email"] = dados["email"]
            contato_do_pedido["celular"] = validacoes.tirar_enfeites(dados["celular"])

        if len(erros) > 0 or frete_info is None:
            # os erros já aparecem nos campos, aqui só avisa que precisa corrigir
            erro_geral = "Corrija os campos marcados em vermelho para ir para o pagamento."
        elif cupom_erro != "":
            erro_geral = "Corrija o cupom (ou apague o código) para ir para o pagamento."
        elif contato_do_pedido is None:
            erro_geral = "Não foi possível buscar o seu contato agora. Tente de novo em alguns minutos."
        else:
            try:
                endereco_do_pedido = {}
                endereco_do_pedido["cep"] = validacoes.tirar_enfeites(dados["cep"])
                endereco_do_pedido["rua"] = dados["rua"]
                endereco_do_pedido["numero"] = dados["numero"]
                endereco_do_pedido["bairro"] = dados["bairro"]
                endereco_do_pedido["cidade"] = dados["cidade"]
                endereco_do_pedido["uf"] = dados["uf"]

                id_do_cupom = None
                if cupom is not None:
                    id_do_cupom = cupom["id"]

                total_do_pedido = carrinho_model.calcular_total(subtotal, frete_info["valor"], desconto)

                # o pedido que ela já tinha criado e não pagou (se tiver) é cancelado
                novo = pedido_model.criar_pedido(id_cliente, contato_do_pedido, endereco_do_pedido, itens, subtotal, frete_info, desconto, total_do_pedido, id_do_cupom, session.get("pedido_atual"))

                # guarda na sessão qual é o pedido dela (o visitante só vê o pedido que ele mesmo criou)
                session["pedido_atual"] = novo["id"]
                return redirect(url_for("pagamento.pagar", numero=novo["numero"]))

            except Exception as e:
                print("ERRO AO CRIAR O PEDIDO:", e)
                erro_geral = "Não foi possível criar o pedido agora. Tente de novo em alguns minutos."

    # os erros dos campos só aparecem depois que a pessoa clicou no botão
    erros_da_tela = {}
    if request.method == "POST":
        erros_da_tela = erros

    return render_template("checkout.html", dados=dados, erros=erros_da_tela, eh_cliente=eh_cliente,
                           contato=contato, resumo=resumo, sem_entrega=sem_entrega,
                           cupom_erro=cupom_erro, erro_geral=erro_geral)