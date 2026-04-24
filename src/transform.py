"""
Transformação de Dados (transform.py)
=========================================
Responsável por fazer a limpeza dos dados da camada RAW para a camada TRUSTED.
Um exemplo dessa etapa é a estratégia EPA (exploração, polimento e análise de anomalias)

REGRAS:
  - Este script deve ser IDEMPOTENTE (rodar várias vezes sem duplicar dados).
  - Credenciais vêm do .env, nunca hardcoded aqui.
  - Saída: data/trusted/<nome_arquivo>.<extensão>
"""
import pandas as pd
import numpy as np

df_ma = pd.read_csv('data/raw/ideb_municipios_ma.csv', sep=';', skiprows=0)

# ── TRATAMENTO DE VALORES ESPECIAIS → NaN ───────────────────
# Todos os códigos de não-divulgação do INEP
valores_nulos = ['ND', 'ND*', 'ND***', '(*)', '(**)', '--', '-', '']

anos = '2023'
cols_anos = [col for col in df_ma.columns if anos in col]
cols_numericas = cols_anos  # todas as colunas de ano são candidatas a float

for col in cols_numericas:
    # Substituir valores especiais por NaN
    df_ma[col] = df_ma[col].replace(valores_nulos, np.nan)
    # Remover espaços extras que possam existir
    df_ma[col] = df_ma[col].astype(str).str.strip()
    df_ma[col] = df_ma[col].replace('nan', np.nan)
    # Converter para float (vírgula → ponto se necessário)
    df_ma[col] = df_ma[col].str.replace(',', '.', regex=False)
    df_ma[col] = pd.to_numeric(df_ma[col], errors='coerce')

#exploração
print(df_ma.head())
print(df_ma.info(verbose=True))

# ── DIAGNÓSTICO DE MISSING ─────────────────────────────────────────────────
#print(f"Shape: {df_ma.shape}")
#print(f"Municípios únicos: {df_ma['NO_MUNICIPIO'].nunique()}")
#print("\nPercentual de NaN por coluna:")
#print(df_ma[cols_anos].isna().mean().mul(100).round(1).to_string())
