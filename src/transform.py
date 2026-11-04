import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
TRUSTED_DIR = Path("data/trusted")

# ── TRANSFORMAÇÃO DO IDEB ───────────────────
def transform_indicadores_municipais_ma_ideb_2025():
  df_ideb = pd.read_csv(RAW_DIR / 'indicadores_municipais_ma_ideb_2025.csv', sep=';', skiprows=0)

  # ── TRATAMENTO DE VALORES ESPECIAIS → NaN ───────────────────
  # Todos os códigos de não-divulgação do INEP
  valores_nulos = ['ND', 'ND*', 'ND***', '(*)', '(**)', '--', '-', '']

  anos = '2025'
  cols_anos = [col for col in df_ideb.columns if anos in col]
  cols_numericas = cols_anos  # todas as colunas de ano são candidatas a float

  for col in cols_numericas:
    # Substituir valores especiais por NaN
    df_ideb[col] = df_ideb[col].replace(valores_nulos, np.nan)
    # Remover espaços extras que possam existir
    df_ideb[col] = df_ideb[col].astype(str).str.strip()
    df_ideb[col] = df_ideb[col].replace('nan', np.nan)
    # Converter para float (vírgula → ponto se necessário)
    df_ideb[col] = df_ideb[col].str.replace(',', '.', regex=False)
    df_ideb[col] = pd.to_numeric(df_ideb[col], errors='coerce')

  # Converter CO_MUNICIPIO para int
  df_ideb['CO_MUNICIPIO'] = pd.to_numeric(df_ideb['CO_MUNICIPIO'], errors='coerce').astype('int64')

  # Remover a coluna REDE, pois todos os municípios são da rede municipal
  if 'REDE' in df_ideb.columns:
      df_ideb = df_ideb.drop(columns=['REDE'])

  # Remover a coluna SG_UF, pois todos os municípios são do Maranhão
  if 'SG_UF' in df_ideb.columns:
      df_ideb = df_ideb.drop(columns=['SG_UF'])

  # Remover colunas redundantes de nota (a média já está em VL_NOTA_MEDIA_2025)
  df_ideb = df_ideb.drop(columns=['VL_NOTA_MATEMATICA_2025', 'VL_NOTA_PORTUGUES_2025'], errors='ignore')

  return df_ideb

# ── TRANSFORMAÇÃO DO CENSO ───────────────────
def transform_indicadores_municipais_ma_censo_2025():
  df_censo = pd.read_csv(RAW_DIR / 'indicadores_municipais_ma_censo_escolar_2025.csv', sep=';', skiprows=0)

  # Remover colunas sem nenhum valor preenchido
  df_censo = df_censo.dropna(axis=1, how='all')
  # Remover coluna MEDIA_ALUNOS_POR_TURMA_MED, pois o estudo se baseia somente em EFAI e EFAF
  if 'MEDIA_ALUNOS_POR_TURMA_MED' in df_censo.columns:
      df_censo = df_censo.drop(columns=['MEDIA_ALUNOS_POR_TURMA_MED'])
  # Converter todas as colunas com QT_ para int
  cols_qt = [col for col in df_censo.columns if col.startswith('QT_')]
  for col in cols_qt:
      df_censo[col] = pd.to_numeric(df_censo[col], errors='coerce').astype('int64')

  # Remover a coluna SG_UF, pois todos os municípios são do Maranhão
  if 'SG_UF' in df_censo.columns:
      df_censo = df_censo.drop(columns=['SG_UF'])

  return df_censo

# ── TRANSFORMAÇÃO DO IBGE (RENDA PER CAPITA, CENSO 2022) ───────────────────
def transform_indicadores_municipais_ma_ibge_2022():
  df_ibge = pd.read_csv(RAW_DIR / 'indicadores_municipais_ma_ibge_2022.csv', sep=';', skiprows=0)

  for col in ['RENDA_PER_CAPITA_2022', 'PCT_POBREZA_EXTREMA_2022']:
    df_ibge[col] = pd.to_numeric(df_ibge[col], errors='coerce')

  return df_ibge

def merge_dataframes(df_ideb, df_censo, df_ibge):
  #Normalizar NO_MUNICIPIO para garantir o join correto
  for df in [df_ideb, df_censo, df_ibge]:
      df['NO_MUNICIPIO'] = df['NO_MUNICIPIO'].str.strip().str.upper()

  # Etapa 1: ideb + censo pelo código do município (sem NO_MUNICIPIO do censo)
  censo_cols = df_censo.drop(columns=['NO_MUNICIPIO'])
  df_merged = df_ideb.merge(censo_cols, on='CO_MUNICIPIO', how='left', validate='one_to_one')

  #Etapa 2: merge com IBGE (sem NO_MUNICIPIO do IBGE após o join)
  df_merged = df_merged.merge(df_ibge, on='NO_MUNICIPIO', how='left')

  return df_merged

def main() -> None:
  TRUSTED_DIR.mkdir(parents=True, exist_ok=True)
      
  # ── TRANSFORMAÇÃO DO IDEB ───────────────────
  print("Transformação do IDEB 2025...")
  df_ideb = transform_indicadores_municipais_ma_ideb_2025()
  print(df_ideb.head())

  # ── TRANSFORMAÇÃO DO CENSO ───────────────────
  print("Transformação do CENSO 2025...")
  df_censo = transform_indicadores_municipais_ma_censo_2025()

  # ── TRANSFORMAÇÃO DO IBGE (RENDA PER CAPITA, CENSO 2022) ───────────────────
  print("Transformação da renda e da pobreza extrema — Censo 2022...")
  df_ibge = transform_indicadores_municipais_ma_ibge_2022()
      
  # ── MERGE DOS INDICADORES BASEADO NA COLUNA 'NO_MUNICIPIO' ───────────────────
  print("Realizando merge dos indicadores...")
  df_merged = merge_dataframes(df_ideb, df_censo, df_ibge) 
  print(df_merged.info())
  output_path_trusted = TRUSTED_DIR / "indicadores_municipais_ma.csv"
  df_merged.to_csv(output_path_trusted, index=False, sep=";")

if __name__ == "__main__":
	main()