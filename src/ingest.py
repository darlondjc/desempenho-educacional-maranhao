import pandas as pd

# Carregar o arquivo
df = pd.read_excel('data/raw/divulgacao_anos_iniciais_municipios_2023.xlsx', skiprows=9)

# Filtrar Maranhão e rede pública
df_ma = df[(df['SG_UF'] == 'MA') & (df['REDE'] == 'Municipal')]

# Colunas de identificação (sempre manter)
cols_id = ['SG_UF', 'CO_MUNICIPIO', 'NO_MUNICIPIO', 'REDE']

# Colunas dos anos de interesse (2019, 2021, 2023)
anos = ['2019', '2021', '2023']
cols_anos = [col for col in df_ma.columns if any(ano in col for ano in anos)]

# Selecionar apenas as colunas relevantes
df_ma = df_ma[cols_id + cols_anos]

# Salvar na camada raw
df_ma.to_csv('data/raw/ideb_municipios_ma_publico.csv', index=False, sep=';')

print(f"Shape final: {df_ma.shape}")
print(f"Colunas mantidas: {df_ma.columns.tolist()}")
print(df_ma['NO_MUNICIPIO'].nunique(), 'municípios exportados para data/raw/ideb_municipios_ma_publico.csv')
