-- Consultas de exemplo (execute depois do schema e dos dados de exemplo)

-- Vitrine: cupcakes à venda, com preço da tabela ativa e categorias (IDs 01, 02 e 03)
SELECT p.nome, pp.valor AS preco,
       COALESCE(string_agg(cat.nome, ', ' ORDER BY cat.nome), '-') AS categorias
FROM produto p
JOIN cupcake c             ON c.id_cupcake = p.id_produto
JOIN preco_produto pp      ON pp.id_produto = p.id_produto
JOIN tabela_preco tp       ON tp.id_tabela_preco = pp.id_tabela_preco AND tp.ativa
LEFT JOIN cupcake_categoria cc ON cc.id_cupcake = c.id_cupcake
LEFT JOIN categoria cat    ON cat.id_categoria = cc.id_categoria
WHERE p.ativo AND p.estoque > 0
GROUP BY p.nome, pp.valor
ORDER BY p.nome;

-- Filtro "diet": cupcakes sem açúcar comum (ID 02)
SELECT p.nome, c.ingredientes
FROM produto p
JOIN cupcake c ON c.id_cupcake = p.id_produto
WHERE p.ativo AND p.estoque > 0 AND NOT c.contem_acucar
ORDER BY p.nome;

-- Acompanhamento do pedido 10001 (ID 12)
SELECT h.status, to_char(h.data_hora, 'HH24:MI') AS hora,
       COALESCE(pe.nome, 'sistema') AS quem_alterou
FROM historico_status h
JOIN pedido pd          ON pd.id_pedido = h.id_pedido
LEFT JOIN pessoa pe     ON pe.id_pessoa = h.id_pessoa
WHERE pd.numero = 10001
ORDER BY h.data_hora;

-- Meus pedidos de um cliente, com a quantidade de itens (ID 15)
SELECT pd.numero, pd.status, pd.total, SUM(ip.quantidade) AS unidades
FROM pedido pd
JOIN cliente c     ON c.id_cliente = pd.id_cliente
JOIN pessoa p      ON p.id_pessoa = c.id_cliente
JOIN item_pedido ip ON ip.id_pedido = pd.id_pedido
WHERE p.email = 'marcos@exemplo.com'
GROUP BY pd.numero, pd.status, pd.total
ORDER BY pd.numero DESC;

-- Resumo de vendas por status, para o painel do administrador
SELECT status, COUNT(*) AS pedidos, SUM(total) AS valor_total
FROM pedido
GROUP BY status
ORDER BY status;
