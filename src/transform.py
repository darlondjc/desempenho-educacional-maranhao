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

df_ma = pd.read_csv('data/raw/ideb_municipios_ma_publico.csv', sep=';', skiprows=0)

# ── TRATAMENTO DE VALORES ESPECIAIS → NaN ───────────────────
# Todos os códigos de não-divulgação do INEP
valores_nulos = ['ND', 'ND*', 'ND***', '(*)', '(**)', '--', '-', '']

anos = ['2019', '2021', '2023']
cols_anos = [col for col in df_ma.columns if any(ano in col for ano in anos)]
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
#print(df_ma.head())
#print(df_ma.info(verbose=True))

# ── DIAGNÓSTICO DE MISSING ─────────────────────────────────────────────────
#print(f"Shape: {df_ma.shape}")
#print(f"Municípios únicos: {df_ma['NO_MUNICIPIO'].nunique()}")
#print("\nPercentual de NaN por coluna:")
#print(df_ma[cols_anos].isna().mean().mul(100).round(1).to_string())


# ── OUTROS DIAGNÓSTICOS ───────────────────────────────────────────────
cols_essenciais = [
    'CO_MUNICIPIO', 'NO_MUNICIPIO',
    'VL_OBSERVADO_2019', 'VL_OBSERVADO_2021', 'VL_OBSERVADO_2023',
    'VL_NOTA_MEDIA_2019', 'VL_NOTA_MEDIA_2021', 'VL_NOTA_MEDIA_2023',
    'VL_INDICADOR_REND_2019', 'VL_INDICADOR_REND_2021', 'VL_INDICADOR_REND_2023',
    'VL_PROJECAO_2019', 'VL_PROJECAO_2021'
]

df_analise = df_ma[cols_essenciais].copy()

# ── CLASSIFICAR DISPONIBILIDADE DE DADOS ─────────────────────────────────────
df_analise['TEM_2019'] = df_analise['VL_OBSERVADO_2019'].notna()
df_analise['TEM_2021'] = df_analise['VL_OBSERVADO_2021'].notna()
df_analise['TEM_2023'] = df_analise['VL_OBSERVADO_2023'].notna()
df_analise['TEM_SERIE_COMPLETA'] = (
    df_analise['TEM_2019'] & df_analise['TEM_2021'] & df_analise['TEM_2023']
)

# ── DIAGNÓSTICO ───────────────────────────────────────────────────────────────
# print("Disponibilidade por ano:")
# print(f"  Com IDEB 2019: {df_analise['TEM_2019'].sum()}")
# print(f"  Com IDEB 2021: {df_analise['TEM_2021'].sum()}")
# print(f"  Com IDEB 2023: {df_analise['TEM_2023'].sum()}")
# print(f"  Série completa (2019+2021+2023): {df_analise['TEM_SERIE_COMPLETA'].sum()}")

# # Distribuição do IDEB 2023 para quem tem dado
# print("\nDistribuição IDEB 2023 (rede municipal):")
# print(df_analise['VL_OBSERVADO_2023'].describe())

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import os

os.makedirs('reports/figures', exist_ok=True)

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle('IDEB 2023 — Rede Municipal — Maranhão', fontsize=13, fontweight='bold')

# Histograma
axes[0].hist(df_analise['VL_OBSERVADO_2023'].dropna(), bins=20,
             color='steelblue', edgecolor='white')
axes[0].axvline(df_analise['VL_OBSERVADO_2023'].mean(), color='red',
                linestyle='--', label=f"Média: {df_analise['VL_OBSERVADO_2023'].mean():.2f}")
axes[0].axvline(6.0, color='orange', linestyle='--', label='Meta nacional: 6.0')
axes[0].set_title('Distribuição IDEB 2023')
axes[0].set_xlabel('IDEB')
axes[0].set_ylabel('Municípios')
axes[0].legend(fontsize=8)

# Evolução média 2019-2021-2023
anos = ['2019', '2021', '2023']
medias = [
    df_analise['VL_OBSERVADO_2019'].mean(),
    df_analise['VL_OBSERVADO_2021'].mean(),
    df_analise['VL_OBSERVADO_2023'].mean()
]
axes[1].plot(anos, medias, marker='o', color='steelblue', linewidth=2)
axes[1].axhline(6.0, color='orange', linestyle='--', label='Meta nacional: 6.0')
for i, (ano, val) in enumerate(zip(anos, medias)):
    axes[1].annotate(f'{val:.2f}', (ano, val),
                     textcoords='offset points', xytext=(0, 10), ha='center')
axes[1].set_title('Evolução da média estadual')
axes[1].set_xlabel('Ano')
axes[1].set_ylabel('IDEB médio')
axes[1].set_ylim(3.5, 7.0)
axes[1].legend(fontsize=8)

# Boxplot comparativo por ano
dados_box = [
    df_analise['VL_OBSERVADO_2019'].dropna(),
    df_analise['VL_OBSERVADO_2021'].dropna(),
    df_analise['VL_OBSERVADO_2023'].dropna()
]
bp = axes[2].boxplot(dados_box, tick_labels=anos, patch_artist=True)
for patch in bp['boxes']:
    patch.set_facecolor('steelblue')
    patch.set_alpha(0.6)
axes[2].axhline(6.0, color='orange', linestyle='--', label='Meta nacional: 6.0')
axes[2].set_title('Dispersão por ano')
axes[2].set_xlabel('Ano')
axes[2].set_ylabel('IDEB')
axes[2].legend(fontsize=8)

plt.tight_layout()
plt.savefig('reports/figures/ideb_ma_distribuicao.png', dpi=150, bbox_inches='tight')
plt.show()
print("Figura salva em reports/figures/")