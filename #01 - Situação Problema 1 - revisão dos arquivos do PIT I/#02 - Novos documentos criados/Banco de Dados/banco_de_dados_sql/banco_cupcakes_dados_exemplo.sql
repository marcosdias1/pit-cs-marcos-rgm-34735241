-- =====================================================================
--  Dados de exemplo para testar o banco e a aplicação (opcional)
--  Execute DEPOIS de banco_cupcakes_schema.sql, num banco vazio.
--  Todos os dados são fictícios. As senhas são hashes de mentira.
-- =====================================================================

-- ---------- pessoas ----------
INSERT INTO pessoa (nome, email, celular) VALUES
    ('Marcos Dias',    'marcos@exemplo.com', '11900000001'),
    ('Ana Souza',      'ana@exemplo.com',    '11900000002'),
    ('Carla Mendes',   'carla@exemplo.com',  '11900000003'),
    ('Pedro Lima',     'pedro@exemplo.com',  '11900000004');

INSERT INTO cliente (id_cliente, cpf, senha_hash)
SELECT id_pessoa, CASE email WHEN 'marcos@exemplo.com' THEN '52998224725' ELSE '11144477735' END,
       '$2b$12$hashDeExemploNaoUsarEmProducao000000000000000000000'
FROM pessoa WHERE email IN ('marcos@exemplo.com', 'ana@exemplo.com');

INSERT INTO funcionario (id_funcionario, perfil, senha_hash)
SELECT id_pessoa, 'ADMINISTRADOR', '$2b$12$hashDeExemploNaoUsarEmProducao000000000000000000000'
FROM pessoa WHERE email = 'carla@exemplo.com';

INSERT INTO entregador (id_entregador, placa)
SELECT id_pessoa, 'ABC1D23' FROM pessoa WHERE email = 'pedro@exemplo.com';

-- ---------- endereços e cartão ----------
INSERT INTO endereco (id_cliente, apelido, cep, rua, numero, bairro, cidade, uf, principal)
SELECT c.id_cliente, v.apelido, v.cep, v.rua, v.numero, v.bairro, 'São Paulo', 'SP', v.principal
FROM (VALUES
    ('marcos@exemplo.com', 'Casa',     '01234000', 'Rua das Flores',  '123', 'Centro',     TRUE),
    ('marcos@exemplo.com', 'Trabalho', '04567000', 'Avenida Paulista','1000','Bela Vista', FALSE),
    ('ana@exemplo.com',    'Casa',     '05678000', 'Rua das Acácias', '45',  'Pinheiros',  TRUE)
) AS v(email, apelido, cep, rua, numero, bairro, principal)
JOIN pessoa p ON p.email = v.email
JOIN cliente c ON c.id_cliente = p.id_pessoa;

-- endereço de um visitante (sem cliente)
INSERT INTO endereco (cep, rua, numero, bairro, cidade, uf)
VALUES ('02345000', 'Rua do Visitante', '77', 'Santana', 'São Paulo', 'SP');

INSERT INTO cartao_salvo (id_cliente, bandeira, ultimos_digitos, validade_mes, validade_ano, token_operadora)
SELECT id_pessoa, 'Visa', '1234', 12, 2030, 'tok_exemplo_visa_1234'
FROM pessoa WHERE email = 'marcos@exemplo.com';

INSERT INTO token_recuperacao_senha (id_cliente, token_hash, expira_em)
SELECT id_pessoa, repeat('a1', 32), CURRENT_TIMESTAMP + INTERVAL '1 hour'
FROM pessoa WHERE email = 'ana@exemplo.com';

-- ---------- catálogo ----------
INSERT INTO categoria (nome) VALUES
    ('Diet'), ('Salgado'), ('Regional'), ('Tempo limitado'), ('Promoção');

INSERT INTO produto (tipo, nome, imagem_url, estoque) VALUES
    ('CUPCAKE',   'Red Velvet',        'img/red-velvet.jpg',  40),
    ('CUPCAKE',   'Limão',             'img/limao.jpg',       35),
    ('CUPCAKE',   'Chocolate',         'img/chocolate.jpg',   50),
    ('CUPCAKE',   'Morango',           'img/morango.jpg',     30),
    ('CUPCAKE',   'Brigadeiro Diet',   'img/brig-diet.jpg',   20),
    ('CUPCAKE',   'Queijo e Orégano',  'img/queijo.jpg',      25),
    ('CUPCAKE',   'Cupuaçu',           'img/cupuacu.jpg',     15),
    ('CUPCAKE',   'Abóbora (Halloween)','img/abobora.jpg',     0),
    ('ADICIONAL', 'Embalagem especial','img/embalagem.jpg',   100),
    ('ADICIONAL', 'Chocolate extra',   'img/choco-extra.jpg', 100),
    ('ADICIONAL', 'Balas coloridas',   'img/balas.jpg',       100);

INSERT INTO cupcake (id_cupcake, descricao, ingredientes, alergenos, contem_acucar)
SELECT p.id_produto, v.descricao, v.ingredientes, v.alergenos, v.acucar
FROM (VALUES
    ('Red Velvet',         'Massa aveludada com cobertura de cream cheese.', 'farinha, cacau, açúcar, cream cheese, manteiga', 'leite, ovo e glúten', TRUE),
    ('Limão',              'Massa leve com cobertura cítrica.',              'farinha, limão, açúcar, manteiga',                 'leite, ovo e glúten', TRUE),
    ('Chocolate',          'Massa de chocolate com ganache.',                'farinha, cacau, açúcar, chocolate meio amargo',    'leite, ovo e glúten', TRUE),
    ('Morango',            'Massa branca com recheio de morango.',           'farinha, morango, açúcar, creme de leite',         'leite, ovo e glúten', TRUE),
    ('Brigadeiro Diet',    'Versão sem açúcar com cobertura de brigadeiro.', 'farinha, cacau, adoçante, leite desnatado',        'leite, ovo e glúten', FALSE),
    ('Queijo e Orégano',   'Cupcake salgado com queijo derretido.',          'farinha, queijo, orégano, ovo',                    'leite, ovo e glúten', FALSE),
    ('Cupuaçu',            'Sabor regional com creme de cupuaçu.',           'farinha, cupuaçu, açúcar, manteiga',               'leite, ovo e glúten', TRUE),
    ('Abóbora (Halloween)','Edição de tempo limitado.',                      'farinha, abóbora, canela, açúcar',                 'ovo e glúten',        TRUE)
) AS v(nome, descricao, ingredientes, alergenos, acucar)
JOIN produto p ON p.nome = v.nome;

INSERT INTO adicional (id_adicional, tipo_adicional)
SELECT id_produto, CASE nome WHEN 'Embalagem especial' THEN 'EMBALAGEM'
                             WHEN 'Chocolate extra'    THEN 'CHOCOLATE'
                             ELSE 'BALA' END
FROM produto WHERE tipo = 'ADICIONAL';

INSERT INTO cupcake_categoria (id_cupcake, id_categoria)
SELECT p.id_produto, c.id_categoria
FROM (VALUES
    ('Brigadeiro Diet', 'Diet'), ('Queijo e Orégano', 'Salgado'), ('Cupuaçu', 'Regional'),
    ('Abóbora (Halloween)', 'Tempo limitado'), ('Morango', 'Promoção'), ('Limão', 'Promoção')
) AS v(produto, categoria)
JOIN produto p ON p.nome = v.produto
JOIN categoria c ON c.nome = v.categoria;

INSERT INTO tabela_preco (nome, ativa) VALUES ('Popular', TRUE), ('Classe A/B', FALSE);

INSERT INTO preco_produto (id_produto, id_tabela_preco, valor)
SELECT p.id_produto, t.id_tabela_preco,
       CASE WHEN p.tipo = 'CUPCAKE' THEN (CASE t.nome WHEN 'Popular' THEN 12.00 ELSE 15.00 END)
            WHEN p.nome = 'Embalagem especial' THEN (CASE t.nome WHEN 'Popular' THEN 5.00 ELSE 6.00 END)
            WHEN p.nome = 'Chocolate extra'    THEN (CASE t.nome WHEN 'Popular' THEN 4.00 ELSE 5.00 END)
            ELSE (CASE t.nome WHEN 'Popular' THEN 3.00 ELSE 4.00 END) END
FROM produto p CROSS JOIN tabela_preco t;

-- ---------- cupons ----------
INSERT INTO cupom (codigo, tipo, valor, valido_de, valido_ate, uso_unico, primeira_compra)
VALUES ('BEMVINDO15', 'VALOR_FIXO', 15.00, DATE '2026-01-01', DATE '2030-12-31', TRUE,  TRUE),
       ('PROMO10',    'PERCENTUAL', 10.00, DATE '2026-01-01', DATE '2030-12-31', FALSE, FALSE),
       ('VENCIDO5',   'VALOR_FIXO',  5.00, DATE '2025-01-01', DATE '2025-01-31', FALSE, FALSE);

INSERT INTO cupom (id_cliente, codigo, tipo, valor, valido_de, valido_ate, uso_unico)
SELECT id_pessoa, 'MARCOS5', 'VALOR_FIXO', 5.00, DATE '2026-01-01', DATE '2030-12-31', FALSE
FROM pessoa WHERE email = 'marcos@exemplo.com';

-- ---------- carrinhos ----------
INSERT INTO carrinho (id_cliente) SELECT id_pessoa FROM pessoa WHERE email = 'ana@exemplo.com';
INSERT INTO carrinho (id_sessao) VALUES ('sessao-visitante-0001');

INSERT INTO item_carrinho (id_carrinho, id_produto, quantidade)
SELECT c.id_carrinho, p.id_produto, v.qtd
FROM (VALUES ('ana@exemplo.com', 'Cupuaçu', 2), ('ana@exemplo.com', 'Balas coloridas', 1)) AS v(email, produto, qtd)
JOIN pessoa pe ON pe.email = v.email
JOIN carrinho c ON c.id_cliente = pe.id_pessoa
JOIN produto p ON p.nome = v.produto;

-- ---------- pedido 1: Marcos, entregue ----------
INSERT INTO pedido (id_cliente, id_endereco, id_cupom, id_entregador, status,
                    subtotal, distancia_km, valor_frete, desconto, total, previsao_entrega)
SELECT pe.id_pessoa,
       (SELECT id_endereco FROM endereco WHERE id_cliente = pe.id_pessoa AND principal),
       (SELECT id_cupom FROM cupom WHERE codigo = 'MARCOS5'),
       (SELECT id_pessoa FROM pessoa WHERE email = 'pedro@exemplo.com'),
       'ENTREGUE', 41.00, 4.20, 7.50, 5.00, 43.50, CURRENT_TIMESTAMP
FROM pessoa pe WHERE pe.email = 'marcos@exemplo.com';

INSERT INTO item_pedido (id_pedido, id_produto, quantidade, preco_unitario)
SELECT (SELECT id_pedido FROM pedido WHERE numero = 10001), p.id_produto, v.qtd, v.preco
FROM (VALUES ('Red Velvet', 2, 12.00), ('Limão', 1, 12.00), ('Embalagem especial', 1, 5.00)) AS v(produto, qtd, preco)
JOIN produto p ON p.nome = v.produto;

INSERT INTO pagamento (id_pedido, forma, valor, status, codigo_transacao)
SELECT id_pedido, 'CARTAO_CREDITO', 43.50, 'APROVADO', 'tx-exemplo-0001' FROM pedido WHERE numero = 10001;

INSERT INTO historico_status (id_pedido, id_pessoa, status, data_hora)
SELECT (SELECT id_pedido FROM pedido WHERE numero = 10001),
       (SELECT id_pessoa FROM pessoa WHERE email = v.email), v.status,
       CURRENT_TIMESTAMP - v.atras
FROM (VALUES
    (NULL::text,         'AGUARDANDO_PAGAMENTO', INTERVAL '60 minutes'),
    (NULL,               'CONFIRMADO',           INTERVAL '58 minutes'),
    ('carla@exemplo.com','EM_PREPARO',           INTERVAL '55 minutes'),
    ('carla@exemplo.com','SAIU_PARA_ENTREGA',    INTERVAL '30 minutes'),
    ('pedro@exemplo.com','ENTREGUE',             INTERVAL '5 minutes')
) AS v(email, status, atras);

INSERT INTO checklist_embalagem (id_pedido, id_funcionario, aprovado, observacao)
SELECT (SELECT id_pedido FROM pedido WHERE numero = 10001),
       (SELECT id_pessoa FROM pessoa WHERE email = 'carla@exemplo.com'),
       TRUE, 'Embalagem íntegra e lacrada.';

-- ---------- pedido 2: visitante, aguardando pagamento PIX ----------
INSERT INTO pedido (id_endereco, status, subtotal, distancia_km, valor_frete, desconto, total, email_contato, nome_contato)
SELECT id_endereco, 'AGUARDANDO_PAGAMENTO', 12.00, 3.10, 6.00, 0.00, 18.00, 'visitante@exemplo.com', 'Visitante'
FROM endereco WHERE id_cliente IS NULL;

INSERT INTO item_pedido (id_pedido, id_produto, quantidade, preco_unitario)
SELECT (SELECT id_pedido FROM pedido WHERE numero = 10002), id_produto, 1, 12.00
FROM produto WHERE nome = 'Chocolate';

INSERT INTO pagamento (id_pedido, forma, valor, status)
SELECT id_pedido, 'PIX', 18.00, 'PENDENTE' FROM pedido WHERE numero = 10002;

-- ---------- pedido 3: Ana, em preparo ----------
INSERT INTO pedido (id_cliente, id_endereco, status, subtotal, distancia_km, valor_frete, desconto, total)
SELECT pe.id_pessoa, (SELECT id_endereco FROM endereco WHERE id_cliente = pe.id_pessoa AND principal),
       'EM_PREPARO', 24.00, 6.80, 9.00, 0.00, 33.00
FROM pessoa pe WHERE pe.email = 'ana@exemplo.com';

INSERT INTO item_pedido (id_pedido, id_produto, quantidade, preco_unitario)
SELECT (SELECT id_pedido FROM pedido WHERE numero = 10003), id_produto, 2, 12.00
FROM produto WHERE nome = 'Morango';

INSERT INTO pagamento (id_pedido, forma, valor, status, codigo_transacao)
SELECT id_pedido, 'PIX', 33.00, 'APROVADO', 'tx-exemplo-0003' FROM pedido WHERE numero = 10003;

-- ---------- orçamento de evento ----------
INSERT INTO solicitacao_evento (nome_contato, email_contato, telefone_contato, data_evento, quantidade, tema, observacoes)
VALUES ('Empresa Exemplo Ltda', 'contato@empresa.exemplo', '1130000000', DATE '2026-12-18', 60,
        'Confraternização de fim de ano', 'Entrega às 11h, com embalagem especial.');
