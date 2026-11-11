-- =====================================================================
--  Banco de dados do aplicativo da confeitaria de cupcakes
--  Projeto físico para PostgreSQL 14 ou superior
--  Autor: Marcos Alexandre Dias dos Santos (RGM 34735241)
--
--  Como usar (num banco novo e vazio):
--    CREATE DATABASE cupcakes ENCODING 'UTF8';
--    \c cupcakes
--    \i banco_cupcakes_schema.sql
--
--  Convenções: nomes em minúsculas, sem acento, com sublinhado.
--  Chave primária: id_<tabela>. Chave estrangeira: mesmo nome da chave
--  que ela referencia. Dinheiro: NUMERIC(10,2).
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. PESSOAS E ACESSO
--    Pessoa é a classe abstrata; Cliente, Funcionário e Entregador herdam
--    dela (uma tabela por subclasse, com a mesma chave da pessoa).
-- ---------------------------------------------------------------------
CREATE TABLE pessoa (
    id_pessoa   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    email       VARCHAR(120) NOT NULL,
    celular     VARCHAR(15)  NOT NULL,
    CONSTRAINT uq_pessoa_email  UNIQUE (email),
    CONSTRAINT ck_pessoa_email  CHECK (email LIKE '%_@_%._%'),
    CONSTRAINT ck_pessoa_celular CHECK (celular ~ '^[0-9()+ -]{10,15}$')
);

CREATE TABLE cliente (
    id_cliente     INTEGER PRIMARY KEY,
    cpf            CHAR(11)     NOT NULL,
    senha_hash     VARCHAR(255) NOT NULL,
    data_cadastro  DATE         NOT NULL DEFAULT CURRENT_DATE,
    ativo          BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_cliente_pessoa FOREIGN KEY (id_cliente)
        REFERENCES pessoa (id_pessoa) ON DELETE CASCADE,
    CONSTRAINT uq_cliente_cpf UNIQUE (cpf),
    CONSTRAINT ck_cliente_cpf CHECK (cpf ~ '^[0-9]{11}$')
);

CREATE TABLE funcionario (
    id_funcionario INTEGER PRIMARY KEY,
    perfil         VARCHAR(15)  NOT NULL DEFAULT 'ATENDENTE',
    senha_hash     VARCHAR(255) NOT NULL,
    ativo          BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_funcionario_pessoa FOREIGN KEY (id_funcionario)
        REFERENCES pessoa (id_pessoa) ON DELETE CASCADE,
    CONSTRAINT ck_funcionario_perfil CHECK (perfil IN ('ATENDENTE', 'ADMINISTRADOR'))
);

CREATE TABLE entregador (
    id_entregador INTEGER PRIMARY KEY,
    placa         VARCHAR(8) NOT NULL,
    ativo         BOOLEAN    NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_entregador_pessoa FOREIGN KEY (id_entregador)
        REFERENCES pessoa (id_pessoa) ON DELETE CASCADE
);

CREATE TABLE endereco (
    id_endereco  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente   INTEGER,
    apelido      VARCHAR(30),
    cep          CHAR(8)      NOT NULL,
    rua          VARCHAR(120) NOT NULL,
    numero       VARCHAR(10)  NOT NULL,
    complemento  VARCHAR(60),
    bairro       VARCHAR(60)  NOT NULL,
    cidade       VARCHAR(60)  NOT NULL,
    uf           CHAR(2)      NOT NULL,
    principal    BOOLEAN      NOT NULL DEFAULT FALSE,
    ativo        BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_endereco_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente) ON DELETE CASCADE,
    CONSTRAINT ck_endereco_cep CHECK (cep ~ '^[0-9]{8}$'),
    CONSTRAINT ck_endereco_uf  CHECK (uf ~ '^[A-Z]{2}$'),
    CONSTRAINT ck_endereco_principal CHECK (NOT principal OR id_cliente IS NOT NULL)
);
-- cada cliente tem no máximo um endereço principal ativo
CREATE UNIQUE INDEX ux_endereco_principal ON endereco (id_cliente)
    WHERE principal AND ativo;

CREATE TABLE cartao_salvo (
    id_cartao_salvo  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente       INTEGER      NOT NULL,
    bandeira         VARCHAR(20)  NOT NULL,
    ultimos_digitos  CHAR(4)      NOT NULL,
    validade_mes     SMALLINT     NOT NULL,
    validade_ano     SMALLINT     NOT NULL,
    token_operadora  VARCHAR(100) NOT NULL,
    CONSTRAINT fk_cartao_salvo_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente) ON DELETE CASCADE,
    CONSTRAINT uq_cartao_salvo_token UNIQUE (token_operadora),
    CONSTRAINT ck_cartao_salvo_digitos CHECK (ultimos_digitos ~ '^[0-9]{4}$'),
    CONSTRAINT ck_cartao_salvo_mes CHECK (validade_mes BETWEEN 1 AND 12),
    CONSTRAINT ck_cartao_salvo_ano CHECK (validade_ano BETWEEN 2000 AND 2100)
);

CREATE TABLE token_recuperacao_senha (
    id_token    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente  INTEGER   NOT NULL,
    token_hash  CHAR(64)  NOT NULL,
    criado_em   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expira_em   TIMESTAMP NOT NULL,
    usado       BOOLEAN   NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_token_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente) ON DELETE CASCADE,
    CONSTRAINT uq_token_hash UNIQUE (token_hash),
    CONSTRAINT ck_token_validade CHECK (expira_em > criado_em)
);

-- ---------------------------------------------------------------------
-- 2. CATÁLOGO
--    Produto é a classe abstrata; Cupcake e Adicional herdam dela.
-- ---------------------------------------------------------------------
CREATE TABLE categoria (
    id_categoria  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome          VARCHAR(40) NOT NULL,
    CONSTRAINT uq_categoria_nome UNIQUE (nome)
);

CREATE TABLE produto (
    id_produto  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo        VARCHAR(10) NOT NULL,
    nome        VARCHAR(80) NOT NULL,
    imagem_url  VARCHAR(255),
    estoque     INTEGER     NOT NULL DEFAULT 0,
    ativo       BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_produto_tipo    CHECK (tipo IN ('CUPCAKE', 'ADICIONAL')),
    CONSTRAINT ck_produto_estoque CHECK (estoque >= 0)
);

CREATE TABLE cupcake (
    id_cupcake     INTEGER PRIMARY KEY,
    descricao      TEXT         NOT NULL,
    ingredientes   TEXT         NOT NULL,
    alergenos      VARCHAR(150),
    contem_acucar  BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_cupcake_produto FOREIGN KEY (id_cupcake)
        REFERENCES produto (id_produto) ON DELETE CASCADE
);

CREATE TABLE adicional (
    id_adicional    INTEGER PRIMARY KEY,
    tipo_adicional  VARCHAR(10) NOT NULL,
    CONSTRAINT fk_adicional_produto FOREIGN KEY (id_adicional)
        REFERENCES produto (id_produto) ON DELETE CASCADE,
    CONSTRAINT ck_adicional_tipo CHECK (tipo_adicional IN ('EMBALAGEM', 'CHOCOLATE', 'BALA'))
);

-- relação muitos-para-muitos entre cupcake e categoria
CREATE TABLE cupcake_categoria (
    id_cupcake    INTEGER NOT NULL,
    id_categoria  INTEGER NOT NULL,
    PRIMARY KEY (id_cupcake, id_categoria),
    CONSTRAINT fk_cupcake_categoria_cupcake FOREIGN KEY (id_cupcake)
        REFERENCES cupcake (id_cupcake) ON DELETE CASCADE,
    CONSTRAINT fk_cupcake_categoria_categoria FOREIGN KEY (id_categoria)
        REFERENCES categoria (id_categoria) ON DELETE CASCADE
);

CREATE TABLE tabela_preco (
    id_tabela_preco  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome             VARCHAR(40) NOT NULL,
    ativa            BOOLEAN     NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_tabela_preco_nome UNIQUE (nome)
);
-- só uma tabela de preço pode estar ativa por vez
CREATE UNIQUE INDEX ux_tabela_preco_ativa ON tabela_preco ((TRUE)) WHERE ativa;

CREATE TABLE preco_produto (
    id_produto       INTEGER       NOT NULL,
    id_tabela_preco  INTEGER       NOT NULL,
    valor            NUMERIC(10,2) NOT NULL,
    PRIMARY KEY (id_produto, id_tabela_preco),
    CONSTRAINT fk_preco_produto_produto FOREIGN KEY (id_produto)
        REFERENCES produto (id_produto) ON DELETE CASCADE,
    CONSTRAINT fk_preco_produto_tabela FOREIGN KEY (id_tabela_preco)
        REFERENCES tabela_preco (id_tabela_preco) ON DELETE CASCADE,
    CONSTRAINT ck_preco_produto_valor CHECK (valor >= 0)
);

-- ---------------------------------------------------------------------
-- 3. CARRINHO, CUPOM E PEDIDO
-- ---------------------------------------------------------------------
CREATE TABLE carrinho (
    id_carrinho    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente     INTEGER,
    id_sessao      VARCHAR(64),
    atualizado_em  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_carrinho_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente) ON DELETE CASCADE,
    CONSTRAINT uq_carrinho_cliente UNIQUE (id_cliente),
    CONSTRAINT uq_carrinho_sessao  UNIQUE (id_sessao),
    CONSTRAINT ck_carrinho_dono CHECK (id_cliente IS NOT NULL OR id_sessao IS NOT NULL)
);

CREATE TABLE item_carrinho (
    id_item_carrinho  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_carrinho       INTEGER NOT NULL,
    id_produto        INTEGER NOT NULL,
    quantidade        INTEGER NOT NULL,
    CONSTRAINT fk_item_carrinho_carrinho FOREIGN KEY (id_carrinho)
        REFERENCES carrinho (id_carrinho) ON DELETE CASCADE,
    CONSTRAINT fk_item_carrinho_produto FOREIGN KEY (id_produto)
        REFERENCES produto (id_produto),
    CONSTRAINT uq_item_carrinho UNIQUE (id_carrinho, id_produto),
    CONSTRAINT ck_item_carrinho_qtd CHECK (quantidade > 0)
);

CREATE TABLE cupom (
    id_cupom         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente       INTEGER,
    codigo           VARCHAR(30)   NOT NULL,
    tipo             VARCHAR(12)   NOT NULL,
    valor            NUMERIC(10,2) NOT NULL,
    valido_de        DATE          NOT NULL,
    valido_ate       DATE          NOT NULL,
    uso_unico        BOOLEAN       NOT NULL DEFAULT FALSE,
    primeira_compra  BOOLEAN       NOT NULL DEFAULT FALSE,
    ativo            BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_cupom_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente) ON DELETE CASCADE,
    CONSTRAINT uq_cupom_codigo UNIQUE (codigo),
    CONSTRAINT ck_cupom_tipo   CHECK (tipo IN ('VALOR_FIXO', 'PERCENTUAL')),
    CONSTRAINT ck_cupom_valor  CHECK (valor > 0 AND (tipo <> 'PERCENTUAL' OR valor <= 100)),
    CONSTRAINT ck_cupom_prazo  CHECK (valido_ate >= valido_de)
);

CREATE TABLE pedido (
    id_pedido         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero            INTEGER GENERATED ALWAYS AS IDENTITY (START WITH 10001),
    id_cliente        INTEGER,
    id_endereco       INTEGER       NOT NULL,
    id_cupom          INTEGER,
    id_entregador     INTEGER,
    data_hora         TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status            VARCHAR(20)   NOT NULL DEFAULT 'AGUARDANDO_PAGAMENTO',
    subtotal          NUMERIC(10,2) NOT NULL,
    distancia_km      NUMERIC(6,2),
    valor_frete       NUMERIC(10,2) NOT NULL DEFAULT 0,
    desconto          NUMERIC(10,2) NOT NULL DEFAULT 0,
    total             NUMERIC(10,2) NOT NULL,
    previsao_entrega  TIMESTAMP,
    nome_contato      VARCHAR(100),
    email_contato     VARCHAR(120),
    telefone_contato  VARCHAR(15),
    CONSTRAINT fk_pedido_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente),
    CONSTRAINT fk_pedido_endereco FOREIGN KEY (id_endereco)
        REFERENCES endereco (id_endereco),
    CONSTRAINT fk_pedido_cupom FOREIGN KEY (id_cupom)
        REFERENCES cupom (id_cupom),
    CONSTRAINT fk_pedido_entregador FOREIGN KEY (id_entregador)
        REFERENCES entregador (id_entregador),
    CONSTRAINT uq_pedido_numero UNIQUE (numero),
    CONSTRAINT ck_pedido_status CHECK (status IN ('AGUARDANDO_PAGAMENTO', 'CONFIRMADO',
        'EM_PREPARO', 'SAIU_PARA_ENTREGA', 'ENTREGUE', 'CANCELADO')),
    CONSTRAINT ck_pedido_valores CHECK (subtotal >= 0 AND valor_frete >= 0
        AND desconto >= 0 AND total >= 0 AND (distancia_km IS NULL OR distancia_km >= 0)),
    CONSTRAINT ck_pedido_total CHECK (total = subtotal + valor_frete - desconto),
    CONSTRAINT ck_pedido_contato CHECK (id_cliente IS NOT NULL OR email_contato IS NOT NULL),
    CONSTRAINT ck_pedido_entregador CHECK (
        status NOT IN ('SAIU_PARA_ENTREGA', 'ENTREGUE') OR id_entregador IS NOT NULL)
);

CREATE TABLE item_pedido (
    id_item_pedido  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pedido       INTEGER       NOT NULL,
    id_produto      INTEGER       NOT NULL,
    quantidade      INTEGER       NOT NULL,
    preco_unitario  NUMERIC(10,2) NOT NULL,
    CONSTRAINT fk_item_pedido_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedido (id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_item_pedido_produto FOREIGN KEY (id_produto)
        REFERENCES produto (id_produto),
    CONSTRAINT uq_item_pedido UNIQUE (id_pedido, id_produto),
    CONSTRAINT ck_item_pedido_qtd   CHECK (quantidade > 0),
    CONSTRAINT ck_item_pedido_preco CHECK (preco_unitario >= 0)
);

-- ---------------------------------------------------------------------
-- 4. PAGAMENTO, ENTREGA E QUALIDADE
-- ---------------------------------------------------------------------
CREATE TABLE pagamento (
    id_pagamento       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pedido          INTEGER       NOT NULL,
    forma              VARCHAR(15)   NOT NULL,
    valor              NUMERIC(10,2) NOT NULL,
    status             VARCHAR(10)   NOT NULL DEFAULT 'PENDENTE',
    codigo_transacao   VARCHAR(60),
    data_hora          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_pagamento_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedido (id_pedido),
    CONSTRAINT uq_pagamento_transacao UNIQUE (codigo_transacao),
    CONSTRAINT ck_pagamento_forma  CHECK (forma IN ('CARTAO_CREDITO', 'PIX')),
    CONSTRAINT ck_pagamento_status CHECK (status IN ('PENDENTE', 'APROVADO', 'RECUSADO')),
    CONSTRAINT ck_pagamento_valor  CHECK (valor > 0)
);

CREATE TABLE historico_status (
    id_historico_status  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pedido            INTEGER     NOT NULL,
    id_pessoa            INTEGER,
    status               VARCHAR(20) NOT NULL,
    data_hora            TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historico_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedido (id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_historico_pessoa FOREIGN KEY (id_pessoa)
        REFERENCES pessoa (id_pessoa) ON DELETE SET NULL,
    CONSTRAINT ck_historico_status CHECK (status IN ('AGUARDANDO_PAGAMENTO', 'CONFIRMADO',
        'EM_PREPARO', 'SAIU_PARA_ENTREGA', 'ENTREGUE', 'CANCELADO'))
);

CREATE TABLE checklist_embalagem (
    id_checklist    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_pedido       INTEGER      NOT NULL,
    id_funcionario  INTEGER      NOT NULL,
    aprovado        BOOLEAN      NOT NULL,
    observacao      VARCHAR(255),
    data_hora       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_checklist_pedido FOREIGN KEY (id_pedido)
        REFERENCES pedido (id_pedido) ON DELETE CASCADE,
    CONSTRAINT fk_checklist_funcionario FOREIGN KEY (id_funcionario)
        REFERENCES funcionario (id_funcionario),
    CONSTRAINT uq_checklist_pedido UNIQUE (id_pedido)
);

CREATE TABLE solicitacao_evento (
    id_solicitacao_evento  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_cliente             INTEGER,
    nome_contato           VARCHAR(100) NOT NULL,
    email_contato          VARCHAR(120) NOT NULL,
    telefone_contato       VARCHAR(15)  NOT NULL,
    data_evento            DATE         NOT NULL,
    quantidade             INTEGER      NOT NULL,
    tema                   VARCHAR(100),
    observacoes            VARCHAR(500),
    data_solicitacao       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status                 VARCHAR(10)  NOT NULL DEFAULT 'RECEBIDA',
    CONSTRAINT fk_solicitacao_cliente FOREIGN KEY (id_cliente)
        REFERENCES cliente (id_cliente) ON DELETE SET NULL,
    CONSTRAINT ck_solicitacao_qtd    CHECK (quantidade >= 30),
    CONSTRAINT ck_solicitacao_status CHECK (status IN ('RECEBIDA', 'ORCADA', 'CANCELADA'))
);

-- ---------------------------------------------------------------------
-- 5. ÍNDICES PARA AS CONSULTAS MAIS COMUNS
--    (o PostgreSQL já cria índice para chaves primárias e para UNIQUE)
-- ---------------------------------------------------------------------
CREATE INDEX ix_endereco_cliente          ON endereco (id_cliente);
CREATE INDEX ix_cartao_salvo_cliente      ON cartao_salvo (id_cliente);
CREATE INDEX ix_token_cliente             ON token_recuperacao_senha (id_cliente);
CREATE INDEX ix_produto_tipo_ativo        ON produto (tipo, ativo);
CREATE INDEX ix_cupcake_categoria_categ   ON cupcake_categoria (id_categoria);
CREATE INDEX ix_item_carrinho_produto     ON item_carrinho (id_produto);
CREATE INDEX ix_cupom_cliente             ON cupom (id_cliente);
CREATE INDEX ix_pedido_cliente            ON pedido (id_cliente);
CREATE INDEX ix_pedido_status             ON pedido (status);
CREATE INDEX ix_pedido_data_hora          ON pedido (data_hora);
CREATE INDEX ix_item_pedido_produto       ON item_pedido (id_produto);
CREATE INDEX ix_pagamento_pedido          ON pagamento (id_pedido);
CREATE INDEX ix_historico_pedido          ON historico_status (id_pedido);

-- ---------------------------------------------------------------------
-- 6. DESCRIÇÕES (alimentam o dicionário de dados)
--    Para ver no psql:  \d+ pedido   ou   SELECT obj_description('pedido'::regclass);
-- ---------------------------------------------------------------------
COMMENT ON TABLE adicional IS 'Detalhes dos produtos que acompanham o pedido: embalagem especial, chocolate ou balas (ID 06).';
COMMENT ON COLUMN adicional.id_adicional IS 'Identificador do adicional. É o mesmo número do produto (herança).';
COMMENT ON COLUMN adicional.tipo_adicional IS 'Tipo do adicional: EMBALAGEM, CHOCOLATE ou BALA.';

COMMENT ON TABLE carrinho IS 'Carrinho de compras. Pertence a um cliente ou a uma sessão de visitante. Os itens ficam salvos se o app for fechado (ID 05).';
COMMENT ON COLUMN carrinho.id_carrinho IS 'Identificador do carrinho.';
COMMENT ON COLUMN carrinho.id_cliente IS 'Cliente dono do carrinho. Vazio para visitante. Cada cliente tem no máximo um carrinho.';
COMMENT ON COLUMN carrinho.id_sessao IS 'Código da sessão do visitante. Preenchido quando não há cliente.';
COMMENT ON COLUMN carrinho.atualizado_em IS 'Última vez que o carrinho foi alterado.';

COMMENT ON TABLE cartao_salvo IS 'Cartão que o cliente guardou para comprar mais rápido (ID 20). Nunca guarda o número completo nem o CVV.';
COMMENT ON COLUMN cartao_salvo.id_cartao_salvo IS 'Identificador do cartão salvo.';
COMMENT ON COLUMN cartao_salvo.id_cliente IS 'Cliente dono do cartão.';
COMMENT ON COLUMN cartao_salvo.bandeira IS 'Bandeira do cartão, por exemplo Visa ou Mastercard.';
COMMENT ON COLUMN cartao_salvo.ultimos_digitos IS 'Últimos 4 dígitos, só para o cliente reconhecer o cartão.';
COMMENT ON COLUMN cartao_salvo.validade_mes IS 'Mês de validade (1 a 12).';
COMMENT ON COLUMN cartao_salvo.validade_ano IS 'Ano de validade com 4 dígitos.';
COMMENT ON COLUMN cartao_salvo.token_operadora IS 'Código que a operadora de pagamento devolve no lugar do número do cartão. É ele que permite cobrar de novo.';

COMMENT ON TABLE categoria IS 'Agrupamento de cupcakes para o filtro da vitrine, como Diet, Salgado, Tempo limitado ou Promoção (ID 02).';
COMMENT ON COLUMN categoria.id_categoria IS 'Identificador da categoria.';
COMMENT ON COLUMN categoria.nome IS 'Nome da categoria, único.';

COMMENT ON TABLE checklist_embalagem IS 'Conferência de embalagem e qualidade feita antes de o pedido sair para entrega. Guarda quem aprovou, para auditoria (ID 13).';
COMMENT ON COLUMN checklist_embalagem.id_checklist IS 'Identificador do checklist.';
COMMENT ON COLUMN checklist_embalagem.id_pedido IS 'Pedido conferido. Cada pedido tem um único checklist.';
COMMENT ON COLUMN checklist_embalagem.id_funcionario IS 'Funcionário que preencheu e aprovou.';
COMMENT ON COLUMN checklist_embalagem.aprovado IS 'Verdadeiro se tudo estava de acordo. Só então o botão de liberar a entrega fica ativo.';
COMMENT ON COLUMN checklist_embalagem.observacao IS 'Observação livre do funcionário.';
COMMENT ON COLUMN checklist_embalagem.data_hora IS 'Momento do preenchimento.';

COMMENT ON TABLE cliente IS 'Pessoa que criou uma conta para comprar com desconto (cartões ID 16, 17, 19 e 20).';
COMMENT ON COLUMN cliente.id_cliente IS 'Identificador do cliente. É o mesmo número da pessoa (herança).';
COMMENT ON COLUMN cliente.cpf IS 'CPF só com os 11 dígitos, sem pontos. Usado no login e único por conta. A validação dos dígitos verificadores é feita pela aplicação.';
COMMENT ON COLUMN cliente.senha_hash IS 'Senha criptografada (hash). A senha em texto puro nunca é gravada.';
COMMENT ON COLUMN cliente.data_cadastro IS 'Data em que a conta foi criada.';
COMMENT ON COLUMN cliente.ativo IS 'Verdadeiro se a conta está ativa. Conta inativa não consegue entrar.';

COMMENT ON TABLE cupcake IS 'Detalhes específicos dos produtos do tipo cupcake (IDs 01 a 04).';
COMMENT ON COLUMN cupcake.id_cupcake IS 'Identificador do cupcake. É o mesmo número do produto (herança).';
COMMENT ON COLUMN cupcake.descricao IS 'Descrição longa exibida na tela de detalhes.';
COMMENT ON COLUMN cupcake.ingredientes IS 'Lista de ingredientes. Ajuda quem tem alergia (ID 03).';
COMMENT ON COLUMN cupcake.alergenos IS 'Aviso de alérgenos, por exemplo "leite, ovo e glúten".';
COMMENT ON COLUMN cupcake.contem_acucar IS 'Falso para os cupcakes diet. O filtro "diet" esconde os que contêm açúcar comum (ID 02).';

COMMENT ON TABLE cupcake_categoria IS 'Liga cada cupcake às categorias em que ele aparece (relação muitos para muitos).';
COMMENT ON COLUMN cupcake_categoria.id_cupcake IS 'Cupcake que pertence à categoria.';
COMMENT ON COLUMN cupcake_categoria.id_categoria IS 'Categoria do cupcake.';

COMMENT ON TABLE cupom IS 'Código de desconto: campanha de marketing, cupom pessoal ou cupom de boas-vindas de R$ 15 (IDs 09 e 17).';
COMMENT ON COLUMN cupom.id_cupom IS 'Identificador do cupom.';
COMMENT ON COLUMN cupom.id_cliente IS 'Cliente dono do cupom, quando ele é pessoal (desconto atrelado ao CPF). Vazio para cupom de campanha.';
COMMENT ON COLUMN cupom.codigo IS 'Texto que o cliente digita, único.';
COMMENT ON COLUMN cupom.tipo IS 'VALOR_FIXO (desconta reais) ou PERCENTUAL (desconta uma porcentagem).';
COMMENT ON COLUMN cupom.valor IS 'Valor do desconto: reais, no tipo VALOR_FIXO, ou porcentagem de 0 a 100, no tipo PERCENTUAL.';
COMMENT ON COLUMN cupom.valido_de IS 'Primeiro dia em que o cupom vale.';
COMMENT ON COLUMN cupom.valido_ate IS 'Último dia em que o cupom vale.';
COMMENT ON COLUMN cupom.uso_unico IS 'Verdadeiro se o cupom só pode ser usado uma vez. A conferência de uso é feita pela aplicação.';
COMMENT ON COLUMN cupom.primeira_compra IS 'Verdadeiro se o cupom só vale na primeira compra do cliente.';
COMMENT ON COLUMN cupom.ativo IS 'Falso para desligar o cupom antes do fim da validade.';

COMMENT ON TABLE endereco IS 'Endereço de entrega. Pertence a um cliente ou, no caso de visitante, fica só no pedido (IDs 10, 18 e 20).';
COMMENT ON COLUMN endereco.id_endereco IS 'Identificador do endereço.';
COMMENT ON COLUMN endereco.id_cliente IS 'Cliente dono do endereço. Vazio quando o endereço é de um visitante.';
COMMENT ON COLUMN endereco.apelido IS 'Nome dado pelo cliente, por exemplo Casa ou Trabalho.';
COMMENT ON COLUMN endereco.cep IS 'CEP só com os 8 dígitos, sem hífen.';
COMMENT ON COLUMN endereco.rua IS 'Nome da rua ou avenida.';
COMMENT ON COLUMN endereco.numero IS 'Número do imóvel (texto, para aceitar "S/N" ou "12A").';
COMMENT ON COLUMN endereco.complemento IS 'Apartamento, bloco ou ponto de referência.';
COMMENT ON COLUMN endereco.bairro IS 'Bairro.';
COMMENT ON COLUMN endereco.cidade IS 'Cidade.';
COMMENT ON COLUMN endereco.uf IS 'Sigla do estado, em maiúsculas (por exemplo SP).';
COMMENT ON COLUMN endereco.principal IS 'Verdadeiro para o endereço principal, que já vem marcado no fechamento do pedido. Só um por cliente.';
COMMENT ON COLUMN endereco.ativo IS 'Falso quando o cliente "exclui" o endereço. A linha continua no banco para não alterar pedidos antigos.';

COMMENT ON TABLE entregador IS 'Pessoa que faz a entrega dos pedidos e confirma a entrega no aplicativo (ID 14).';
COMMENT ON COLUMN entregador.id_entregador IS 'Identificador do entregador. É o mesmo número da pessoa (herança).';
COMMENT ON COLUMN entregador.placa IS 'Placa do veículo usado nas entregas.';
COMMENT ON COLUMN entregador.ativo IS 'Verdadeiro se o entregador está ativo.';

COMMENT ON TABLE funcionario IS 'Pessoa que trabalha na loja e usa o módulo interno (checklist de embalagem, ID 13).';
COMMENT ON COLUMN funcionario.id_funcionario IS 'Identificador do funcionário. É o mesmo número da pessoa (herança).';
COMMENT ON COLUMN funcionario.perfil IS 'Papel no sistema: ATENDENTE ou ADMINISTRADOR.';
COMMENT ON COLUMN funcionario.senha_hash IS 'Senha criptografada (hash) do acesso interno.';
COMMENT ON COLUMN funcionario.ativo IS 'Verdadeiro se o funcionário está ativo.';

COMMENT ON TABLE historico_status IS 'Registro de cada mudança de status do pedido. Alimenta a tela de acompanhamento (ID 12).';
COMMENT ON COLUMN historico_status.id_historico_status IS 'Identificador do registro.';
COMMENT ON COLUMN historico_status.id_pedido IS 'Pedido que mudou de status.';
COMMENT ON COLUMN historico_status.id_pessoa IS 'Quem fez a mudança. Vazio quando foi o próprio sistema.';
COMMENT ON COLUMN historico_status.status IS 'Novo status do pedido.';
COMMENT ON COLUMN historico_status.data_hora IS 'Momento da mudança.';

COMMENT ON TABLE item_carrinho IS 'Cada produto colocado no carrinho, com a quantidade (IDs 05, 06 e 07).';
COMMENT ON COLUMN item_carrinho.id_item_carrinho IS 'Identificador do item do carrinho.';
COMMENT ON COLUMN item_carrinho.id_carrinho IS 'Carrinho a que o item pertence.';
COMMENT ON COLUMN item_carrinho.id_produto IS 'Produto escolhido.';
COMMENT ON COLUMN item_carrinho.quantidade IS 'Quantidade, maior que zero. Quando o cliente reduz a zero, a linha é apagada.';

COMMENT ON TABLE item_pedido IS 'Cada produto do pedido, com o preço da hora da compra.';
COMMENT ON COLUMN item_pedido.id_item_pedido IS 'Identificador do item do pedido.';
COMMENT ON COLUMN item_pedido.id_pedido IS 'Pedido a que o item pertence.';
COMMENT ON COLUMN item_pedido.id_produto IS 'Produto comprado.';
COMMENT ON COLUMN item_pedido.quantidade IS 'Quantidade comprada, maior que zero.';
COMMENT ON COLUMN item_pedido.preco_unitario IS 'Preço de uma unidade na hora da compra. Fica gravado para que mudanças futuras de preço não alterem pedidos antigos.';

COMMENT ON TABLE pagamento IS 'Tentativa de pagamento de um pedido. O pedido só vira CONFIRMADO depois da aprovação do banco (ID 11).';
COMMENT ON COLUMN pagamento.id_pagamento IS 'Identificador do pagamento.';
COMMENT ON COLUMN pagamento.id_pedido IS 'Pedido que está sendo pago.';
COMMENT ON COLUMN pagamento.forma IS 'CARTAO_CREDITO ou PIX.';
COMMENT ON COLUMN pagamento.valor IS 'Valor cobrado, maior que zero.';
COMMENT ON COLUMN pagamento.status IS 'PENDENTE (aguardando a operadora), APROVADO ou RECUSADO.';
COMMENT ON COLUMN pagamento.codigo_transacao IS 'Código devolvido pela operadora de pagamento, único.';
COMMENT ON COLUMN pagamento.data_hora IS 'Momento da tentativa de pagamento.';

COMMENT ON TABLE pedido IS 'Compra feita pelo cliente ou por um visitante. Guarda os valores no momento da compra (IDs 10, 09, 11, 12 e 18).';
COMMENT ON COLUMN pedido.id_pedido IS 'Identificador interno do pedido.';
COMMENT ON COLUMN pedido.numero IS 'Número mostrado ao cliente, começando em 10001.';
COMMENT ON COLUMN pedido.id_cliente IS 'Cliente que comprou. Vazio quando a compra foi como visitante.';
COMMENT ON COLUMN pedido.id_endereco IS 'Endereço de entrega.';
COMMENT ON COLUMN pedido.id_cupom IS 'Cupom usado no pedido, se houver.';
COMMENT ON COLUMN pedido.id_entregador IS 'Entregador responsável. Obrigatório a partir de SAIU_PARA_ENTREGA.';
COMMENT ON COLUMN pedido.data_hora IS 'Momento em que o pedido foi criado.';
COMMENT ON COLUMN pedido.status IS 'Situação do pedido: AGUARDANDO_PAGAMENTO, CONFIRMADO, EM_PREPARO, SAIU_PARA_ENTREGA, ENTREGUE ou CANCELADO.';
COMMENT ON COLUMN pedido.subtotal IS 'Soma dos itens, antes do frete e dos descontos.';
COMMENT ON COLUMN pedido.distancia_km IS 'Distância da loja até o endereço, em km, devolvida pela API de mapas.';
COMMENT ON COLUMN pedido.valor_frete IS 'Frete calculado pela distância.';
COMMENT ON COLUMN pedido.desconto IS 'Total de descontos (cupom e desconto do cliente cadastrado).';
COMMENT ON COLUMN pedido.total IS 'Valor final. O banco confere que é igual a subtotal + frete - desconto.';
COMMENT ON COLUMN pedido.previsao_entrega IS 'Horário previsto de chegada, atualizado quando o status muda.';
COMMENT ON COLUMN pedido.nome_contato IS 'Nome de contato. Usado principalmente na compra como visitante.';
COMMENT ON COLUMN pedido.email_contato IS 'E-mail para enviar o acompanhamento. Obrigatório quando o pedido é de visitante (ID 18).';
COMMENT ON COLUMN pedido.telefone_contato IS 'Telefone de contato para a entrega.';

COMMENT ON TABLE pessoa IS 'Dados comuns a quem usa o sistema. Classe abstrata: nunca existe sozinha, sempre é um cliente, funcionário ou entregador.';
COMMENT ON COLUMN pessoa.id_pessoa IS 'Identificador da pessoa (gerado pelo banco).';
COMMENT ON COLUMN pessoa.nome IS 'Nome completo.';
COMMENT ON COLUMN pessoa.email IS 'E-mail, único no sistema. Usado para contato e recuperação de senha.';
COMMENT ON COLUMN pessoa.celular IS 'Celular com DDD (aceita dígitos, parênteses, espaço, hífen e +).';

COMMENT ON TABLE preco_produto IS 'Preço de cada produto em cada tabela de preços.';
COMMENT ON COLUMN preco_produto.id_produto IS 'Produto que está sendo precificado.';
COMMENT ON COLUMN preco_produto.id_tabela_preco IS 'Tabela de preços a que o valor pertence.';
COMMENT ON COLUMN preco_produto.valor IS 'Preço em reais. Não pode ser negativo.';

COMMENT ON TABLE produto IS 'Qualquer coisa que se vende. Classe abstrata: cada produto é um cupcake ou um adicional.';
COMMENT ON COLUMN produto.id_produto IS 'Identificador do produto.';
COMMENT ON COLUMN produto.tipo IS 'Diz em qual tabela estão os detalhes: CUPCAKE ou ADICIONAL.';
COMMENT ON COLUMN produto.nome IS 'Nome exibido na vitrine.';
COMMENT ON COLUMN produto.imagem_url IS 'Endereço da foto do produto.';
COMMENT ON COLUMN produto.estoque IS 'Unidades disponíveis. Produto com estoque zero não aparece na vitrine (ID 01).';
COMMENT ON COLUMN produto.ativo IS 'Falso quando o produto saiu de linha.';

COMMENT ON TABLE solicitacao_evento IS 'Pedido de orçamento para eventos e grandes encomendas, de cliente ou visitante (ID 08).';
COMMENT ON COLUMN solicitacao_evento.id_solicitacao_evento IS 'Identificador da solicitação.';
COMMENT ON COLUMN solicitacao_evento.id_cliente IS 'Cliente que solicitou, se estava logado.';
COMMENT ON COLUMN solicitacao_evento.nome_contato IS 'Nome de quem pediu o orçamento.';
COMMENT ON COLUMN solicitacao_evento.email_contato IS 'E-mail para responder o orçamento. O administrador também recebe os dados por e-mail.';
COMMENT ON COLUMN solicitacao_evento.telefone_contato IS 'Telefone para contato.';
COMMENT ON COLUMN solicitacao_evento.data_evento IS 'Data da festa ou evento.';
COMMENT ON COLUMN solicitacao_evento.quantidade IS 'Quantidade de cupcakes. O mínimo é 30; abaixo disso o cliente é orientado a comprar pelo carrinho.';
COMMENT ON COLUMN solicitacao_evento.tema IS 'Tema do evento.';
COMMENT ON COLUMN solicitacao_evento.observacoes IS 'Detalhes adicionais.';
COMMENT ON COLUMN solicitacao_evento.data_solicitacao IS 'Momento em que o formulário foi enviado.';
COMMENT ON COLUMN solicitacao_evento.status IS 'RECEBIDA (nova), ORCADA (orçamento enviado) ou CANCELADA.';

COMMENT ON TABLE tabela_preco IS 'Conjunto de preços, como "Popular" e "Classe A/B". Só uma fica ativa por vez (ID 03).';
COMMENT ON COLUMN tabela_preco.id_tabela_preco IS 'Identificador da tabela de preços.';
COMMENT ON COLUMN tabela_preco.nome IS 'Nome da tabela, único.';
COMMENT ON COLUMN tabela_preco.ativa IS 'Verdadeiro para a tabela em uso. O banco impede duas tabelas ativas ao mesmo tempo.';

COMMENT ON TABLE token_recuperacao_senha IS 'Pedido de troca de senha. O link enviado por e-mail vale 1 hora e só pode ser usado uma vez (ID 19).';
COMMENT ON COLUMN token_recuperacao_senha.id_token IS 'Identificador do pedido de recuperação.';
COMMENT ON COLUMN token_recuperacao_senha.id_cliente IS 'Cliente que pediu a nova senha.';
COMMENT ON COLUMN token_recuperacao_senha.token_hash IS 'Hash SHA-256 (64 caracteres hexadecimais) do código enviado no link. O código em si não é gravado.';
COMMENT ON COLUMN token_recuperacao_senha.criado_em IS 'Momento em que o link foi gerado.';
COMMENT ON COLUMN token_recuperacao_senha.expira_em IS 'Momento em que o link deixa de valer (1 hora depois de criado).';
COMMENT ON COLUMN token_recuperacao_senha.usado IS 'Verdadeiro depois que o link foi usado.';
