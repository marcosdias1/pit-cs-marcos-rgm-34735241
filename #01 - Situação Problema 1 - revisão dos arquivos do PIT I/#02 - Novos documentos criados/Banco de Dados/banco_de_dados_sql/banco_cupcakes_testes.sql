-- =====================================================================
--  Testes do banco: cada teste tenta gravar um dado que as regras de
--  negócio proíbem e confere que o banco RECUSA.
--  Execute DEPOIS do schema e dos dados de exemplo:
--     psql -d cupcakes -f banco_cupcakes_testes.sql
--  Cada linha de resultado é "PASSOU" (o banco recusou) ou "FALHOU".
-- =====================================================================
CREATE TEMP TABLE resultado_teste (n INT, regra TEXT, resultado TEXT, motivo TEXT);

CREATE FUNCTION pg_temp.esperar_erro(n INT, regra TEXT, comando TEXT) RETURNS VOID AS $f$
BEGIN
    BEGIN
        EXECUTE comando;
        INSERT INTO resultado_teste VALUES (n, regra, 'FALHOU', 'o banco aceitou o dado inválido');
        RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'desfaz';
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLERRM = 'desfaz' THEN
                NULL;
            ELSE
                INSERT INTO resultado_teste VALUES (n, regra, 'PASSOU', regexp_replace(SQLERRM, '\s+', ' ', 'g'));
            END IF;
    END;
END;
$f$ LANGUAGE plpgsql;

SELECT pg_temp.esperar_erro(1,  'CPF só aceita 11 dígitos numéricos',
  $$INSERT INTO cliente (id_cliente, cpf, senha_hash) SELECT id_pessoa, '1234ABC8901', 'x' FROM pessoa WHERE email = 'carla@exemplo.com'$$);
SELECT pg_temp.esperar_erro(2,  'Um CPF só pode ter uma conta',
  $$INSERT INTO cliente (id_cliente, cpf, senha_hash) SELECT id_pessoa, '52998224725', 'x' FROM pessoa WHERE email = 'carla@exemplo.com'$$);
SELECT pg_temp.esperar_erro(3,  'O e-mail é único no sistema',
  $$INSERT INTO pessoa (nome, email, celular) VALUES ('Outro', 'marcos@exemplo.com', '11999999999')$$);
SELECT pg_temp.esperar_erro(4,  'Cada cliente tem no máximo um endereço principal',
  $$INSERT INTO endereco (id_cliente, cep, rua, numero, bairro, cidade, uf, principal)
    SELECT id_pessoa, '01234000', 'Rua X', '1', 'Centro', 'São Paulo', 'SP', TRUE FROM pessoa WHERE email = 'marcos@exemplo.com'$$);
SELECT pg_temp.esperar_erro(5,  'Só uma tabela de preço pode estar ativa',
  $$UPDATE tabela_preco SET ativa = TRUE WHERE nome = 'Classe A/B'$$);
SELECT pg_temp.esperar_erro(6,  'O estoque não pode ser negativo',
  $$UPDATE produto SET estoque = -1 WHERE nome = 'Red Velvet'$$);
SELECT pg_temp.esperar_erro(7,  'Total do pedido = subtotal + frete - desconto',
  $$INSERT INTO pedido (id_endereco, subtotal, valor_frete, desconto, total, email_contato)
    SELECT id_endereco, 10, 5, 0, 99, 'a@b.com' FROM endereco WHERE id_cliente IS NULL$$);
SELECT pg_temp.esperar_erro(8,  'Pedido de visitante precisa de e-mail de contato',
  $$INSERT INTO pedido (id_endereco, subtotal, valor_frete, desconto, total)
    SELECT id_endereco, 10, 5, 0, 15 FROM endereco WHERE id_cliente IS NULL$$);
SELECT pg_temp.esperar_erro(9,  'Pedido só sai para entrega se tiver entregador',
  $$UPDATE pedido SET status = 'SAIU_PARA_ENTREGA', id_entregador = NULL WHERE numero = 10003$$);
SELECT pg_temp.esperar_erro(10, 'Cupom percentual não passa de 100%',
  $$INSERT INTO cupom (codigo, tipo, valor, valido_de, valido_ate) VALUES ('GRANDE', 'PERCENTUAL', 150, DATE '2026-01-01', DATE '2026-12-31')$$);
SELECT pg_temp.esperar_erro(11, 'O fim da validade do cupom não vem antes do início',
  $$INSERT INTO cupom (codigo, tipo, valor, valido_de, valido_ate) VALUES ('INVERTIDO', 'VALOR_FIXO', 5, DATE '2026-12-31', DATE '2026-01-01')$$);
SELECT pg_temp.esperar_erro(12, 'Orçamento de evento exige no mínimo 30 unidades',
  $$INSERT INTO solicitacao_evento (nome_contato, email_contato, telefone_contato, data_evento, quantidade)
    VALUES ('Teste', 't@t.com', '11999999999', DATE '2026-12-01', 20)$$);
SELECT pg_temp.esperar_erro(13, 'Quantidade no carrinho precisa ser maior que zero',
  $$INSERT INTO item_carrinho (id_carrinho, id_produto, quantidade)
    SELECT c.id_carrinho, p.id_produto, 0 FROM carrinho c, produto p WHERE c.id_sessao IS NOT NULL AND p.nome = 'Red Velvet'$$);
SELECT pg_temp.esperar_erro(14, 'Cada pedido tem um único checklist de embalagem',
  $$INSERT INTO checklist_embalagem (id_pedido, id_funcionario, aprovado)
    SELECT (SELECT id_pedido FROM pedido WHERE numero = 10001), (SELECT id_pessoa FROM pessoa WHERE email = 'carla@exemplo.com'), TRUE$$);
SELECT pg_temp.esperar_erro(15, 'Carrinho precisa de dono (cliente ou sessão de visitante)',
  $$INSERT INTO carrinho (id_cliente, id_sessao) VALUES (NULL, NULL)$$);
SELECT pg_temp.esperar_erro(16, 'Não se apaga um cliente que já tem pedidos',
  $$DELETE FROM pessoa WHERE email = 'marcos@exemplo.com'$$);
SELECT pg_temp.esperar_erro(17, 'O link de recuperação de senha não expira antes de ser criado',
  $$INSERT INTO token_recuperacao_senha (id_cliente, token_hash, criado_em, expira_em)
    SELECT id_pessoa, repeat('b2', 32), CURRENT_TIMESTAMP, CURRENT_TIMESTAMP - INTERVAL '1 hour' FROM pessoa WHERE email = 'ana@exemplo.com'$$);
SELECT pg_temp.esperar_erro(18, 'O tipo do produto só pode ser CUPCAKE ou ADICIONAL',
  $$INSERT INTO produto (tipo, nome) VALUES ('BEBIDA', 'Suco')$$);
SELECT pg_temp.esperar_erro(19, 'Cartão salvo guarda só os 4 últimos dígitos',
  $$INSERT INTO cartao_salvo (id_cliente, bandeira, ultimos_digitos, validade_mes, validade_ano, token_operadora)
    SELECT id_pessoa, 'Visa', '4111111111111111', 1, 2030, 'tok_x' FROM pessoa WHERE email = 'ana@exemplo.com'$$);
SELECT pg_temp.esperar_erro(20, 'Forma de pagamento só PIX ou cartão de crédito',
  $$INSERT INTO pagamento (id_pedido, forma, valor) SELECT id_pedido, 'BOLETO', 10 FROM pedido WHERE numero = 10003$$);

SELECT n AS "nº", resultado, regra,
       COALESCE(substring(motivo from 'constraint "([^"]+)"'),
                substring(motivo from '(value too long for type [a-z]+\([0-9]+\))')) AS restricao_que_barrou
FROM resultado_teste ORDER BY n;
SELECT count(*) FILTER (WHERE resultado = 'PASSOU') AS passou,
       count(*) FILTER (WHERE resultado = 'FALHOU') AS falhou
FROM resultado_teste;
