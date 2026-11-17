# Loja de cupcakes

Projeto Integrador de Engenharia de Software II (PIT II), Cruzeiro do Sul.

Autor: Marcos Alexandre Dias dos Santos, RGM 34735241.

É um site de uma loja de cupcakes. A pessoa escolhe os cupcakes, paga e acompanha a entrega até chegar. O pagamento, os e-mails e o aviso de saída para entrega são simulados, porque o projeto é uma demonstração.

## Links

| O quê | Onde |
|---|---|
| Site, versão 2 (corrigida depois dos testes) | https://pit-cs-marcos-rgm-34735241-loja-cup.vercel.app |
| Site, versão 1 (a que os colegas testaram) | https://pit-cs-marcos-rgm-34735241-loja-cup-tau.vercel.app |
| Vídeo narrado (Situação 2) | https://youtu.be/pv5hYaWBNS0 |
| Vídeo das modificações (Situação 3) | https://youtu.be/kKZhi4V-31I |
| Manual de uso | [Manual_de_uso.docx](Manual%20de%20uso/Manual_de_uso.docx) |
| Laudo de qualidade e melhorias | [Melhorias_solicitadas_e_decisoes.docx](%2303%20-%20Situa%C3%A7%C3%A3o%20Problema%203%20-%20realiza%C3%A7%C3%A3o%20de%20testes%20feitos%20pelos%20clientes/%2301%20-%20Testes%20com%205%20pessoas%20%2B%20Coleta%20de%20sugest%C3%B5es/Melhorias_solicitadas_e_decisoes.docx) |

As duas versões do site usam o mesmo banco de dados. Um pedido feito numa aparece na outra, e o estoque é um só.

## O que o site faz

- Vitrine com filtro por categoria e busca por nome ou ingrediente (a busca ignora acentos).
- Detalhe do cupcake, com ingredientes, alérgenos e preço.
- Carrinho para visitante e para cliente, com sugestão de adicionais.
- Fechamento do pedido com endereço preenchido pelo CEP (ViaCEP), frete por região e cupom de desconto.
- Pagamento simulado por PIX ou cartão de crédito.
- Acompanhamento do pedido: o status muda sozinho na tela. O visitante acompanha pelo número do pedido e pelo e-mail.
- Cancelamento do pedido, enquanto ele ainda não saiu para entrega.
- Conta de cliente: criar conta, entrar, esqueci minha senha, Meus pedidos (com "Comprar de novo"), Meu perfil e até 5 endereços.
- Orçamento para eventos (a partir de 30 cupcakes), com as encomendas listadas em "Meus pedidos".
- Funciona no computador e no celular. No celular, os atalhos ficam numa barra embaixo da tela.

O passo a passo de cada tela está no [Manual de uso](Manual%20de%20uso/Manual_de_uso.docx).

## Tecnologias

| Parte | O que usei |
|---|---|
| Back-end | Python 3.13 e Flask 3.1, no padrão MVC |
| Front-end | HTML, CSS e JavaScript puro, sem framework |
| Banco de dados | PostgreSQL (o script pede a versão 14 ou superior) |
| Testes | pytest e pytest-cov |
| Publicação | Vercel (o site) e Neon (o banco), com deploy automático a cada push no GitHub |

## Como o repositório está organizado

```
Manual de uso/                    o manual de uso do site, com prints (Manual_de_uso.docx)
#01 - Situação Problema 1 - ...   documentação revisada do PIT I (backlog, UML, banco de dados, telas)
#02 - Situação Problema 2 -       o sistema
    cupcakes/
        app.py                    liga as partes e registra as rotas
        config.py                 lê as variáveis de ambiente
        controllers/              as rotas (o C do MVC)
        models/                   as regras e o acesso ao banco (o M)
        templates/                as telas em HTML (o V)
        public/static/            CSS e JavaScript
        tests/                    os testes automáticos
#03 - Situação Problema 3 - ...   testes com os colegas, laudo de qualidade e roteiros dos vídeos
```

Dentro de `models/`, os arquivos que terminam em `_regras.py` só têm regra e texto, sem banco. Foi isso que deixou o código possível de testar sem o PostgreSQL.

## Como rodar na sua máquina

Precisa de Python 3.13 e de um PostgreSQL 14 ou superior. Os comandos abaixo são para o PowerShell do Windows.

**1. Criar o banco.** Os scripts estão em [banco_de_dados_sql](%2301%20-%20Situa%C3%A7%C3%A3o%20Problema%201%20-%20revis%C3%A3o%20dos%20arquivos%20do%20PIT%20I/%2302%20-%20Novos%20documentos%20criados/Banco%20de%20Dados/banco_de_dados_sql). Dentro dessa pasta, rode:

```powershell
psql -U postgres -c "CREATE DATABASE cupcakes ENCODING 'UTF8';"
psql -U postgres -d cupcakes -f banco_cupcakes_schema.sql
psql -U postgres -d cupcakes -f banco_cupcakes_dados_exemplo.sql
```

O primeiro script cria as 23 tabelas. O segundo é opcional e carrega dados de exemplo: cupcakes, preços, clientes e alguns pedidos. Os clientes de exemplo têm senha de mentira e não conseguem entrar: crie a sua conta pelo site.

**2. Preparar o Python.** Na pasta `#02 - Situação Problema 2 -/cupcakes`:

```powershell
py -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configurar o `.env`.** Copie o `.env.exemplo` para `.env` e preencha. O `.env` nunca vai para o GitHub.

```powershell
copy .env.exemplo .env
python -c "import secrets; print(secrets.token_hex(32))"
```

Cole o resultado do segundo comando em `CHAVE_SECRETA` e coloque a senha do seu PostgreSQL em `DB_SENHA`. Com `MOSTRAR_LINK_DE_SENHA_NA_TELA=sim`, o link do "esqueci minha senha" aparece na tela (útil para demonstração). Com `nao`, ele aparece só no terminal.

**4. Rodar.**

```powershell
python app.py
```

Abra http://127.0.0.1:5000 no navegador.

## Dados de teste

- **Conta de teste:** o CPF e a senha estão no arquivo [`conta_de_teste.txt`](%2302%20-%20Situa%C3%A7%C3%A3o%20Problema%202%20-/cupcakes/conta_de_teste.txt). Se essa conta não existir no banco que você está usando (por exemplo, num banco local novo), crie uma conta pelo site.
- **Cartão que aprova:** 4111 1111 1111 1111.
- **Cartão que recusa:** 4000 0000 0000 0002.
- Nos dois, vale qualquer nome, uma validade futura (por exemplo 12/35) e um CVV de 3 números. No PIX, basta clicar em "Confirmar pagamento".
- **CEP que entrega:** 01001-000 (a loja fica em São Paulo, SP). Um CEP de outro estado mostra o aviso de que não entrega.

## Testes automáticos

Na pasta `cupcakes`, com o ambiente virtual ligado:

```powershell
pytest
pytest --cov=models --cov=controllers
```

São 655 testes, e todos passam. Eles rodam em poucos segundos e não precisam de banco: os testes trocam o banco por funções de mentira. O `tests/conftest.py` define uma chave secreta de teste, então o pytest também roda sem o arquivo `.env`.

A cobertura das regras e dos controllers fica perto de 100%. A cobertura total é de uns 66%, porque os arquivos que escrevem SQL (os que terminam em `_model.py`) só rodam de verdade com o PostgreSQL.

## Versões

| Versão | Onde está no Git |
|---|---|
| Versão 1, a que os colegas testaram | commit `8e96a0f`, marcado com a tag `v1-testes` e com a branch `v1` |
| Versão 2, com as correções | branch `main` |

Para ver tudo o que mudou: https://github.com/marcosdias1/pit-cs-marcos-rgm-34735241/compare/v1-testes...main

As mudanças da versão 2 saíram dos testes com 5 colegas. O laudo de qualidade lista os 18 pedidos que eles fizeram, o que foi implementado, o que ficou de fora e como cada correção foi conferida.

## O que é simulado e o que ficou de fora

- **Pagamento:** não existe operadora de verdade. O PIX é um QR code de mentira, e os cartões de teste aprovam ou recusam por número.
- **E-mails:** são simulados e aparecem no terminal onde o Flask está rodando. O mesmo vale para o aviso de "saiu para entrega": nenhuma mensagem é enviada.
- **Status do pedido:** como o projeto não tem funcionário nem entregador, o próprio sistema avança o pedido com o tempo (30, 90 e 150 segundos depois de confirmado). Esses tempos são curtos só para a demonstração.
- **Não foram feitos:** painel do funcionário e do entregador, cartões salvos e algumas proteções de segurança (token contra CSRF e limite de tentativas de login).
- **Segurança que existe:** senha guardada com hash, consultas ao banco sempre com parâmetros, chaves em variáveis de ambiente e cada pessoa só vê os próprios pedidos.
