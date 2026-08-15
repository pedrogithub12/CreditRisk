# ============================================================
# Passo 2 — Importar e explorar o dataset
# Projeto: Análise de Inadimplência | BancoX
# ============================================================
# O objetivo deste script é:
#   1. Ler o CSV com pandas
#   2. Entender o que chegou (shape, tipos, nulos)
#   3. Identificar os problemas que trataremos no passo 3
# Ainda não há limpeza aqui — só olhamos os dados.
# ============================================================

import pandas as pd

# ── Caminho do arquivo ────────────────────────────────────────
CAMINHO_CSV = "credit_risk_dataset.csv"  # ajuste se necessário

# ─────────────────────────────────────────────────────────────
# 1. Carregar o CSV
# ─────────────────────────────────────────────────────────────
df = pd.read_csv(CAMINHO_CSV)

print("=" * 55)
print("1. SHAPE DO DATASET")
print("=" * 55)
print(f"Linhas  : {len(df):,}")
print(f"Colunas : {len(df.columns)}")
print(f"Colunas : {list(df.columns)}")


# ─────────────────────────────────────────────────────────────
# 2. Tipos de dados de cada coluna
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("2. TIPOS DE DADOS (dtypes)")
print("=" * 55)
print(df.dtypes.to_string())


# ─────────────────────────────────────────────────────────────
# 3. Primeiras linhas
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("3. PRIMEIRAS 5 LINHAS")
print("=" * 55)
print(df.head().to_string())


# ─────────────────────────────────────────────────────────────
# 4. Valores nulos por coluna
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("4. VALORES NULOS")
print("=" * 55)
nulos = df.isnull().sum()
nulos_pct = (nulos / len(df) * 100).round(2)
resumo_nulos = pd.DataFrame({"nulos": nulos, "pct (%)": nulos_pct})
print(resumo_nulos[resumo_nulos["nulos"] > 0].to_string())

# Colunas sem nulos
sem_nulos = nulos[nulos == 0].index.tolist()
print(f"\nColunas sem nulos: {sem_nulos}")


# ─────────────────────────────────────────────────────────────
# 5. Estatísticas das colunas numéricas
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("5. ESTATÍSTICAS NUMÉRICAS")
print("=" * 55)
print(df.describe().round(2).to_string())


# ─────────────────────────────────────────────────────────────
# 6. Distribuição das colunas categóricas
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("6. COLUNAS CATEGÓRICAS")
print("=" * 55)
categoricas = ["person_home_ownership", "loan_intent", "loan_grade", "cb_person_default_on_file"]
for col in categoricas:
    print(f"\n── {col}")
    print(df[col].value_counts().to_string())


# ─────────────────────────────────────────────────────────────
# 7. Distribuição da variável alvo: loan_status
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("7. VARIÁVEL ALVO: loan_status")
print("=" * 55)
contagem = df["loan_status"].value_counts()
pct = (df["loan_status"].value_counts(normalize=True) * 100).round(1)
print(f"  0 = adimplente  → {contagem[0]:,} registros ({pct[0]}%)")
print(f"  1 = inadimplente → {contagem[1]:,} registros ({pct[1]}%)")


# ─────────────────────────────────────────────────────────────
# 8. Outliers óbvios — problemas que trataremos no passo 3
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("8. OUTLIERS IDENTIFICADOS (a tratar no passo 3)")
print("=" * 55)

# person_age
print(f"\n── person_age")
print(f"   Esperado: 20–80 anos")
print(f"   Max encontrado: {df['person_age'].max()} anos")
print(f"   Registros com age > 80: {(df['person_age'] > 80).sum()}")
print(f"   Registros com age > 80:\n{df[df['person_age'] > 80][['person_age','person_income','loan_status']].to_string()}")

# person_emp_length
print(f"\n── person_emp_length")
print(f"   Esperado: 0–50 anos de emprego")
print(f"   Max encontrado: {df['person_emp_length'].max()} anos")
print(f"   Registros com emp_length > 60: {(df['person_emp_length'] > 60).sum()}")

print("\n" + "=" * 55)
print("PRÓXIMO PASSO: 03_limpeza.py")
print("Problemas encontrados para tratar:")
print("  [CRÍTICO] person_age: outlier máximo = 144")
print("  [CRÍTICO] loan_int_rate: 3116 nulos (9.6%)")
print("  [MÉDIO]   person_emp_length: 895 nulos + outlier = 123")
print("  [MÉDIO]   cb_person_default_on_file: encode 'Y'/'N' → True/False")
print("  [BAIXO]   loan_grade: encoding ordinal A=1 → G=7")
print("=" * 55)
