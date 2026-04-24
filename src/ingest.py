import pandas as pd
# """ 
# # Carregar o arquivo
# df = pd.read_excel('data/base/divulgacao_anos_iniciais_municipios_2023.xlsx', skiprows=9)

# # Filtrar Maranhão e rede pública
# df_ma = df[(df['SG_UF'] == 'MA') & (df['REDE'] == 'Municipal')]

# # Colunas de identificação (sempre manter)
# cols_id = ['SG_UF', 'CO_MUNICIPIO', 'NO_MUNICIPIO', 'REDE']

# # Colunas dos anos de interesse (2023)
# anos = '2023'
# cols_anos = [col for col in df_ma.columns if anos in col]

# # Selecionar apenas as colunas relevantes
# df_ma = df_ma[cols_id + cols_anos]

# # Salvar na camada raw
# df_ma.to_csv('data/raw/ideb_municipios_ma.csv', index=False, sep=';')

# print(f"Shape final: {df_ma.shape}")
# print(f"Colunas mantidas: {df_ma.columns.tolist()}")
# print(df_ma['NO_MUNICIPIO'].nunique(), 'municípios exportados para data/raw/ideb_municipios_ma.csv') """


# Carregar o arquivo
df = pd.read_excel('data/base/Sinopse_Estatistica_da_Educacao_Basica_2023.ods', skiprows=0)

print(df.head())
