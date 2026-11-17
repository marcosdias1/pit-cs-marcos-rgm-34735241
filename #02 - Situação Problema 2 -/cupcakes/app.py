from flask import Flask, session, render_template
from config import *
from controllers.vitrine_controller import vitrine_bp
from controllers.auth_controller import auth_bp
from controllers.carrinho_controller import carrinho_bp
from controllers.checkout_controller import checkout_bp
from controllers.pagamento_controller import pagamento_bp
from controllers.acompanhamento_controller import acompanhamento_bp
from controllers.pedidos_controller import pedidos_bp
from controllers.senha_controller import senha_bp
from controllers.perfil_controller import perfil_bp
from controllers.evento_controller import evento_bp
from models import carrinho_model


# cria o app do flask
app = Flask(__name__, static_folder="public/static")
app.secret_key = CHAVE_SECRETA
app.register_blueprint(vitrine_bp) # registra as rotas da vitrine
app.register_blueprint(auth_bp) # registra as rotas de login e cadastro
app.register_blueprint(carrinho_bp) # registra as rotas do carrinho
app.register_blueprint(checkout_bp) # registra as rotas do fechamento do pedido
app.register_blueprint(pagamento_bp) # registra as rotas do pagamento e do pedido confirmado
app.register_blueprint(acompanhamento_bp) # registra as rotas do acompanhamento do pedido
app.register_blueprint(pedidos_bp) # registra as rotas do histórico de compras (Meus pedidos)
app.register_blueprint(senha_bp) # registra as rotas da recuperação de senha
app.register_blueprint(perfil_bp) # registra as rotas do Meu perfil (dados e endereços)
app.register_blueprint(evento_bp) # registra as rotas do orçamento para eventos

# essa função roda antes de desenhar qualquer página e manda a quantidade do carrinho pro html (o numerozinho do ícone do carrinho no topo)
@app.context_processor
def quantidade_do_carrinho():
    quantidade = 0
    try:
        quantidade = carrinho_model.contar_itens(session.get("id_cliente"), session.get("id_sessao"))
    except Exception as e:
        # se o banco falhar, a página abre mesmo assim, só com 0 no carrinho
        print("ERRO AO CONTAR O CARRINHO:", e)
    return {"quantidade_carrinho": quantidade}

# páginas de erro em português, com botão pra voltar (antes aparecia o "Not Found" em inglês do Flask)
# a função recebe o erro, mas aqui eu não uso ele
@app.errorhandler(404)
def pagina_nao_encontrada(erro):
    mensagem = "Não encontramos a página que você procurou. Confira o endereço ou volte para a vitrine."
    return render_template("erro.html", codigo=404, titulo="Página não encontrada", mensagem=mensagem), 404

@app.errorhandler(405)
def metodo_nao_permitido(erro):
    mensagem = "Essa página não pode ser aberta desse jeito. Volte e tente de novo pelos botões do site."
    return render_template("erro.html", codigo=405, titulo="Ação não permitida", mensagem=mensagem), 405

@app.errorhandler(500)
def erro_do_servidor(erro):
    mensagem = "Algo deu errado do nosso lado. Tente de novo em alguns minutos."
    return render_template("erro.html", codigo=500, titulo="Algo deu errado", mensagem=mensagem), 500

if __name__ == "__main__":
    app.run(debug=True)