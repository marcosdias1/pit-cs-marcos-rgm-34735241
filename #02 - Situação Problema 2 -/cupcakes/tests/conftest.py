# o pytest lê este arquivo ANTES de rodar os testes
# aqui eu faço os testes funcionarem mesmo sem o arquivo .env 

import os

# os testes precisam de uma chave secreta pra o Flask guardar a sessão (o login, o carrinho...)
# o setdefault só coloca esta chave se ainda não existir uma
# ou seja: se o .env existir, a chave de verdade dele continua valendo
os.environ.setdefault("CHAVE_SECRETA", "chave-so-para-os-testes-nao-use-no-site-de-verdade")
