from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify, flash
from models import produto_model
from models import validacoes

# o blueprint é tipo um "pedaço" do site, depois eu registro ele no app.py
vitrine_bp = Blueprint("vitrine", __name__)

# função que transforma o texto da url em número (ou None se não for número)
def ler_numero(texto):
    if validacoes.so_tem_numeros(texto) == False:
        return None
    # número muito grande o banco não aceita
    if len(texto) > 9:
        return None
    return int(texto)

# rota da pagina inicial (vitrine)
@vitrine_bp.route("/")
def vitrine():
    # se a pessoa ainda não entrou nem escolheu ser visitante, manda pro login
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    # o pop-up do cupom só aparece uma vez (o pop tira da sessão depois de ler)
    mostrar_cupom = session.pop("mostrar_cupom", False)

    # se a pessoa ainda não entrou nem escolheu ser visitante, manda pro login
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    # o pop-up do cupom só aparece uma vez (o pop tira da sessão depois de ler)
    mostrar_cupom = session.pop("mostrar_cupom", False)

    # pega o que veio na url (ex: /?categoria=3&busca=limao)
    id_categoria = ler_numero(request.args.get("categoria", ""))
    busca = request.args.get("busca", "").strip()[:60]
    categoria_atual = ""
    if id_categoria is not None:
        categoria_atual = str(id_categoria)

    categorias = []
    cupcakes = []
    erro = ""
    aviso = ""

    
    # tenta buscar os cupcakes no banco
    # se der erro (banco desligado, senha errada...) mostra uma mensagem em vez de quebrar
    try:
        categorias = produto_model.listar_categorias()
        cupcakes = produto_model.listar_cupcakes_filtrados(id_categoria, busca)
    except Exception as e:
        print("ERRO AO BUSCAR NO BANCO:", e)
        erro = "Não foi possível carregar os cupcakes agora. Tente de novo em alguns minutos."

    # se não veio nenhum cupcake e não deu erro, avisa que está vazio
    if erro == "":
        if len(cupcakes) == 0:
            # se a pessoa estava filtrando ou buscando, a mensagem é outra
            if id_categoria is not None or busca != "":
                aviso = "Nenhum cupcake encontrado. Tente outra busca ou outra categoria."
            else:
                aviso = "Nenhum cupcake disponível no momento."

                
    # manda os dados pro html
    return render_template("vitrine.html", cupcakes=cupcakes, erro=erro, aviso=aviso,
                           categorias=categorias, categoria_atual=categoria_atual,
                           busca_atual=busca, mostrar_cupom=mostrar_cupom)


# rota da tela de detalhes do cupcake (cartão 03)
@vitrine_bp.route("/cupcake/<int:id_cupcake>")
def detalhe(id_cupcake):
    # quem não entrou nem escolheu ser visitante vai pro login
    if "tipo" not in session:
        return redirect(url_for("auth.login"))

    cupcake = None
    deu_erro_no_banco = False

    # o banco não aceita número muito grande, então já descarta aqui
    if id_cupcake < 2000000000:
        try:
            cupcake = produto_model.buscar_cupcake_por_id(id_cupcake)
        except Exception as e:
            print("ERRO AO BUSCAR O CUPCAKE:", e)
            deu_erro_no_banco = True

    if deu_erro_no_banco == True:
        flash("Não foi possível abrir esse cupcake agora. Tente de novo em alguns minutos.", "erro")
        return redirect(url_for("vitrine.vitrine"))

    # não achou, ou o cupcake está sem estoque
    if cupcake is None:
        flash("Esse cupcake não está disponível no momento.", "aviso")
        return redirect(url_for("vitrine.vitrine"))

    return render_template("detalhe.html", c=cupcake)


# rota que devolve os cupcakes em json
@vitrine_bp.route("/api/cupcakes")
def api_cupcakes():
    # se a sessão acabou, avisa o javascript
    if "tipo" not in session:
        return jsonify({"erro": "Entre ou continue como visitante."}), 401

    id_categoria = ler_numero(request.args.get("categoria", ""))
    busca = request.args.get("busca", "").strip()[:60]

    try:
        cupcakes = produto_model.listar_cupcakes_filtrados(id_categoria, busca)
    except Exception as e:
        print("ERRO NA API DE CUPCAKES:", e)
        return jsonify({"erro": "Não foi possível carregar os cupcakes agora."}), 500

    return jsonify({"cupcakes": cupcakes})