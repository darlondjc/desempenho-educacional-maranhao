from pathlib import Path
import pandas as pd

BASE_DIR = Path("data/base")
RAW_DIR = Path("data/raw")

# ── INGESTÃO DO IDEB ───────────────────
def build_indicadores_municipais_ma_ideb_2023():
	df = pd.read_excel(BASE_DIR / 'divulgacao_anos_iniciais_municipios_2023.xlsx', skiprows=9)
	df_ma = df[(df['SG_UF'] == 'MA') & (df['REDE'] == 'Municipal')]
	cols_id = ['SG_UF', 'CO_MUNICIPIO', 'NO_MUNICIPIO', 'REDE']
	anos = '2023'
	cols_anos = [col for col in df_ma.columns if anos in col]
	df_ma = df_ma[cols_id + cols_anos]

	return df_ma

# ── INGESTÃO DO CENSO ESCOLAR 2023 ───────────────────
def safe_divide(numerator: pd.Series, denominator: pd.Series, factor: float = 1.0) -> pd.Series:
	denominator = denominator.replace(0, pd.NA)
	return (numerator / denominator) * factor


def normalize_municipio_code(series: pd.Series) -> pd.Series:
	return pd.to_numeric(series, errors="coerce").astype("Int64").astype("string")


def resolve_censo_path() -> Path:
	path_censo_escolar = Path("data/base/microdados_censo_escolar_2023/dados/microdados_ed_basica_2023.csv")
	if path_censo_escolar.exists():
		return path_censo_escolar
	raise FileNotFoundError("Arquivo de microdados do Censo Escolar não encontrado em data/base.")


def load_censo_microdados() -> pd.DataFrame:
	censo_path = resolve_censo_path()
	usecols = [
		"SG_UF",
		"NO_MUNICIPIO",
		"CO_MUNICIPIO",
		"TP_DEPENDENCIA",
		"CO_ENTIDADE",
		"IN_INTERNET",
		"IN_BIBLIOTECA",
		"IN_BIBLIOTECA_SALA_LEITURA",
		"IN_SALA_LEITURA",
		"IN_LABORATORIO_INFORMATICA",
		"IN_QUADRA_ESPORTES",
		"IN_AGUA_POTAVEL",
		"IN_AGUA_REDE_PUBLICA",
		"IN_ESGOTO_REDE_PUBLICA",
		"IN_ESGOTO_FOSSA_SEPTICA",
		"QT_DOC_BAS",
		"QT_DOC_BAS_ESCO_SUP_GRAD",
		"QT_DOC_BAS_ESCO_SUP_GRAD_LICEN",
		"QT_MAT_BAS",
		"QT_MAT_FUND",
		"QT_MAT_MED",
		"QT_MAT_BAS_15_17",
		"QT_MAT_BAS_18_MAIS",
		"QT_TUR_BAS",
		"QT_TUR_FUND",
		"QT_TUR_MED",
		"QT_TUR_FUND_AF",
		"QT_TUR_FUND_AF_CORRFLUXO",
	]
	return pd.read_csv(
		censo_path,
		sep=";",
		low_memory=False,
		encoding="latin1",
		usecols=lambda c: c in usecols,
	)


def ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
	for col in columns:
		if col not in df.columns:
			df[col] = 0
	return df


def build_indicadores_municipais_ma_censo_escolar_2023() -> pd.DataFrame:
	censo = load_censo_microdados()
	has_doc_sup = "QT_DOC_BAS_ESCO_SUP_GRAD" in censo.columns
	has_doc_lic = "QT_DOC_BAS_ESCO_SUP_GRAD_LICEN" in censo.columns
	has_corrfluxo = "QT_TUR_FUND_AF_CORRFLUXO" in censo.columns
	censo = ensure_columns(
		censo,
		[
			"QT_DOC_BAS_ESCO_SUP_GRAD",
			"QT_DOC_BAS_ESCO_SUP_GRAD_LICEN",
			"QT_TUR_FUND_AF",
			"QT_TUR_FUND_AF_CORRFLUXO",
		],
	)

	# Foco em rede municipal no Maranhão.
	censo = censo[(censo["SG_UF"] == "MA") & (censo["TP_DEPENDENCIA"] == 3)].copy()
	censo["CO_MUNICIPIO"] = normalize_municipio_code(censo["CO_MUNICIPIO"])

	censo["IN_BIBLIOTECA_OU_LEITURA"] = (
		(censo["IN_BIBLIOTECA"].fillna(0) == 1)
		| (censo["IN_BIBLIOTECA_SALA_LEITURA"].fillna(0) == 1)
		| (censo["IN_SALA_LEITURA"].fillna(0) == 1)
	).astype(int)
	censo["IN_AGUA_ADEQUADA"] = (
		(censo["IN_AGUA_POTAVEL"].fillna(0) == 1)
		| (censo["IN_AGUA_REDE_PUBLICA"].fillna(0) == 1)
	).astype(int)
	censo["IN_ESGOTO_ADEQUADO"] = (
		(censo["IN_ESGOTO_REDE_PUBLICA"].fillna(0) == 1)
		| (censo["IN_ESGOTO_FOSSA_SEPTICA"].fillna(0) == 1)
	).astype(int)

	indicadores = (
		censo.groupby("CO_MUNICIPIO", as_index=False)
		.agg(
			SG_UF=("SG_UF", "first"),
			NO_MUNICIPIO=("NO_MUNICIPIO", "first"),
			QT_ESCOLAS=("CO_ENTIDADE", "nunique"),
			PCT_ESCOLAS_COM_INTERNET=("IN_INTERNET", "mean"),
			PCT_ESCOLAS_COM_BIBLIOTECA_LEITURA=("IN_BIBLIOTECA_OU_LEITURA", "mean"),
			PCT_ESCOLAS_COM_LAB_INFORMATICA=("IN_LABORATORIO_INFORMATICA", "mean"),
			PCT_ESCOLAS_COM_QUADRA=("IN_QUADRA_ESPORTES", "mean"),
			PCT_ESCOLAS_COM_AGUA_ADEQUADA=("IN_AGUA_ADEQUADA", "mean"),
			PCT_ESCOLAS_COM_ESGOTO_ADEQUADO=("IN_ESGOTO_ADEQUADO", "mean"),
			QT_DOC_BAS=("QT_DOC_BAS", "sum"),
			QT_DOC_BAS_ESCO_SUP_GRAD=("QT_DOC_BAS_ESCO_SUP_GRAD", "sum"),
			QT_DOC_BAS_ESCO_SUP_GRAD_LICEN=("QT_DOC_BAS_ESCO_SUP_GRAD_LICEN", "sum"),
			QT_MAT_BAS=("QT_MAT_BAS", "sum"),
			QT_MAT_FUND=("QT_MAT_FUND", "sum"),
			QT_MAT_MED=("QT_MAT_MED", "sum"),
			QT_MAT_BAS_15_17=("QT_MAT_BAS_15_17", "sum"),
			QT_MAT_BAS_18_MAIS=("QT_MAT_BAS_18_MAIS", "sum"),
			QT_TUR_BAS=("QT_TUR_BAS", "sum"),
			QT_TUR_FUND=("QT_TUR_FUND", "sum"),
			QT_TUR_MED=("QT_TUR_MED", "sum"),
			QT_TUR_FUND_AF=("QT_TUR_FUND_AF", "sum"),
			QT_TUR_FUND_AF_CORRFLUXO=("QT_TUR_FUND_AF_CORRFLUXO", "sum"),
		)
		.assign(
			PCT_ESCOLAS_COM_INTERNET=lambda x: x["PCT_ESCOLAS_COM_INTERNET"] * 100,
			PCT_ESCOLAS_COM_BIBLIOTECA_LEITURA=lambda x: x["PCT_ESCOLAS_COM_BIBLIOTECA_LEITURA"] * 100,
			PCT_ESCOLAS_COM_LAB_INFORMATICA=lambda x: x["PCT_ESCOLAS_COM_LAB_INFORMATICA"] * 100,
			PCT_ESCOLAS_COM_QUADRA=lambda x: x["PCT_ESCOLAS_COM_QUADRA"] * 100,
			PCT_ESCOLAS_COM_AGUA_ADEQUADA=lambda x: x["PCT_ESCOLAS_COM_AGUA_ADEQUADA"] * 100,
			PCT_ESCOLAS_COM_ESGOTO_ADEQUADO=lambda x: x["PCT_ESCOLAS_COM_ESGOTO_ADEQUADO"] * 100,
		)
	)

	if has_doc_sup:
		indicadores["PCT_DOC_SUPERIOR_COMPLETO"] = safe_divide(
			indicadores["QT_DOC_BAS_ESCO_SUP_GRAD"], indicadores["QT_DOC_BAS"], factor=100
		)
	else:
		indicadores["PCT_DOC_SUPERIOR_COMPLETO"] = pd.NA

	# Proxy de formação específica: participação de licenciatura no total de docentes.
	if has_doc_lic:
		indicadores["PCT_DOC_LICENCIATURA_TOTAL"] = safe_divide(
			indicadores["QT_DOC_BAS_ESCO_SUP_GRAD_LICEN"], indicadores["QT_DOC_BAS"], factor=100
		)
	else:
		indicadores["PCT_DOC_LICENCIATURA_TOTAL"] = pd.NA

	indicadores["MEDIA_ALUNOS_POR_TURMA_BAS"] = safe_divide(
		indicadores["QT_MAT_BAS"], indicadores["QT_TUR_BAS"]
	)
	indicadores["MEDIA_ALUNOS_POR_TURMA_FUND"] = safe_divide(
		indicadores["QT_MAT_FUND"], indicadores["QT_TUR_FUND"]
	)
	indicadores["MEDIA_ALUNOS_POR_TURMA_MED"] = safe_divide(
		indicadores["QT_MAT_MED"], indicadores["QT_TUR_MED"]
	)

	# Proxy 1 para distorção idade-série: alunos de 15+ na educação básica municipal.
	indicadores["PCT_MAT_15_ANOS_OU_MAIS_PROXY_DISTSERIE"] = safe_divide(
		indicadores["QT_MAT_BAS_15_17"] + indicadores["QT_MAT_BAS_18_MAIS"],
		indicadores["QT_MAT_BAS"],
		factor=100,
	)
	# Proxy 2 para distorção (quando disponível): correção de fluxo no fundamental AF.
	if has_corrfluxo:
		indicadores["PCT_TURMAS_CORRFLUXO_FUND_AF"] = safe_divide(
			indicadores["QT_TUR_FUND_AF_CORRFLUXO"], indicadores["QT_TUR_FUND_AF"], factor=100
		)
	else:
		indicadores["PCT_TURMAS_CORRFLUXO_FUND_AF"] = pd.NA

	ideb_path = RAW_DIR / "ideb_municipios_ma_publico.csv"
	if ideb_path.exists():
		ideb = pd.read_csv(ideb_path, sep=";", low_memory=False)
		ideb["CO_MUNICIPIO"] = normalize_municipio_code(ideb["CO_MUNICIPIO"])

		# Proxy para abandono: não aprovação anual no IDEB.
		aprovacao_col = "VL_APROVACAO_2023_SI"
		if aprovacao_col in ideb.columns:
			ideb[aprovacao_col] = pd.to_numeric(ideb[aprovacao_col], errors="coerce")
			ideb["PCT_NAO_APROVACAO_PROXY_2023"] = 100 - ideb[aprovacao_col]
			indicadores = indicadores.merge(
				ideb[["CO_MUNICIPIO", "PCT_NAO_APROVACAO_PROXY_2023"]],
				on="CO_MUNICIPIO",
				how="left",
			)

	return indicadores


def main() -> None:
	RAW_DIR.mkdir(parents=True, exist_ok=True)

	# ── INGESTÃO DO IDEB ───────────────────
	print("Iniciando ingestão do IDEB 2023...")
	indicadores_ideb = build_indicadores_municipais_ma_ideb_2023()
	output_path_ideb = RAW_DIR / "indicadores_municipais_ma_ideb_2023.csv"
	indicadores_ideb.to_csv(output_path_ideb, index=False, sep=";")

	print(f"Arquivo gerado: {output_path_ideb}")
	print(f"Linhas: {len(indicadores_ideb)}")
	print(f"Colunas: {len(indicadores_ideb.columns)}")

	# ── INGESTÃO DO CENSO ESCOLAR 2023 ───────────────────	
	print("Iniciando ingestão do Censo Escolar 2023...")
	indicadores_censo_escolar = build_indicadores_municipais_ma_censo_escolar_2023()
	output_path_censo_escolar = RAW_DIR / "indicadores_municipais_ma_censo_escolar_2023.csv"
	indicadores_censo_escolar.to_csv(output_path_censo_escolar, index=False, sep=";")

	print(f"Arquivo gerado: {output_path_censo_escolar}")
	print(f"Linhas: {len(indicadores_censo_escolar)}")
	print(f"Colunas: {len(indicadores_censo_escolar.columns)}")


if __name__ == "__main__":
	main()

