# ============================================================
# Passo 3 — Limpeza de dados
# Projeto: Análise de Inadimplência | BancoX
# ============================================================
# Problemas identificados no passo 2:
#
#   [CRÍTICO] person_age: outliers com 84, 94, 123 e 144 anos
#   [CRÍTICO] loan_int_rate: 3116 nulos (9.6%)
#   [MÉDIO]   person_emp_length: 2 outliers + 895 nulos
#   [MÉDIO]   cb_person_default_on_file: 'Y'/'N' → boolean
#   [BAIXO]   loan_grade: texto ordinal, útil virar numérico
#
# Estratégias:
#   • Outliers de idade e tempo de emprego → remover as linhas
#     (são erros de digitação, não têm como imputar)
#   • loan_int_rate nulos → mediana por loan_grade
#     (correlação 0.934 entre grade e taxa — imputar por grupo é
#      muito mais preciso que a mediana global)
#   • person_emp_length nulos → mediana global
#     (variação entre grupos é mínima: 3–5 anos)
# ============================================================

import pandas as pd

CAMINHO_CSV    = "credit_risk_dataset.csv"   # ajuste para o caminho do seu arquivo
CAMINHO_SAIDA  = "credit_risk_clean.csv"     # será salvo na mesma pasta do script


# ─────────────────────────────────────────────────────────────
# 1. Carregar
# ─────────────────────────────────────────────────────────────
df = pd.read_csv(CAMINHO_CSV)
total_original = len(df)

print("=" * 55)
print("DATASET ORIGINAL")
print("=" * 55)
print(f"Linhas  : {total_original:,}")
print(f"Nulos   : loan_int_rate={df['loan_int_rate'].isnull().sum()} | "
      f"person_emp_length={df['person_emp_length'].isnull().sum()}")


# ─────────────────────────────────────────────────────────────
# 2. Remover outliers de person_age
#    Critério: > 80 anos (claramente erros de digitação)
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("TRATAMENTO 1 — person_age: remover outliers > 80")
print("=" * 55)

mascara_age = df["person_age"] > 80
print(f"Registros removidos: {mascara_age.sum()}")
print(df[mascara_age][["person_age", "person_income", "person_emp_length"]].to_string())

df = df[~mascara_age].copy()
print(f"\nLinhas restantes: {len(df):,}")


# ─────────────────────────────────────────────────────────────
# 3. Remover outliers de person_emp_length
#    Critério: > 60 anos (ninguém trabalha 123 anos)
#    Feito ANTES de imputar os nulos para não contaminar
#    a mediana com valores absurdos
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("TRATAMENTO 2 — person_emp_length: remover outliers > 60")
print("=" * 55)

mascara_emp = df["person_emp_length"] > 60
print(f"Registros removidos: {mascara_emp.sum()}")
print(df[mascara_emp][["person_age", "person_emp_length", "person_income"]].to_string())

df = df[~mascara_emp].copy()
print(f"\nLinhas restantes: {len(df):,}")


# ─────────────────────────────────────────────────────────────
# 4. Imputar loan_int_rate com mediana por loan_grade
#    Estratégia: calcular mediana dentro de cada grupo A–G
#    e preencher apenas os nulos
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("TRATAMENTO 3 — loan_int_rate: imputar mediana por grade")
print("=" * 55)

nulos_antes = df["loan_int_rate"].isnull().sum()

# Calcular mediana por grupo e aplicar apenas onde é nulo
mediana_por_grade = df.groupby("loan_grade")["loan_int_rate"].transform("median")
df["loan_int_rate"] = df["loan_int_rate"].fillna(mediana_por_grade)

nulos_depois = df["loan_int_rate"].isnull().sum()
print(f"Nulos antes : {nulos_antes}")
print(f"Nulos depois: {nulos_depois}")
print("\nMediana usada por grau:")
medianas = df.groupby("loan_grade")["loan_int_rate"].median().round(2)
for grade, mediana in medianas.items():
    print(f"   Grau {grade}: {mediana}%")


# ─────────────────────────────────────────────────────────────
# 5. Imputar person_emp_length com mediana global
#    Variação entre grupos (RENT/OWN/MORTGAGE) é de 3–5 anos
#    → mediana global é suficiente
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("TRATAMENTO 4 — person_emp_length: imputar mediana global")
print("=" * 55)

nulos_antes = df["person_emp_length"].isnull().sum()
mediana_emp = df["person_emp_length"].median()

df["person_emp_length"] = df["person_emp_length"].fillna(mediana_emp)

nulos_depois = df["person_emp_length"].isnull().sum()
print(f"Mediana usada : {mediana_emp} anos")
print(f"Nulos antes   : {nulos_antes}")
print(f"Nulos depois  : {nulos_depois}")


# ─────────────────────────────────────────────────────────────
# 6. Encode cb_person_default_on_file: 'Y'/'N' → True/False
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("TRATAMENTO 5 — cb_person_default_on_file: 'Y'/'N' → bool")
print("=" * 55)

print("Antes:", df["cb_person_default_on_file"].value_counts().to_dict())
df["cb_person_default_on_file"] = df["cb_person_default_on_file"].map({"Y": True, "N": False})
print("Depois:", df["cb_person_default_on_file"].value_counts().to_dict())


# ─────────────────────────────────────────────────────────────
# 7. Encoding ordinal de loan_grade → grau_risco_num
#    A (melhor crédito) = 1  →  G (pior crédito) = 7
#    Útil para correlações e gráficos de dispersão
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("TRATAMENTO 6 — loan_grade: adicionar encoding ordinal")
print("=" * 55)

grade_map = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7}
df["grau_risco_num"] = df["loan_grade"].map(grade_map)
print("loan_grade → grau_risco_num:")
print(df[["loan_grade", "grau_risco_num"]].drop_duplicates().sort_values("grau_risco_num").to_string(index=False))


# ─────────────────────────────────────────────────────────────
# 8. Reset index (os índices ficaram com gaps após os drops)
# ─────────────────────────────────────────────────────────────
df = df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# 9. Validação final
# ─────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("VALIDAÇÃO FINAL")
print("=" * 55)

nulos_restantes = df.isnull().sum()
print("Nulos restantes por coluna:")
print(nulos_restantes[nulos_restantes > 0] if nulos_restantes.sum() > 0 else "  Nenhum nulo restante!")

print(f"\nLinhas originais : {total_original:,}")
print(f"Linhas removidas : {total_original - len(df):,}  ({(total_original - len(df)) / total_original * 100:.2f}%)")
print(f"Linhas finais    : {len(df):,}")

print("\nEstatísticas pós-limpeza (colunas tratadas):")
print(df[["person_age", "person_emp_length", "loan_int_rate"]].describe().round(2).to_string())


# ─────────────────────────────────────────────────────────────
# 10. Salvar dataset limpo
# ─────────────────────────────────────────────────────────────
df.to_csv(CAMINHO_SAIDA, index=False)

print("\n" + "=" * 55)
print(f"Arquivo salvo: {CAMINHO_SAIDA}")
print("PRÓXIMO PASSO: 04_adaptar_schema.py")
print("=" * 55)
