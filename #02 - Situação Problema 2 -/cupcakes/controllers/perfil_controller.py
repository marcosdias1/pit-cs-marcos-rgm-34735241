from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import validacoes
from models import perfil_model
from models import perfil_regras

# controller do Meu perfil (tela 12): dados da conta e endereços
# cartão 20: gerenciar dados (a parte de pagamentos salvos ficou de fora)


perfil_bp = Blueprint("perfil", __name__)

# os campos do formulário de endereço
CAMPOS_DO_ENDERECO = ["apelido", "cep", "rua", "numero", "complemento", "bairro", "cidade", "uf"]


# função que confere se quem está usando é um cliente com conta
# devolve um redirect (se não for) ou None (se pode seguir)
def conferir_acesso():
    if "tipo" not in session:
        return redirect(url_for("auth.login"))
    if session.get("tipo") != "cliente":
        flash("Entre na sua conta para ver o seu perfil.", "aviso")
        return redirect(url_for("auth.login"))
    return None


# função que pega o que a pessoa digitou no formulário de endereço, sem espaço sobrando
def ler_formulario_do_endereco():
    dados = {}
    for campo in CAMPOS_DO_ENDERECO:
        dados[campo] = request.form.get(campo, "").strip()
    dados["uf"] = dados["uf"].upper()
    return dados


# função que prepara os dados do endereço pra gravar no banco
# (cep só com números, e apelido e complemento vazios viram "nada" no banco)
def preparar_para_gravar(dados):
    campos = dict(dados)
    campos["cep"] = validacoes.tirar_enfeites(dados["cep"])
    if campos["apelido"] == "":
        campos["apelido"] = None
    if campos["complemento"] == "":
        campos["complemento"] = None
    return campos


# TELA 12 - Meu perfil: os dados da conta (o formulário de cima) e a lista de endereços
@perfil_bp.route("/perfil", methods=["GET", "POST"])
def perfil():
    resposta = conferir_acesso()
    if resposta is not None:
        return resposta

    id_cliente = session.get("id_cliente")
    erros = {}
    erro_geral = ""
    cliente = None
    enderecos = []

    try:
        cliente = perfil_model.buscar_dados_do_cliente(id_cliente)
        enderecos = perfil_model.listar_enderecos(id_cliente)
    except Exception as e:
        print("ERRO AO ABRIR O PERFIL:", e)
        return render_template("perfil.html", dados={"nome": "", "email": "", "celular": ""}, cpf="",
                               erros={}, erro_geral="Não foi possível abrir o seu perfil agora. Tente de novo em alguns minutos.",
                               enderecos=[], maximo=perfil_regras.MAXIMO_DE_ENDERECOS)

    # conta que não existe mais (ou foi desativada): sai da sessão
    if cliente is None:
        session.clear()
        flash("Não encontramos a sua conta. Entre de novo.", "erro")
        return redirect(url_for("auth.login"))

    # o que aparece nos campos: o que está no banco (celular com parênteses e traço)
    dados = {}
    dados["nome"] = cliente["nome"]
    dados["email"] = cliente["email"]
    dados["celular"] = perfil_regras.formatar_celular(cliente["celular"])

    if request.method == "POST":
        # o que a pessoa digitou (assim os campos não perdem o que ela escreveu se der erro)
        dados["nome"] = request.form.get("nome", "").strip()
        dados["email"] = request.form.get("email", "").strip().lower()
        dados["celular"] = request.form.get("celular", "").strip()

        erros = validacoes.conferir_contato(dados["nome"], dados["email"], dados["celular"])

        if len(erros) == 0:
            try:
                if perfil_model.email_em_uso_por_outro(dados["email"], id_cliente) == True:
                    erros["email"] = "Esse e-mail já está cadastrado."
                else:
                    perfil_model.atualizar_dados(id_cliente, dados["nome"], dados["email"],
                                                 validacoes.tirar_enfeites(dados["celular"]))
                    # o nome que aparece no topo do site vem da sessão
                    session["nome"] = dados["nome"]
                    flash("Seus dados foram atualizados.", "ok")
                    return redirect(url_for("perfil.perfil"))
            except Exception as e:
                print("ERRO AO ATUALIZAR OS DADOS:", e)
                erro_geral = "Não foi possível salvar agora. Tente de novo em alguns minutos."

    return render_template("perfil.html", dados=dados, cpf=perfil_regras.mascarar_cpf(cliente["cpf"]),
                           erros=erros, erro_geral=erro_geral, enderecos=enderecos,
                           maximo=perfil_regras.MAXIMO_DE_ENDERECOS)


# Endereço novo
@perfil_bp.route("/perfil/endereco/novo", methods=["GET", "POST"])
def novo_endereco():
    resposta = conferir_acesso()
    if resposta is not None:
        return resposta

    id_cliente = session.get("id_cliente")

    # confere o limite de endereços
    try:
        if perfil_model.contar_enderecos(id_cliente) >= perfil_regras.MAXIMO_DE_ENDERECOS:
            flash("Você já tem " + str(perfil_regras.MAXIMO_DE_ENDERECOS) +
                  " endereços. Exclua um para poder adicionar outro.", "aviso")
            return redirect(url_for("perfil.perfil"))
    except Exception as e:
        print("ERRO AO CONTAR OS ENDEREÇOS:", e)
        flash("Não foi possível abrir essa tela agora. Tente de novo em alguns minutos.", "erro")
        return redirect(url_for("perfil.perfil"))

    dados = {}
    for campo in CAMPOS_DO_ENDERECO:
        dados[campo] = ""
    erros = {}
    erro_geral = ""

    if request.method == "POST":
        dados = ler_formulario_do_endereco()
        erros = perfil_regras.conferir_endereco_do_perfil(dados["apelido"], dados["cep"], dados["rua"],
                                                          dados["numero"], dados["complemento"], dados["bairro"],
                                                          dados["cidade"], dados["uf"])
        if len(erros) == 0:
            try:
                perfil_model.criar_endereco(id_cliente, preparar_para_gravar(dados))
                flash("Endereço guardado.", "ok")
                return redirect(url_for("perfil.perfil"))
            except Exception as e:
                print("ERRO AO GUARDAR O ENDEREÇO:", e)
                erro_geral = "Não foi possível guardar o endereço agora. Tente de novo em alguns minutos."

    return render_template("endereco_form.html", titulo="Novo endereço",
                           acao=url_for("perfil.novo_endereco"),
                           dados=dados, erros=erros, erro_geral=erro_geral)


# Editar um endereço
@perfil_bp.route("/perfil/endereco/<int:id_endereco>/editar", methods=["GET", "POST"])
def editar_endereco(id_endereco):
    resposta = conferir_acesso()
    if resposta is not None:
        return resposta

    id_cliente = session.get("id_cliente")

    endereco = None
    try:
        endereco = perfil_model.buscar_endereco(id_cliente, id_endereco)
    except Exception as e:
        print("ERRO AO BUSCAR O ENDEREÇO:", e)
        flash("Não foi possível abrir o endereço agora. Tente de novo em alguns minutos.", "erro")
        return redirect(url_for("perfil.perfil"))

    # endereço que não existe ou é de outra pessoa
    if endereco is None:
        flash("Endereço não encontrado.", "erro")
        return redirect(url_for("perfil.perfil"))

    # começa com o que está guardado
    dados = {}
    dados["apelido"] = endereco["apelido"] or ""
    dados["cep"] = perfil_regras.formatar_cep(endereco["cep"])
    dados["rua"] = endereco["rua"]
    dados["numero"] = endereco["numero"]
    dados["complemento"] = endereco["complemento"] or ""
    dados["bairro"] = endereco["bairro"]
    dados["cidade"] = endereco["cidade"]
    dados["uf"] = endereco["uf"]
    erros = {}
    erro_geral = ""

    if request.method == "POST":
        dados = ler_formulario_do_endereco()
        erros = perfil_regras.conferir_endereco_do_perfil(dados["apelido"], dados["cep"], dados["rua"],
                                                          dados["numero"], dados["complemento"], dados["bairro"],
                                                          dados["cidade"], dados["uf"])
        if len(erros) == 0:
            try:
                achou = perfil_model.substituir_endereco(id_cliente, id_endereco, preparar_para_gravar(dados))
                if achou == False:
                    flash("Endereço não encontrado.", "erro")
                else:
                    flash("Endereço atualizado.", "ok")
                return redirect(url_for("perfil.perfil"))
            except Exception as e:
                print("ERRO AO ATUALIZAR O ENDEREÇO:", e)
                erro_geral = "Não foi possível guardar o endereço agora. Tente de novo em alguns minutos."

    return render_template("endereco_form.html", titulo="Editar endereço",
                           acao=url_for("perfil.editar_endereco", id_endereco=id_endereco),
                           dados=dados, erros=erros, erro_geral=erro_geral)


# Marcar um endereço como principal
@perfil_bp.route("/perfil/endereco/<int:id_endereco>/principal", methods=["POST"])
def endereco_principal(id_endereco):
    resposta = conferir_acesso()
    if resposta is not None:
        return resposta

    try:
        achou = perfil_model.definir_principal(session.get("id_cliente"), id_endereco)
        if achou == True:
            flash("Pronto! Esse endereço agora vem preenchido no fechamento do pedido.", "ok")
        else:
            flash("Endereço não encontrado.", "erro")
    except Exception as e:
        print("ERRO AO MARCAR O ENDEREÇO PRINCIPAL:", e)
        flash("Não foi possível alterar agora. Tente de novo em alguns minutos.", "erro")

    return redirect(url_for("perfil.perfil"))


# Excluir um endereço
@perfil_bp.route("/perfil/endereco/<int:id_endereco>/excluir", methods=["POST"])
def endereco_excluir(id_endereco):
    resposta = conferir_acesso()
    if resposta is not None:
        return resposta

    id_cliente = session.get("id_cliente")

    try:
        endereco = perfil_model.buscar_endereco(id_cliente, id_endereco)
        if endereco is None:
            flash("Endereço não encontrado.", "erro")
        else:
            total = perfil_model.contar_enderecos(id_cliente)
            motivo = perfil_regras.motivo_para_nao_excluir(endereco["principal"], total)
            if motivo != "":
                flash(motivo, "aviso")
            else:
                perfil_model.excluir_endereco(id_cliente, id_endereco)
                flash("Endereço excluído.", "ok")
    except Exception as e:
        print("ERRO AO EXCLUIR O ENDEREÇO:", e)
        flash("Não foi possível excluir agora. Tente de novo em alguns minutos.", "erro")

    return redirect(url_for("perfil.perfil"))