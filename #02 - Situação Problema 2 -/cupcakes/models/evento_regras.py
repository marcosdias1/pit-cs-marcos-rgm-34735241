# regras do orçamento de evento / grandes encomendas (cartão 08)
# regra do cartão: mínimo de 30 cupcakes; abaixo disso a pessoa é orientada a comprar pelo carrinho

from datetime import datetime, timedelta
from models import validacoes

# mínimo do cartão 08 (o banco também confere: ck_solicitacao_qtd)
MINIMO_DE_UNIDADES = 30

# máximo que o formulário aceita (premissa minha, pra não aceitar número absurdo)
MAXIMO_DE_UNIDADES = 1000

# com quantos dias de antecedência a loja precisa ser avisada (premissa minha, combinar com o cliente)
DIAS_DE_ANTECEDENCIA = 3

# até quantos dias pra frente aceita a data do evento
DIAS_MAXIMOS_A_FRENTE = 365

# quantos pedidos de orçamento o mesmo e-mail pode mandar por dia (pra ninguém encher a caixa da loja)
MAXIMO_POR_DIA = 3

# o e-mail da loja, que recebe os dados do pedido de orçamento (e-mail de exemplo, o envio é simulado)
EMAIL_DA_LOJA = "contato@lojadecupcakes.exemplo"

# em quanto tempo a loja promete responder (premissa minha)
PRAZO_DE_RESPOSTA = "2 dias úteis"


# função que transforma o texto da data em data de verdade
# aceita 2026-11-30 (o que o navegador manda) e 30/11/2026 (se a pessoa digitar)
# devolve a data, ou None se o texto não for uma data
def ler_data(texto):
    for formato in ["%Y-%m-%d", "%d/%m/%Y"]:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    return None


# função que escreve a data como dia/mês/ano
def formatar_data(data):
    return data.strftime("%d/%m/%Y")


# função que diz a primeira data que a loja aceita (hoje + a antecedência)
def primeira_data_aceita(hoje):
    return hoje + timedelta(days=DIAS_DE_ANTECEDENCIA)


# função que diz a última data que a loja aceita
def ultima_data_aceita(hoje):
    return hoje + timedelta(days=DIAS_MAXIMOS_A_FRENTE)


# função que diz se a quantidade digitada é um número menor que o mínimo
# (a tela usa isso pra mostrar o aviso "compre pelo carrinho")
def quantidade_abaixo_do_minimo(quantidade_texto):
    if validacoes.so_tem_numeros(quantidade_texto) == False or len(quantidade_texto) > 6:
        return False
    return int(quantidade_texto) < MINIMO_DE_UNIDADES


# função que confere o formulário inteiro
# devolve um dicionário com os erros (vazio = tudo certo)
def conferir_pedido_de_evento(nome, email, celular, data_texto, quantidade_texto, tema, observacoes, hoje):
    # nome, e-mail e celular têm as mesmas regras do contato do visitante
    erros = validacoes.conferir_contato(nome, email, celular)

    # data do evento
    data = ler_data(data_texto)
    if data is None:
        erros["data"] = "Informe a data do evento."
    elif data < primeira_data_aceita(hoje):
        erros["data"] = "Precisamos de pelo menos " + str(DIAS_DE_ANTECEDENCIA) + " dias de antecedência. Escolha uma data a partir de " + formatar_data(primeira_data_aceita(hoje)) + "."
    elif data > ultima_data_aceita(hoje):
        erros["data"] = "Escolha uma data dentro de 1 ano."

    # quantidade
    if validacoes.so_tem_numeros(quantidade_texto) == False or len(quantidade_texto) > 6:
        erros["quantidade"] = "Digite só números. Exemplo: 50"
    else:
        quantidade = int(quantidade_texto)
        if quantidade < MINIMO_DE_UNIDADES:
            erros["quantidade"] = "Para eventos o mínimo é de " + str(MINIMO_DE_UNIDADES) + " cupcakes. Para menos que isso, compre pelo carrinho."
        elif quantidade > MAXIMO_DE_UNIDADES:
            erros["quantidade"] = "Para mais de " + str(MAXIMO_DE_UNIDADES) + " cupcakes, fale direto com a loja."

    # tema e observações são opcionais
    if len(tema) > 100:
        erros["tema"] = "O tema pode ter no máximo 100 letras."
    if len(observacoes) > 500:
        erros["observacoes"] = "As observações podem ter no máximo 500 letras."

    return erros


# função que escreve o e-mail que vai pra loja (devolve o assunto e o texto)
# campos: nome, email, celular, data_evento (data de verdade), quantidade, tema e observacoes (podem ser None)
def montar_email_para_a_loja(numero, campos):
    assunto = "Novo pedido de orçamento #" + str(numero) + " - " + str(campos["quantidade"]) + " cupcakes"
    texto = "Chegou um pedido de orçamento de evento.\n\n"
    texto = texto + "Protocolo: #" + str(numero) + "\n"
    texto = texto + "Nome: " + campos["nome"] + "\n"
    texto = texto + "E-mail: " + campos["email"] + "\n"
    texto = texto + "Celular: " + campos["celular"] + "\n"
    texto = texto + "Data do evento: " + formatar_data(campos["data_evento"]) + "\n"
    texto = texto + "Quantidade: " + str(campos["quantidade"]) + " cupcakes\n"
    if campos["tema"] is not None:
        texto = texto + "Tema: " + campos["tema"] + "\n"
    if campos["observacoes"] is not None:
        texto = texto + "Observações: " + campos["observacoes"] + "\n"
    texto = texto + "\nResponda para o e-mail acima em até " + PRAZO_DE_RESPOSTA + "."
    return assunto, texto


# função que escreve o e-mail de confirmação que vai pra quem pediu (devolve o assunto e o texto)
def montar_email_para_o_cliente(numero, campos):
    assunto = "Recebemos o seu pedido de orçamento #" + str(numero)
    texto = "Olá, " + campos["nome"] + "!\n\n"
    texto = texto + "Recebemos o seu pedido de orçamento para " + str(campos["quantidade"])
    texto = texto + " cupcakes no dia " + formatar_data(campos["data_evento"]) + ".\n"
    texto = texto + "O seu protocolo é #" + str(numero) + ".\n\n"
    texto = texto + "Vamos responder neste e-mail em até " + PRAZO_DE_RESPOSTA + ", com os valores e os detalhes da encomenda."
    return assunto, texto