# regras do Meu perfil: dados da conta e endereços (cartão 20)

from models import validacoes

# quantos endereços cada cliente pode ter guardados
MAXIMO_DE_ENDERECOS = 5


# função que põe o traço no cep: "01001000" vira "01001-000"
def formatar_cep(cep):
    if len(cep) != 8:
        return cep
    return cep[0:5] + "-" + cep[5:8]


# função que põe parênteses e traço no celular: "11900001111" vira "(11) 90000-1111"
# (se o celular não tiver 10 ou 11 números, devolve como veio)
def formatar_celular(celular):
    numeros = validacoes.tirar_enfeites(celular)
    if validacoes.so_tem_numeros(numeros) == False:
        return celular
    if len(numeros) == 11:
        return "(" + numeros[0:2] + ") " + numeros[2:7] + "-" + numeros[7:11]
    if len(numeros) == 10:
        return "(" + numeros[0:2] + ") " + numeros[2:6] + "-" + numeros[6:10]
    return celular


# função que esconde parte do cpf na tela: "12345678909" vira "***.456.789-**"
def mascarar_cpf(cpf):
    if len(cpf) != 11:
        return cpf
    return "***." + cpf[3:6] + "." + cpf[6:9] + "-**"


# função que confere o formulário de endereço do perfil
# é a conferência do fechamento do pedido + o apelido e o complemento (que são opcionais)
# devolve um dicionário com os erros (vazio = tudo certo)
def conferir_endereco_do_perfil(apelido, cep, rua, numero, complemento, bairro, cidade, uf):
    erros = validacoes.conferir_endereco(cep, rua, numero, bairro, cidade, uf)

    if len(apelido) > 30:
        erros["apelido"] = "O apelido pode ter no máximo 30 letras."

    if len(complemento) > 60:
        erros["complemento"] = "O complemento pode ter no máximo 60 letras."

    return erros


# função que diz o nome do endereço na lista (o apelido, ou "Endereço" se não tem)
def nome_do_endereco(apelido):
    if apelido is None or apelido == "":
        return "Endereço"
    return apelido


# função que escreve o endereço em uma linha, ex: "Rua A, 10 - apto 2 - Centro, São Paulo/SP - CEP 01001-000"
def resumir_endereco(rua, numero, complemento, bairro, cidade, uf, cep):
    texto = rua + ", " + numero
    if complemento is not None and complemento != "":
        texto = texto + " - " + complemento
    texto = texto + " - " + bairro + ", " + cidade + "/" + uf
    texto = texto + " - CEP " + formatar_cep(cep)
    return texto


# função que diz por que um endereço NÃO pode ser excluído (ou "" se pode)
# regra: o principal só sai quando é o único (senão o checkout ficaria sem saber qual usar)
def motivo_para_nao_excluir(eh_principal, total_de_enderecos):
    if eh_principal == True and total_de_enderecos > 1:
        return "O endereço principal não pode ser excluído. Marque outro endereço como principal primeiro."
    return ""