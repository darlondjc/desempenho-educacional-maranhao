import pandas as pd
import numpy as np
from pathlib import Path

RAW_DIR = Path("data/raw")
TRUSTED_DIR = Path("data/trusted")

# ── TRANSFORMAÇÃO DO IDEB ───────────────────
def transform_indicadores_municipais_ma_ideb_2023():
  df_ideb = pd.read_csv(RAW_DIR / 'indicadores_municipais_ma_ideb_2023.csv', sep=';', skiprows=0)

  # ── TRATAMENTO DE VALORES ESPECIAIS → NaN ───────────────────
  # Todos os códigos de não-divulgação do INEP
  valores_nulos = ['ND', 'ND*', 'ND***', '(*)', '(**)', '--', '-', '']

  anos = '2023'
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

  # Remover colunas redundantes de nota (a média já está em VL_NOTA_MEDIA_2023)
  df_ideb = df_ideb.drop(columns=['VL_NOTA_MATEMATICA_2023', 'VL_NOTA_PORTUGUES_2023'], errors='ignore')
  
  return df_ideb

# ── TRANSFORMAÇÃO DO CENSO ───────────────────
def transform_indicadores_municipais_ma_censo_2023():
  df_censo = pd.read_csv(RAW_DIR / 'indicadores_municipais_ma_censo_escolar_2023.csv', sep=';', skiprows=0)

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

# ── TRANSFORMAÇÃO DO IBGE ───────────────────
def transform_indicadores_municipais_ma_ibge_2010():
  df_ibge = pd.read_csv(RAW_DIR / 'indicadores_municipais_ma_ibge_2010.csv', sep=';', skiprows=0)

  # Remover linhas completamente vazias
  df_ibge = df_ibge.dropna(how='all')

  # Remover as 3 ultimas linhas
  df_ibge = df_ibge.iloc[:-3]

  # Tratar coluna 'Territorialidades': onde houver (MA) no final, remover e manter apenas o nome do município
  df_ibge['Territorialidades'] = df_ibge['Territorialidades'].str.replace(r'\s*\(MA\)$', '', regex=True).str.strip()
  # Remover a linha onde a Territorialidade for 'Brasil' (linha 0), pois não é um município
  df_ibge = df_ibge[df_ibge['Territorialidades'] != 'Brasil']
  
  # Renomear a coluna 'Territorialidades' para 'NO_MUNICIPIO'
  df_ibge = df_ibge.rename(columns={'Territorialidades': 'NO_MUNICIPIO'})

  # Renomear a coluna 'População urbana 2010' para 'POPULACAO_URBANA_2010'
  df_ibge = df_ibge.rename(columns={'População urbana 2010': 'POPULACAO_URBANA_2010'})

  # Renomear a coluna 'Renda per capita 2010' para 'RENDA_PER_CAPITA_2010'
  df_ibge = df_ibge.rename(columns={'Renda per capita 2010': 'RENDA_PER_CAPITA_2010'})

  # Remover a coluna '% de extremamente pobres 2010'
  if '% de extremamente pobres 2010' in df_ibge.columns:
      df_ibge = df_ibge.drop(columns=['% de extremamente pobres 2010'])

  # Remover a coluna '% de pobres 2010'
  if '% de pobres 2010' in df_ibge.columns:
      df_ibge = df_ibge.drop(columns=['% de pobres 2010'])

  # Converter 'POPULACAO_URBANA_2010' para int
  df_ibge['POPULACAO_URBANA_2010'] = pd.to_numeric(df_ibge['POPULACAO_URBANA_2010'], errors='coerce').astype('int64')

  return df_ibge

# ── TRANSFORMAÇÃO DO IDHM ───────────────────
def transform_indicadores_municipais_ma_idhm_2010():
  df_idhm = pd.read_csv(RAW_DIR / 'indicadores_municipais_ma_idhm_2010.csv', sep=';', skiprows=0)

  # Remover as 3 ultimas linhas
  df_idhm = df_idhm.iloc[:-3]
  
  # Remover a coluna '2000'
  if '2000' in df_idhm.columns:
      df_idhm = df_idhm.drop(columns=['2000'])

  # Renomear a coluna '2010' para 'IDHM_2010'
  df_idhm = df_idhm.rename(columns={'2010': 'IDHM_2010'})

  # Renomear coluna 'Código IBGE' para 'COD_IBGE'
  df_idhm = df_idhm.rename(columns={'Código IBGE': 'COD_IBGE'})

  # Converter 'COD_IBGE' para int 
  df_idhm['COD_IBGE'] = pd.to_numeric(df_idhm['COD_IBGE'], errors='coerce').astype('int64')
  
  # Renomear a coluna 'Município' para 'NO_MUNICIPIO'
  df_idhm = df_idhm.rename(columns={'Município': 'NO_MUNICIPIO'})

  return df_idhm

def merge_dataframes(df_ideb, df_censo, df_ibge, df_idhm):
  #Normalizar NO_MUNICIPIO para garantir o join correto
  for df in [df_ideb, df_censo, df_ibge, df_idhm]:
      df['NO_MUNICIPIO'] = df['NO_MUNICIPIO'].str.strip().str.upper()

  # Etapa 1: ideb + censo (sem CO_MUNICIPIO e NO_MUNICIPIO do censo)
  censo_cols = df_censo.drop(columns=['CO_MUNICIPIO', 'NO_MUNICIPIO'])
  df_merged = df_ideb.merge(censo_cols, left_index=True, right_index=True, how='left')

  #Etapa 2: merge com IBGE (sem NO_MUNICIPIO do IBGE após o join)
  df_merged = df_merged.merge(df_ibge, on='NO_MUNICIPIO', how='left')

  #Etapa 3: merge com IDHM (pegar somente a coluna IDHM_2010)
  df_idhm_reduzido = df_idhm[['NO_MUNICIPIO', 'IDHM_2010']]
  df_merged = df_merged.merge(df_idhm_reduzido, on='NO_MUNICIPIO', how='left')

  return df_merged

def main() -> None:
  TRUSTED_DIR.mkdir(parents=True, exist_ok=True)
      
  # ── TRANSFORMAÇÃO DO IDEB ───────────────────
  print("Transformação do IDEB 2023...")
  df_ideb = transform_indicadores_municipais_ma_ideb_2023()
  print(df_ideb.head())
      
  # ── TRANSFORMAÇÃO DO CENSO ───────────────────
  print("Transformação do CENSO 2023...")
  df_censo = transform_indicadores_municipais_ma_censo_2023()
      
  # ── TRANSFORMAÇÃO DO IBGE ───────────────────
  print("Transformação do IBGE 2010...")
  df_ibge = transform_indicadores_municipais_ma_ibge_2010()
      
  # ── TRANSFORMAÇÃO DO IDHM ───────────────────
  print("Transformação do IDHM 2010...")
  df_idhm = transform_indicadores_municipais_ma_idhm_2010()
  print(df_idhm.info())

  # ── MERGE DOS INDICADORES BASEADO NA COLUNA 'NO_MUNICIPIO' ───────────────────
  print("Realizando merge dos indicadores...")
  df_merged = merge_dataframes(df_ideb, df_censo, df_ibge, df_idhm) 
  print(df_merged.info())
  output_path_trusted = TRUSTED_DIR / "indicadores_municipais_ma.csv"
  df_merged.to_csv(output_path_trusted, index=False, sep=";")

if __name__ == "__main__":
	main()