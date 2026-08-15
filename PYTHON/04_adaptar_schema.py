# ============================================================
# Passo 4 — Adaptar ao schema e carregar no PostgreSQL
# Projeto: Análise de Inadimplência | BancoX
# ============================================================
# O que este script faz:
#   1. Lê o credit_risk_clean.csv (saída do passo 3)
#   2. Monta dim_clientes: colunas do dataset + Faker
#   3. Monta fato_contas: mapeamento direto do dataset
#   4. Gera fato_transacoes: criadas com Faker de forma
#      coerente com o perfil de cada cliente
#      (dim_categorias já foi carregada pelo schema.sql)
#   5. Carrega tudo no PostgreSQL via SQLAlchemy
# ============================================================

import pandas as pd
import numpy as np
from faker import Faker
from datetime import date
from datetime import date, datetime
from sqlalchemy import create_engine
import random

# ── Reprodutibilidade ─────────────────────────────────────────
Faker.seed(42)
random.seed(42)
np.random.seed(42)
fake = Faker('pt_BR')

# ── Configuração do banco ─────────────────────────────────────
# Substitua com os seus dados de conexão
DB_URL = "postgresql+psycopg://postgres:12345@localhost:5432/creditrisk"

# ── Caminho do arquivo ────────────────────────────────────────
CAMINHO_CSV = "credit_risk_clean.csv"   # ajuste se necessário


# ─────────────────────────────────────────────────────────────
# 1. Carregar dataset limpo
#    Separador é ponto e vírgula (padrão Excel pt-BR)
# ─────────────────────────────────────────────────────────────
print("Lendo dataset...")
df = pd.read_csv(CAMINHO_CSV, sep=';')
n  = len(df)
print(f"  {n:,} linhas carregadas\n")


# ─────────────────────────────────────────────────────────────
# 2. dim_clientes
#    Combina colunas do dataset com campos gerados pelo Faker
# ─────────────────────────────────────────────────────────────
print("Montando dim_clientes...")

def age_to_birthdate(age):
    """Converte person_age em uma data de nascimento aproximada."""
    year = date.today().year - int(age)
    return date(year, random.randint(1, 12), random.randint(1, 28))

def gerar_cpfs_unicos(quantidade):
    """Gera CPFs garantindo que não há duplicatas."""
    usados = set()
    resultado = []
    while len(resultado) < quantidade:
        cpf = fake.cpf()
        if cpf not in usados:
            usados.add(cpf)
            resultado.append(cpf)
    return resultado

dim_clientes = pd.DataFrame({
    'id_cliente':         range(1, n + 1),

    # gerados com Faker
    'nome':               [fake.name() for _ in range(n)],
    'cpf':                gerar_cpfs_unicos(n),           # UNIQUE no banco
    'genero':             random.choices(['M', 'F', 'O'], weights=[0.48, 0.48, 0.04], k=n),
    'estado':             [fake.state_abbr() for _ in range(n)],
    'cidade':             [fake.city() for _ in range(n)],
    'data_cadastro': [date(random.randint(2020, 2025), random.randint(1, 12), random.randint(1, 28)) for _ in range(n)],    

    # derivados do dataset
    'data_nascimento':    [age_to_birthdate(a) for a in df['person_age']],
    'renda_mensal':       (df['person_income'] / 12).round(2).values,
    'tipo_moradia':       df['person_home_ownership'].values,
    'tempo_emprego_anos': df['person_emp_length'].values,
    'historico_default':  df['cb_person_default_on_file'].values,
    'hist_credito_anos':  df['cb_person_cred_hist_length'].values,
})

print(f"  {len(dim_clientes):,} clientes gerados")
print(f"  CPFs únicos: {dim_clientes['cpf'].nunique():,}\n")


# ─────────────────────────────────────────────────────────────
# 3. fato_contas
#    Mapeamento direto das colunas de crédito do dataset
# ─────────────────────────────────────────────────────────────
print("Montando fato_contas...")

status_map = {0: 'adimplente', 1: 'inadimplente'}

fato_contas = pd.DataFrame({
    'id_conta':        range(1, n + 1),
    'id_cliente':      range(1, n + 1),
    'data_referencia': date(2024, 1, 1),                            # snapshot único do dataset
    'limite_credito':  df['loan_amnt'].values,
    'taxa_juros':      df['loan_int_rate'].round(2).values,
    'grau_risco':      df['loan_grade'].values,
    'pct_renda':       df['loan_percent_income'].values,
    'valor_utilizado': (df['loan_amnt'] * df['loan_percent_income']).round(2).values,
    'status_conta':    df['loan_status'].map(status_map).values,
})

print(f"  {len(fato_contas):,} contas")
print(f"  Adimplentes  : {(fato_contas['status_conta'] == 'adimplente').sum():,}")
print(f"  Inadimplentes: {(fato_contas['status_conta'] == 'inadimplente').sum():,}\n")


# ─────────────────────────────────────────────────────────────
# 4. fato_transacoes
#    Gerada com Faker de forma coerente com o perfil do cliente:
#      • inadimplentes → mais transações recusadas/pendentes
#      • renda maior → ticket médio maior
#      • loan_intent → categoria predominante das transações
# ─────────────────────────────────────────────────────────────
print("Gerando fato_transacoes (pode levar ~1 min para 32k clientes)...")

# IDs de dim_categorias definidos no schema.sql (seed)
intent_to_cat = {
    'PERSONAL': 1, 'EDUCATION': 2, 'MEDICAL': 3,
    'VENTURE': 4, 'HOMEIMPROVEMENT': 5, 'DEBTCONSOLIDATION': 6,
}

registros = []

for i, row in df.iterrows():
    id_cliente   = i + 1
    inadimplente = row['loan_status'] == 1
    renda_mensal = row['person_income'] / 12
    id_cat       = intent_to_cat[row['loan_intent']]
    n_transacoes = random.randint(5, 20)

    # Clientes inadimplentes têm mais recusas e pendências
    pesos_status = [0.60, 0.20, 0.20] if inadimplente else [0.88, 0.07, 0.05]

    for _ in range(n_transacoes):
        registros.append({
            'id_cliente':     id_cliente,
            'id_categoria':   id_cat,
            'data_transacao': datetime(random.randint(2023, 2025), random.randint(1, 12), random.randint(1, 28), random.randint(0, 23), random.randint(0, 59)),
            'valor':          round(random.uniform(renda_mensal * 0.01, renda_mensal * 0.30), 2),
            'tipo_transacao': random.choices(
                                ['pix', 'debito', 'credito', 'ted'],
                                weights=[0.50, 0.25, 0.15, 0.10])[0],
            'status':         random.choices(
                                ['aprovada', 'pendente', 'recusada'],
                                weights=pesos_status)[0],
            'canal':          random.choices(
                                ['app', 'agencia', 'atm', 'online'],
                                weights=[0.60, 0.10, 0.10, 0.20])[0],
        })

fato_transacoes = pd.DataFrame(registros)
fato_transacoes.insert(0, 'id_transacao', range(1, len(fato_transacoes) + 1))

print(f"  {len(fato_transacoes):,} transações geradas")
print(f"  Status: {fato_transacoes['status'].value_counts().to_dict()}")
print(f"  Tipos : {fato_transacoes['tipo_transacao'].value_counts().to_dict()}\n")


# ─────────────────────────────────────────────────────────────
# 5. Carregar no PostgreSQL
#    Ordem obrigatória por causa das FKs:
#      dim_categorias (já carregada pelo schema.sql)
#      → dim_clientes → fato_contas → fato_transacoes
# ─────────────────────────────────────────────────────────────
print("Conectando ao PostgreSQL...")
import os
os.environ["PGCLIENTENCODING"] = "UTF8"

engine = create_engine(DB_URL)

print("Carregando dim_clientes...")
dim_clientes.to_sql(
    name      = 'dim_clientes',
    con       = engine,
    if_exists = 'append',   # não recria a tabela, só insere
    index     = False,
    chunksize = 1000,       # envia em lotes de 1000 linhas
)
print(f"  {len(dim_clientes):,} linhas inseridas")

print("Carregando fato_contas...")
fato_contas.to_sql(
    name      = 'fato_contas',
    con       = engine,
    if_exists = 'append',
    index     = False,
    chunksize = 1000,
)
print(f"  {len(fato_contas):,} linhas inseridas")

print("Carregando fato_transacoes...")
fato_transacoes.to_sql(
    name      = 'fato_transacoes',
    con       = engine,
    if_exists = 'append',
    index     = False,
    chunksize = 1000,
)
print(f"  {len(fato_transacoes):,} linhas inseridas")

print("\n" + "=" * 55)
print("CARGA CONCLUÍDA")
print(f"  dim_clientes    : {len(dim_clientes):,} linhas")
print(f"  fato_contas     : {len(fato_contas):,} linhas")
print(f"  fato_transacoes : {len(fato_transacoes):,} linhas")
print("PRÓXIMO PASSO: queries SQL de análise")
print("=" * 55)