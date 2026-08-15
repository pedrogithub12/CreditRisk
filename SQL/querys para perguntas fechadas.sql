-- ============================================================
-- Passo 5 — Queries SQL para as perguntas fechadas
-- Projeto: Análise de Inadimplência | BancoX
-- ============================================================
-- Estas 6 queries respondem diretamente as perguntas fechadas
-- definidas no início do projeto. Cada uma foi testada e
-- retorna resultados coerentes com os dados carregados.
--
-- Como rodar: cole cada bloco separadamente no Query Tool do
-- pgAdmin (ou no psql) e execute. Comentários explicam cada
-- cláusula para quem está aprendendo SQL agora.
-- ============================================================


-- ============================================================
-- 1. Qual o ticket médio por categoria de gasto?
-- ============================================================
-- JOIN: junta fato_transacoes com dim_categorias usando o id
--       em comum, para trocar o número da categoria pelo nome
-- WHERE: filtra só transações aprovadas (recusadas não geram receita real)
-- GROUP BY: agrupa uma linha por categoria
-- AVG / SUM: calculam a média e o total de cada grupo

SELECT
    c.nome_categoria,
    c.tipo,
    COUNT(t.id_transacao)   AS qtd_transacoes,
    ROUND(AVG(t.valor), 2)  AS ticket_medio,
    ROUND(SUM(t.valor), 2)  AS volume_total
FROM fato_transacoes t
JOIN dim_categorias c ON t.id_categoria = c.id_categoria
WHERE t.status = 'aprovada'
GROUP BY c.nome_categoria, c.tipo
ORDER BY ticket_medio DESC;


-- ============================================================
-- 2. Qual o mês com maior volume de transações?
-- ============================================================
-- DATE_TRUNC('month', ...): arredonda a data para o primeiro dia
--       do mês, permitindo agrupar por mês em vez de por dia exato
-- LIMIT 5: mostra só os 5 primeiros (o "maior" já fica no topo
--       por causa do ORDER BY DESC)

SELECT
    DATE_TRUNC('month', data_transacao) AS mes,
    COUNT(*)                            AS qtd_transacoes,
    ROUND(SUM(valor), 2)                AS volume_total
FROM fato_transacoes
WHERE status = 'aprovada'
GROUP BY DATE_TRUNC('month', data_transacao)
ORDER BY volume_total DESC
LIMIT 5;


-- ============================================================
-- 3. Qual a taxa de inadimplência por faixa etária?
-- ============================================================
-- WITH ... AS (): é uma CTE (common table expression) — uma
--       "tabela temporária" que existe só durante essa query,
--       útil para organizar cálculos em etapas
-- AGE(data_nascimento): calcula a idade atual do cliente
-- CASE WHEN: cria a faixa etária testando condições em ordem
-- COUNT(DISTINCT CASE WHEN ...): conta só os clientes que
--       atendem a condição dentro do CASE — truque comum para
--       "contar condicionalmente" dentro de um agrupamento

WITH clientes_faixa AS (
    SELECT
        id_cliente,
        CASE
            WHEN EXTRACT(YEAR FROM AGE(data_nascimento)) < 25 THEN '18-24'
            WHEN EXTRACT(YEAR FROM AGE(data_nascimento)) < 35 THEN '25-34'
            WHEN EXTRACT(YEAR FROM AGE(data_nascimento)) < 45 THEN '35-44'
            WHEN EXTRACT(YEAR FROM AGE(data_nascimento)) < 55 THEN '45-54'
            ELSE '55+'
        END AS faixa_etaria
    FROM dim_clientes
)
SELECT
    f.faixa_etaria,
    COUNT(DISTINCT ct.id_cliente) AS total_clientes,
    COUNT(DISTINCT CASE WHEN ct.status_conta = 'inadimplente' THEN ct.id_cliente END) AS inadimplentes,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN ct.status_conta = 'inadimplente' THEN ct.id_cliente END)
        / NULLIF(COUNT(DISTINCT ct.id_cliente), 0), 1
    ) AS taxa_pct
FROM fato_contas ct
JOIN clientes_faixa f ON ct.id_cliente = f.id_cliente
GROUP BY f.faixa_etaria
ORDER BY f.faixa_etaria;


-- ============================================================
-- 4. Quais os 5 estados com maior valor médio de transação?
-- ============================================================
-- Mesma lógica da query 1, mas juntando com dim_clientes em vez
-- de dim_categorias, porque o estado mora na tabela de clientes

SELECT
    cl.estado,
    COUNT(t.id_transacao)  AS qtd_transacoes,
    ROUND(AVG(t.valor), 2) AS valor_medio,
    ROUND(SUM(t.valor), 2) AS volume_total
FROM fato_transacoes t
JOIN dim_clientes cl ON t.id_cliente = cl.id_cliente
WHERE t.status = 'aprovada'
GROUP BY cl.estado
ORDER BY valor_medio DESC
LIMIT 5;


-- ============================================================
-- 5. Qual o percentual de transações recusadas por canal?
-- ============================================================
-- FILTER (WHERE ...): é uma forma mais limpa do que CASE WHEN
--       para contar condicionalmente — só soma as linhas que
--       passam no filtro dentro do agregado
-- Repare que aqui NÃO filtramos por status = 'aprovada' no WHERE
--       principal, porque precisamos contar TODAS as transações
--       (aprovadas + recusadas + pendentes) para calcular o %

SELECT
    canal,
    COUNT(*)                                       AS total,
    COUNT(*) FILTER (WHERE status = 'recusada')    AS recusadas,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'recusada') / COUNT(*), 1
    ) AS pct_recusadas
FROM fato_transacoes
GROUP BY canal
ORDER BY pct_recusadas DESC;


-- ============================================================
-- 6. Qual a correlação entre renda e limite de crédito?
-- ============================================================
-- CORR(x, y): função estatística nativa do PostgreSQL que
--       calcula o coeficiente de correlação de Pearson (-1 a 1)
-- Aproveitamos para calcular também renda x taxa de juros,
--       que é uma comparação natural de se fazer junto

SELECT
    ROUND(CORR(cl.renda_mensal, ct.limite_credito)::numeric, 3) AS correlacao_renda_limite,
    ROUND(CORR(cl.renda_mensal, ct.taxa_juros)::numeric, 3)     AS correlacao_renda_juros
FROM dim_clientes cl
JOIN fato_contas ct ON cl.id_cliente = ct.id_cliente;