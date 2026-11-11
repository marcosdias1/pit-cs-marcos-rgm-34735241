from decimal import Decimal
from models.produto_model import tirar_acentos

# regras do frete (cartão 10) + tabelar frete por região (frete dinâmico)


# onde fica a loja
LOJA_BAIRRO = "Centro"
LOJA_CIDADE = "São Paulo"
LOJA_UF = "SP"


# função que compara dois textos sem ligar pra acento, maiúscula nem espaço sobrando
def textos_iguais(texto1, texto2):
    if tirar_acentos(texto1).strip() == tirar_acentos(texto2).strip():
        return True
    else:
        return False


# função que calcula o frete pelo endereço de entrega
# devolve um dicionário (valor, minutos e região) ou None se a gente não entrega lá
def calcular_frete(bairro, cidade, uf):
    # outro estado: não entrega
    if uf.strip().upper() != LOJA_UF:
        return None

    frete = {}
    if textos_iguais(cidade, LOJA_CIDADE) == False:
        # mesmo estado, mas outra cidade
        frete["valor"] = Decimal("15.00")
        frete["minutos"] = 70
        frete["regiao"] = "Outra cidade do mesmo estado"
    elif textos_iguais(bairro, LOJA_BAIRRO) == True:
        # mesmo bairro da loja
        frete["valor"] = Decimal("5.00")
        frete["minutos"] = 30
        frete["regiao"] = "Mesmo bairro da loja"
    else:
        # mesma cidade, outro bairro
        frete["valor"] = Decimal("7.50")
        frete["minutos"] = 40
        frete["regiao"] = "Mesma cidade da loja"

    return frete