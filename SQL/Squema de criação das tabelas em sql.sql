-- ============================================================
-- Projeto: Análise de Inadimplência e Comportamento de Clientes
-- Banco:   BancoX (fictício) | Base: credit_risk_dataset (Kaggle)
-- Schema:  star schema — 2 tabelas fato + 2 dimensões
-- ============================================================

-- Para recriar do zero (rodar na ordem inversa por causa das FKs):
 DROP TABLE IF EXISTS fato_transacoes;
-- DROP TABLE IF EXISTS fato_contas;
-- DROP TABLE IF EXISTS dim_clientes;
-- DROP TABLE IF EXISTS dim_categorias;

-- Primeiro, garanta que o schema existe
CREATE SCHEMA IF NOT EXISTS creditrisk;

-- Muda o contexto da sessão/script para o seu schema
SET search_path TO creditrisk;
-- ============================================================
-- 1. dim_categorias
--    Fonte: loan_intent do dataset (PERSONAL, EDUCATION, etc.)
--    Sem FKs — deve ser criada primeira
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_categorias (
    id_categoria    SERIAL       PRIMARY KEY,
    nome_categoria  VARCHAR(50)  NOT NULL,
    intencao_orig   VARCHAR(30)  NOT NULL,  -- valor original do loan_intent
    tipo            VARCHAR(20)  NOT NULL   -- 'essencial' | 'variavel' | 'luxo'
);

-- Seed: mapeamento loan_intent → português + tipo
INSERT INTO dim_categorias (nome_categoria, intencao_orig, tipo) VALUES
    ('Pessoal',                'PERSONAL',          'variavel'),
    ('Educação',               'EDUCATION',          'essencial'),
    ('Saúde',                  'MEDICAL',            'essencial'),
    ('Empreendimento',         'VENTURE',            'variavel'),
    ('Melhoria de Imóvel',     'HOMEIMPROVEMENT',    'variavel'),
    ('Consolidação de Dívida', 'DEBTCONSOLIDATION',  'variavel')
ON CONFLICT DO NOTHING;


-- ============================================================
-- 2. dim_clientes
--    Do dataset: person_age, person_income, person_home_ownership,
--                person_emp_length, cb_person_default_on_file,
--                cb_person_cred_hist_length
--    Gerado com Faker: nome, cpf, genero, estado, cidade, data_cadastro
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_clientes (
    id_cliente          SERIAL        PRIMARY KEY,

    -- campos gerados com Faker
    nome                VARCHAR(100)  NOT NULL,
    cpf                 VARCHAR(14)   NOT NULL UNIQUE,  -- formato: 000.000.000-00
    genero              CHAR(1),                        -- 'M', 'F', 'O'
    estado              CHAR(2),                        -- UF: 'SP', 'RJ', etc.
    cidade              VARCHAR(100),
    data_cadastro       DATE          NOT NULL,

    -- campos derivados do dataset
    data_nascimento     DATE,                           -- derivado de person_age
    renda_mensal        NUMERIC(10,2),                  -- person_income / 12
    tipo_moradia        VARCHAR(20),                    -- RENT | OWN | MORTGAGE | OTHER
    tempo_emprego_anos  NUMERIC(5,1),                   -- person_emp_length (nulos + outlier 123 → tratar)
    historico_default   BOOLEAN,                        -- cb_person_default_on_file: 'Y'→true, 'N'→false
    hist_credito_anos   SMALLINT                        -- cb_person_cred_hist_length (range: 2–30)
);


-- ============================================================
-- 3. fato_contas  (snapshot de crédito por cliente)
--    Do dataset: loan_amnt, loan_int_rate, loan_percent_income,
--                loan_grade, loan_status
--    Grão: um registro por cliente (este dataset não tem série temporal)
-- ============================================================
CREATE TABLE IF NOT EXISTS fato_contas (
    id_conta         SERIAL        PRIMARY KEY,
    id_cliente       INTEGER       NOT NULL REFERENCES dim_clientes(id_cliente),
    data_referencia  DATE          NOT NULL,         -- data de carga (definida no Python)

    limite_credito   NUMERIC(10,2) NOT NULL,         -- loan_amnt (range: 500–35.000)
    taxa_juros       NUMERIC(5,2),                   -- loan_int_rate (range: 5.42–23.22; 3116 nulos → tratar)
    grau_risco       CHAR(1)       NOT NULL,         -- loan_grade: A (melhor crédito) → G (pior)
    pct_renda        NUMERIC(5,4)  NOT NULL,         -- loan_percent_income (ex: 0.1200 = 12%)
    valor_utilizado  NUMERIC(10,2) NOT NULL,         -- loan_amnt * loan_percent_income (derivado)
    status_conta     VARCHAR(20)   NOT NULL          -- loan_status: 0→'adimplente' | 1→'inadimplente'
);


-- ============================================================
-- 4. fato_transacoes  (gerada com Faker no Python)
--    Grão: uma linha por transação individual
--    Regras de geração (aplicadas no Python):
--      • clientes inadimplentes → mais transações recusadas
--      • renda maior → ticket médio maior
--      • loan_intent do cliente → categoria predominante da transação
--      • entre 5 e 20 transações por cliente geradas
-- ============================================================
CREATE TABLE IF NOT EXISTS fato_transacoes (
    id_transacao    SERIAL        PRIMARY KEY,
    id_cliente      INTEGER       NOT NULL REFERENCES dim_clientes(id_cliente),
    id_categoria    INTEGER       NOT NULL REFERENCES dim_categorias(id_categoria),
    data_transacao  TIMESTAMP     NOT NULL,
    valor           NUMERIC(10,2) NOT NULL,
    tipo_transacao  VARCHAR(10)   NOT NULL,  -- 'pix' | 'debito' | 'credito' | 'ted'
    status          VARCHAR(10)   NOT NULL,  -- 'aprovada' | 'recusada' | 'pendente'
    canal           VARCHAR(10)   NOT NULL   -- 'app' | 'agencia' | 'atm' | 'online'
);


-- ============================================================
-- Índices — aceleram JOINs e filtros de data nas queries
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fato_contas_cliente
    ON fato_contas(id_cliente);

CREATE INDEX IF NOT EXISTS idx_transacoes_cliente
    ON fato_transacoes(id_cliente);

CREATE INDEX IF NOT EXISTS idx_transacoes_categoria
    ON fato_transacoes(id_categoria);

CREATE INDEX IF NOT EXISTS idx_transacoes_data
    ON fato_transacoes(data_transacao);

CREATE INDEX IF NOT EXISTS idx_transacoes_status
    ON fato_transacoes(status);