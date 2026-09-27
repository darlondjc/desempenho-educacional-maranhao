# Atualização da base de dados para Ideb/Censo Escolar 2025 — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (recommended for this plan) or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trocar a edição de dados do artigo/dissertação de Ideb 2023 + Censo Escolar 2023 para Ideb 2025 + Censo Escolar 2025, atualizar a renda per capita municipal de 2010 para o Censo Demográfico 2022 (dado por município já disponível via SIDRA), manter o IDHM em 2010 (sem edição por município mais recente — ver justificativa abaixo), e propagar os novos números para o pipeline de análise e para o texto do artigo em LaTeX.

**Architecture:** Pipeline ETL existente em três zonas (`data/base` → `data/raw` → `data/trusted`), scripts `src/ingest.py` → `src/transform.py` → `src/analytics.py`/`analytics.ipynb`. Este plano troca as fontes de 2023 por 2025 nas mesmas funções, renomeando sufixos de ano e colunas dependentes, sem alterar a arquitetura do pipeline. Ao final, os números do artigo (`artigo/*.tex`) são reescritos a partir da nova saída do notebook.

**Tech Stack:** Python 3.12, pandas, scikit-learn, scipy, matplotlib, Jupyter (via `uv run`), LaTeX (abntex2/pdflatex + biblatex).

**Spec:** Não há spec formal separada; a decisão foi tomada na conversa com o usuário em 2026-09-27 (usuário confirmou tempo disponível para refazer a análise completa com Ideb 2025 e Censo Escolar 2025).

## Global Constraints

- Não alterar a arquitetura do pipeline (três zonas de dados, três scripts). Apenas trocar fonte/ano e propagar renomeações.
- **IDHM permanece em 2010.** Confirmado por pesquisa web em 2026-09-27: a extensão do Atlas Brasil (PNUD/Ipea/FJP) para 2022-2024 usa a PNAD Contínua, e a nota técnica do IBGE ("Estimativas para estratos de Municípios na PNAD Contínua", nota técnica 01/2022) é explícita — essa base desagrega os indicadores em apenas **146 estratos de municípios** para o Brasil inteiro, não por município individual. Um valor "2022" mostrado para um município pequeno no Atlas é, na prática, o valor do estrato (grupo de municípios vizinhos), não um dado específico daquele município. Para um estudo que depende de diferenciar 217 municípios um do outro, isso não serve. O IDHM genuinamente por município mais recente continua sendo o de 2010.
- **Renda per capita é atualizada para o Censo Demográfico 2022** (decisão confirmada com o usuário em 2026-09-27). Diferente do IDHM, a renda per capita 2022 vem do Censo Demográfico (contagem completa, não amostra da PNAD) e tem granularidade individual por município. Fonte confirmada e testada nesta sessão: SIDRA, tabela 10295 ("Moradores em domicílios particulares permanentes ocupados (...), valor do rendimento domiciliar mensal per capita, médio e mediano, por sexo, cor ou raça e grupos de idade"), variável 13431 ("Valor do rendimento nominal médio mensal domiciliar per capita"), nível territorial N6 (município), período 2022. Query testada via API pública do IBGE retornou os 217 municípios do Maranhão sem nenhum valor ausente:
  ```
  https://servicodados.ibge.gov.br/api/v3/agregados/10295/periodos/2022/variaveis/13431?localidades=N6[N3[21]]&classificacao=2[6794]|86[95251]|58[95253]
  ```
  (URL acima com `[`/`]`/`|` literais; ao chamar via `curl`, usar as versões percent-encoded `%5B`/`%5D`/`%7C` — o shell do sandbox desta sessão falhou silenciosamente com os caracteres literais.)
- Isso cria um descompasso proposital de anos entre as duas variáveis do espaço de segmentação socioeconômica (renda 2022, IDHM 2010). A Task 5 (artigo) inclui um parágrafo explícito justificando esse descompasso — não é inconsistência, é "cada variável na edição mais recente disponível com granularidade municipal para ela".
- Este projeto não tem framework de testes (`pytest`/`unittest`) nem `tests/` (confirmado em `.planning/codebase/TESTING.md`). A verificação de cada etapa segue a convenção já estabelecida no projeto: prints de shape/contagem em `main()`, mais a execução do notebook via `nbconvert` como teste de integração de ponta a ponta. Não introduzir `pytest` agora (YAGNI) — não é isso que o usuário pediu.
- Seeds `random_state=42` em todos os algoritmos devem ser preservados (reprodutibilidade), mesmo com os novos dados.
- `git status` deve ser checado antes de qualquer commit; os PDFs em `artigo/submissao/` e `artigo/documentos/` não devem ser sobrescritos sem confirmação, pois representam a versão em revisão com a orientadora.

## Review Focus

- **Formato do Censo Escolar 2025 mudou de colunas:** o Inep já alterou nomenclatura de colunas do Censo Escolar entre edições no passado (ex.: `IN_BIBLIOTECA_SALA_LEITURA` foi adicionada depois). A Task 2 confere `usecols` contra o dicionário de dados 2025 antes de assumir que os nomes são idênticos aos de 2023.
- **Sinopse Estatística 2025 pode não ter a Tabela 2.23 no mesmo número/aba.** A Task 2 abre a planilha e localiza a tabela de docentes EFAI por formação antes de hardcodar `skiprows=10` e nomes de coluna.
- **Divulgação do Ideb 2025 pode não ter o sufixo `_2025` nos nomes de coluna no mesmo padrão de 2023** (ex.: pode vir como `VL_OBSERVADO_2025` ou apenas `VL_OBSERVADO`). A Task 2 imprime `df.columns` antes de filtrar.
- **Municípios com "ND" em 2025 podem diferir dos de 2023** (escolas que não tiveram Saeb aplicado, mínimo de alunos não atingido etc.) — o total de 217 municípios com dado completo pode cair. A Task 4 verifica e reporta a contagem final antes de escrever os números no artigo.
- **IDEB 2025 não tem metas oficiais estabelecidas** (edições 2023 e 2025 são excepcionais nesse ponto, conforme nota técnica do Inep) — isso não afeta o pipeline (a análise não usa metas), mas vale registrar caso apareça nos dados brutos como coluna vazia.
- **A tabela/variável do SIDRA usada para renda per capita 2022 (10295/13431) pode ser descontinuada ou renumerada pelo IBGE no futuro.** A Task 1 salva a resposta da API como arquivo em `data/base/` (não depende de chamada de rede em tempo de execução do pipeline), então uma mudança futura na API não quebra a reprodutibilidade retroativa, mas o comando de download documentado no plano pode parar de funcionar se for repetido depois. Isso é aceitável — o dado salvo é o que importa para este artigo.

---

## Fase A — Dados

### Task 1: Baixar as fontes de dados 2025

**Files:**
- Create: `data/base/divulgacao_anos_iniciais_municipios_2025.xlsx` (Ideb 2025)
- Create: `data/base/microdados_censo_escolar_2025/` (Censo Escolar 2025, extraído do zip)
- Create: `data/base/microdados_censo_escolar_2025/dados/docentes_2025.ods` (Sinopse Estatística 2025, Tabela de docentes EFAI por formação)

**Interfaces:**
- Produces: os três arquivos brutos que a Task 2 vai ler.

- [ ] **Passo 1: Baixar o Censo Escolar 2025 (microdados)**

URL confirmada por `curl -Isk` em 2026-09-27 (retorna `200 OK`, `Content-Length: 537217189`, `Last-Modified: 31 Jul 2026`):

```bash
mkdir -p data/base/microdados_censo_escolar_2025
curl -k -o /tmp/microdados_censo_escolar_2025.zip \
  "https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_2025_.zip"
unzip -o /tmp/microdados_censo_escolar_2025.zip -d data/base/microdados_censo_escolar_2025
```

O `-k` é necessário porque o certificado de `download.inep.gov.br` não é validado pela CA bundle padrão do sistema (erro `unable to get local issuer certificate` confirmado nesta sessão) — isso é um problema conhecido de sites `.gov.br`, não um alerta de phishing.

- [ ] **Passo 2: Localizar o CSV de microdados da escola dentro do zip extraído**

```bash
find data/base/microdados_censo_escolar_2025 -iname "microdados_ed_basica_2025.csv"
```

Se o nome do arquivo dentro do zip 2025 for diferente de `microdados_ed_basica_2025.csv`, anotar o nome real — ele será usado na Task 2 (`resolve_censo_path`).

- [ ] **Passo 3: Baixar a planilha de divulgação do Ideb 2025 por município**

O padrão de URL de 2023 (`download.inep.gov.br/ideb/resultados/divulgacao_anos_iniciais_municipios_2023.xlsx`) retornou 404 para 2025 nesta sessão. Antes de seguir, navegar manualmente (ou via `WebFetch`) em `https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados`, clicar em "Ideb e Saeb 2025 – Confira os resultados" → "Ideb Resultados" → modalidade "Município", e capturar a URL real do arquivo (xlsx ou ods) para o Maranhão/anos iniciais/rede municipal. Salvar em `data/base/divulgacao_anos_iniciais_municipios_2025.xlsx` (ou `.ods`, ajustando a leitura na Task 2 conforme o formato real).

- [ ] **Passo 4: Baixar a Sinopse Estatística da Educação Básica 2025 (tabela de docentes EFAI por formação)**

Em `https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-basica`, localizar a edição 2025 e a tabela equivalente à "Tabela 2.23" de 2023 (docentes dos anos iniciais do fundamental por nível de formação, por município). O número da tabela pode ter mudado — abrir o sumário da planilha ODS/XLSX 2025 e confirmar antes de salvar como `data/base/microdados_censo_escolar_2025/dados/docentes_2025.ods`.

- [ ] **Passo 5: Verificar tamanhos e integridade**

```bash
du -sh data/base/divulgacao_anos_iniciais_municipios_2025.xlsx
du -sh data/base/microdados_censo_escolar_2025
ls data/base/microdados_censo_escolar_2025/dados/
```

Esperado: o CSV de microdados deve ter uma linha por escola do Brasil (em 2023 eram ~224 mil linhas no arquivo bruto antes do filtro por UF); o zip completo (dados + dicionário) deve ficar perto de 500 MB.

- [ ] **Passo 6: Baixar a renda per capita municipal do Censo Demográfico 2022 (IBGE/SIDRA)**

Fonte confirmada nesta sessão: tabela SIDRA 10295, variável 13431, nível município (N6), período 2022, filtrando os municípios do Maranhão (UF 21). Salvar a resposta bruta da API como arquivo em `data/base` (zona de landing, igual às outras fontes):

```bash
curl -sk "https://servicodados.ibge.gov.br/api/v3/agregados/10295/periodos/2022/variaveis/13431?localidades=N6%5BN3%5B21%5D%5D&classificacao=2%5B6794%5D%7C86%5B95251%5D%7C58%5B95253%5D" \
  -o data/base/renda_per_capita_censo2022_ma.json
```

Se o `curl` falhar silenciosamente com os caracteres `[`/`]`/`|` literais (aconteceu nesta sessão), usar a versão com `%5B`/`%5D`/`%7C` acima — já testada e funcionando.

- [ ] **Passo 7: Verificar o arquivo baixado**

```bash
uv run python -c "
import json
d = json.load(open('data/base/renda_per_capita_censo2022_ma.json'))
series = d[0]['resultados'][0]['series']
print('Municípios:', len(series))
print(series[0])
"
```

Esperado: `Municípios: 217`, sem nenhum valor ausente (confirmado nesta sessão — nenhum município do Maranhão tem valor suprimido nessa tabela).

---

## Fase B — Ingestão (`src/ingest.py`)

### Task 2: Apontar `ingest.py` para as fontes de 2025 (e a renda per capita para 2022)

**Files:**
- Modify: `src/ingest.py` (linhas 8-16, 33, 78-134, 136-262, 265-268, 279-330)

**Interfaces:**
- Consumes: os arquivos criados na Task 1.
- Produces: `data/raw/indicadores_municipais_ma_ideb_2025.csv`, `data/raw/indicadores_municipais_ma_censo_escolar_2025.csv` (mesmo schema de colunas que a versão 2023, apenas com sufixo de ano trocado onde ele aparece no nome da coluna, ex. `VL_OBSERVADO_2025`), e `data/raw/indicadores_municipais_ma_ibge_2022.csv` (renda per capita 2022, substituindo o arquivo `_ibge_2010.csv`).

- [ ] **Passo 1: Renomear a função e o filtro de ano do Ideb**

Em `src/ingest.py:8-16`, trocar:

```python
def build_indicadores_municipais_ma_ideb_2023():
	df = pd.read_excel(BASE_DIR / 'divulgacao_anos_iniciais_municipios_2023.xlsx', skiprows=9)
	df_ma = df[(df['SG_UF'] == 'MA') & (df['REDE'] == 'Municipal')]
	cols_id = ['SG_UF', 'CO_MUNICIPIO', 'NO_MUNICIPIO', 'REDE']
	anos = '2023'
	cols_anos = [col for col in df_ma.columns if anos in col]
	df_ma = df_ma[cols_id + cols_anos]

	return df_ma
```

por:

```python
def build_indicadores_municipais_ma_ideb_2025():
	df = pd.read_excel(BASE_DIR / 'divulgacao_anos_iniciais_municipios_2025.xlsx', skiprows=9)
	df_ma = df[(df['SG_UF'] == 'MA') & (df['REDE'] == 'Municipal')]
	cols_id = ['SG_UF', 'CO_MUNICIPIO', 'NO_MUNICIPIO', 'REDE']
	anos = '2025'
	cols_anos = [col for col in df_ma.columns if anos in col]
	df_ma = df_ma[cols_id + cols_anos]

	return df_ma
```

Antes de confiar no `skiprows=9`, abrir a planilha baixada na Task 1 e confirmar em qual linha o cabeçalho de fato começa (o Inep já mudou esse offset entre edições). Ajustar `skiprows` se necessário.

- [ ] **Passo 2: Rodar uma verificação manual do cabeçalho antes de codificar**

```bash
uv run python -c "
import pandas as pd
df = pd.read_excel('data/base/divulgacao_anos_iniciais_municipios_2025.xlsx', skiprows=9)
print(df.columns.tolist())
print(df.head(3))
"
```

Confirmar que existem colunas contendo `2025` (ex. `VL_OBSERVADO_2025`) e que `SG_UF`/`REDE`/`CO_MUNICIPIO`/`NO_MUNICIPIO` existem com esses nomes exatos. Se os nomes vierem diferentes, ajustar `cols_id` no Passo 1 antes de seguir.

- [ ] **Passo 3: Renomear `resolve_censo_path` e `load_censo_microdados` para 2025**

Em `src/ingest.py:28-33`:

```python
def resolve_censo_path() -> Path:
	path_censo_escolar = Path("data/base/microdados_censo_escolar_2025/dados/microdados_ed_basica_2025.csv")
	if path_censo_escolar.exists():
		return path_censo_escolar
	raise FileNotFoundError("Arquivo de microdados do Censo Escolar 2025 não encontrado em data/base.")
```

Ajustar o nome do arquivo conforme o que foi confirmado no Passo 2 da Task 1.

- [ ] **Passo 4: Verificar se as colunas usadas em `load_censo_microdados` (linhas 40-67) ainda existem em 2025**

```bash
uv run python -c "
import pandas as pd
cols = pd.read_csv(
    'data/base/microdados_censo_escolar_2025/dados/microdados_ed_basica_2025.csv',
    sep=';', encoding='latin1', nrows=5
).columns.tolist()
usecols = ['SG_UF','NO_MUNICIPIO','CO_MUNICIPIO','TP_DEPENDENCIA','CO_ENTIDADE',
           'IN_INTERNET','IN_BIBLIOTECA','IN_BIBLIOTECA_SALA_LEITURA','IN_SALA_LEITURA',
           'IN_LABORATORIO_INFORMATICA','IN_QUADRA_ESPORTES','IN_AGUA_POTAVEL',
           'IN_AGUA_REDE_PUBLICA','IN_ESGOTO_REDE_PUBLICA','IN_ESGOTO_FOSSA_SEPTICA',
           'QT_DOC_BAS','QT_DOC_BAS_ESCO_SUP_GRAD','QT_DOC_BAS_ESCO_SUP_GRAD_LICEN',
           'QT_MAT_BAS','QT_MAT_FUND','QT_MAT_MED','QT_MAT_BAS_15_17','QT_MAT_BAS_18_MAIS',
           'QT_TUR_BAS','QT_TUR_FUND','QT_TUR_MED','QT_TUR_FUND_AF','QT_TUR_FUND_AF_CORRFLUXO']
faltando = [c for c in usecols if c not in cols]
print('Faltando em 2025:', faltando)
"
```

Se `faltando` não for vazio, decidir por coluna: (a) o Inep renomeou — ajustar o nome em `load_censo_microdados`; (b) o indicador saiu do Censo — usar `ensure_columns` (já existe no código, linhas 96-100) para não quebrar o resto do pipeline, documentando a perda no texto do artigo (Task 5).

- [ ] **Passo 5: Renomear as funções de construção do Censo Escolar e da Sinopse de docentes**

Em `src/ingest.py:75-134`, renomear:
- `load_sinopse_docentes_efai_2023` → `load_sinopse_docentes_efai_2025`, apontando para `docentes_2025.ods` em vez de `docentes.ods`, e revisando `skiprows=10` contra a planilha real (ver Passo 4 da Task 1).
- `build_indicadores_municipais_ma_censo_docentes_2023` → `build_indicadores_municipais_ma_censo_docentes_2025`.
- `build_indicadores_municipais_ma_censo_escolar_2023` (linha 136) → `build_indicadores_municipais_ma_censo_escolar_2025`, trocando a leitura de `RAW_DIR / "ideb_municipios_ma_publico.csv"` (linha 246) e a coluna `VL_APROVACAO_2023_SI`/`PCT_NAO_APROVACAO_PROXY_2023` (linhas 252-255) para o sufixo `2025`.

Manter a lógica de `has_doc_sup`/`has_doc_lic`/`has_corrfluxo` exatamente como está — ela já foi desenhada para tolerar colunas ausentes.

- [ ] **Passo 6: Atualizar `main()` (linhas 276-330)**

Trocar as chamadas e nomes de arquivo de saída:

```python
def main() -> None:
	RAW_DIR.mkdir(parents=True, exist_ok=True)

	print("Iniciando ingestão do IDEB 2025...")
	timer_thread = start_timer()
	indicadores_ideb = build_indicadores_municipais_ma_ideb_2025()
	output_path_ideb = RAW_DIR / "indicadores_municipais_ma_ideb_2025.csv"
	indicadores_ideb.to_csv(output_path_ideb, index=False, sep=";")
	stop_timer(timer_thread)
	print(f"Arquivo gerado: {output_path_ideb}")
	print(f"Linhas: {len(indicadores_ideb)}")
	print(f"Colunas: {len(indicadores_ideb.columns)}")

	print("Iniciando ingestão do Censo Escolar 2025...")
	timer_thread = start_timer()
	indicadores_censo_escolar = build_indicadores_municipais_ma_censo_escolar_2025()
	indicadores_censo_com_docentes = build_indicadores_municipais_ma_censo_docentes_2025(indicadores_censo_escolar)
	output_path_censo_escolar_com_docentes = RAW_DIR / "indicadores_municipais_ma_censo_escolar_2025.csv"
	indicadores_censo_com_docentes.to_csv(output_path_censo_escolar_com_docentes, index=False, sep=";")
	stop_timer(timer_thread)
	print(f"Arquivo gerado: {output_path_censo_escolar_com_docentes}")
	print(f"Linhas: {len(indicadores_censo_com_docentes)}")
	print(f"Colunas: {len(indicadores_censo_com_docentes.columns)}")

	# IBGE e IDHM ficam em 2010 — sem alteração nesta função.
	print("Iniciando ingestão do IBGE 2010...")
	timer_thread = start_timer()
	indicadores_ibge = build_indicadores_municipais_ma_ibge_2010()
	output_path_ibge = RAW_DIR / "indicadores_municipais_ma_ibge_2010.csv"
	indicadores_ibge.to_csv(output_path_ibge, index=False, sep=";")
	stop_timer(timer_thread)
	print(f"Arquivo gerado: {output_path_ibge}")
	print(f"Linhas: {len(indicadores_ibge)}")
	print(f"Colunas: {len(indicadores_ibge.columns)}")

	print("Iniciando ingestão do IDHM 2010...")
	timer_thread = start_timer()
	indicadores_idhm = build_indicadores_municipais_ma_idhm_2010()
	output_path_idhm = RAW_DIR / "indicadores_municipais_ma_idhm_2010.csv"
	indicadores_idhm.to_csv(output_path_idhm, index=False, sep=";")
	stop_timer(timer_thread)
	print(f"Arquivo gerado: {output_path_idhm}")
	print(f"Linhas: {len(indicadores_idhm)}")
	print(f"Colunas: {len(indicadores_idhm.columns)}")


if __name__ == "__main__":
	main()
```

- [ ] **Passo 7: Trocar a função de ingestão do IBGE de 2010 para renda per capita 2022**

Em `src/ingest.py:264-268`, a função lê uma planilha curada (`ibge.xlsx`) com colunas já renomeadas. A fonte de 2022 (Task 1, Passo 6) é um JSON de resposta da API do SIDRA, com estrutura diferente — não dá pra só trocar o nome do arquivo, precisa de um parser novo. Substituir:

```python
# ── INGESTÃO DO IBGE ───────────────────
def build_indicadores_municipais_ma_ibge_2010():
	df_ma = pd.read_excel(BASE_DIR / 'ibge.xlsx')

	return df_ma
```

por:

```python
# ── INGESTÃO DO IBGE (RENDA PER CAPITA, CENSO 2022) ───────────────────
def build_indicadores_municipais_ma_ibge_2022():
	import json

	with open(BASE_DIR / 'renda_per_capita_censo2022_ma.json', encoding='utf-8') as f:
		payload = json.load(f)

	series = payload[0]['resultados'][0]['series']
	registros = []
	for item in series:
		nome_municipio = item['localidade']['nome'].removesuffix(' - MA')
		valor = item['serie']['2022']
		registros.append({
			'NO_MUNICIPIO': nome_municipio,
			'RENDA_PER_CAPITA_2022': pd.to_numeric(valor, errors='coerce'),
		})

	return pd.DataFrame(registros)
```

Note que essa função já devolve `RENDA_PER_CAPITA_2022` com o nome final de coluna (a fonte 2010 tinha nomes brutos que só eram renomeados depois, em `transform.py`; aqui não há necessidade dessa etapa extra porque a API já não traz nada além do que precisamos).

- [ ] **Passo 8: Atualizar `main()` para chamar a nova função do IBGE**

Em `src/ingest.py:279-330`, trocar o bloco:

```python
	#── INGESTÃO DO IBGE ───────────────────
	print("Iniciando ingestão do IBGE 2010...")
	timer_thread = start_timer()
	indicadores_ibge = build_indicadores_municipais_ma_ibge_2010()
	output_path_ibge = RAW_DIR / "indicadores_municipais_ma_ibge_2010.csv"
	indicadores_ibge.to_csv(output_path_ibge, index=False, sep=";")
	stop_timer(timer_thread)

	print(f"Arquivo gerado: {output_path_ibge}")
	print(f"Linhas: {len(indicadores_ibge)}")
	print(f"Colunas: {len(indicadores_ibge.columns)}")
```

por:

```python
	#── INGESTÃO DO IBGE (RENDA PER CAPITA, CENSO 2022) ───────────────────
	print("Iniciando ingestão da renda per capita — Censo 2022...")
	timer_thread = start_timer()
	indicadores_ibge = build_indicadores_municipais_ma_ibge_2022()
	output_path_ibge = RAW_DIR / "indicadores_municipais_ma_ibge_2022.csv"
	indicadores_ibge.to_csv(output_path_ibge, index=False, sep=";")
	stop_timer(timer_thread)

	print(f"Arquivo gerado: {output_path_ibge}")
	print(f"Linhas: {len(indicadores_ibge)}")
	print(f"Colunas: {len(indicadores_ibge.columns)}")
```

A ingestão do IDHM (linhas 316-326 do arquivo original) não muda — continua chamando `build_indicadores_municipais_ma_idhm_2010()`.

- [ ] **Passo 9: Rodar e verificar**

```bash
uv run python src/ingest.py
```

Esperado: quatro arquivos em `data/raw/`, sem exceção. Conferir na saída que `indicadores_municipais_ma_ideb_2025.csv`, `indicadores_municipais_ma_censo_escolar_2025.csv` e `indicadores_municipais_ma_ibge_2022.csv` têm **217 linhas** (mesma contagem de municípios) — se vier diferente, investigar antes de seguir (ver "Review Focus": municípios sem dado Saeb em 2025).

- [ ] **Passo 10: Commit**

```bash
git add src/ingest.py
git commit -m "Atualiza ingest.py para Ideb 2025, Censo Escolar 2025 e renda per capita Censo 2022"
```

---

## Fase C — Transformação (`src/transform.py`)

### Task 3: Atualizar `transform.py` para a edição 2025 e para a renda per capita 2022

**Files:**
- Modify: `src/transform.py` (linhas 8-64, 66-101, 146-174)

**Interfaces:**
- Consumes: `data/raw/indicadores_municipais_ma_ideb_2025.csv`, `data/raw/indicadores_municipais_ma_censo_escolar_2025.csv`, `data/raw/indicadores_municipais_ma_ibge_2022.csv` (produzidos pela Task 2).
- Produces: `data/trusted/indicadores_municipais_ma.csv` com as colunas `VL_OBSERVADO_2025` (ou o nome real confirmado na Task 2) e `RENDA_PER_CAPITA_2022` no lugar de `VL_OBSERVADO_2023` e `RENDA_PER_CAPITA_2010`.

- [ ] **Passo 1: Renomear `transform_indicadores_municipais_ma_ideb_2023`**

Em `src/transform.py:9-44`, renomear a função para `transform_indicadores_municipais_ma_ideb_2025`, trocar o caminho lido (`indicadores_municipais_ma_ideb_2025.csv`), a variável `anos = '2023'` para `anos = '2025'`, e o `drop(columns=[...])` do final para os nomes de coluna reais com sufixo 2025 (ex. `VL_NOTA_MATEMATICA_2025`, `VL_NOTA_PORTUGUES_2025`) — confirmar esses nomes rodando `df_ideb.columns.tolist()` antes de codificar o `drop`.

- [ ] **Passo 2: Renomear `transform_indicadores_municipais_ma_censo_2023`**

Em `src/transform.py:47-64`, renomear para `transform_indicadores_municipais_ma_censo_2025` e trocar o caminho lido para `indicadores_municipais_ma_censo_escolar_2025.csv`. O corpo da função não referencia o ano em nenhuma outra parte — não precisa de mais mudanças.

- [ ] **Passo 3: Não tocar em `transform_indicadores_municipais_ma_idhm_2010`**

Essa função fica exatamente como está (dado 2010, sem substituto por município disponível — ver Global Constraints).

- [ ] **Passo 3b: Substituir `transform_indicadores_municipais_ma_ibge_2010` por uma versão para a renda 2022**

A função `build_indicadores_municipais_ma_ibge_2022` (Task 2, Passo 7) já devolve `NO_MUNICIPIO` e `RENDA_PER_CAPITA_2022` limpos — não tem linhas de totalização regional nem nomes de coluna brutos do Excel para tratar, como a versão 2010 tinha. Em `src/transform.py:67-101`, trocar:

```python
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
```

por:

```python
# ── TRANSFORMAÇÃO DO IBGE (RENDA PER CAPITA, CENSO 2022) ───────────────────
def transform_indicadores_municipais_ma_ibge_2022():
  df_ibge = pd.read_csv(RAW_DIR / 'indicadores_municipais_ma_ibge_2022.csv', sep=';', skiprows=0)

  df_ibge['RENDA_PER_CAPITA_2022'] = pd.to_numeric(df_ibge['RENDA_PER_CAPITA_2022'], errors='coerce')

  return df_ibge
```

A coluna `POPULACAO_URBANA_2010` deixa de existir — ela não é usada em nenhuma das listas `VARS_*` de `src/analytics.py` (confirmado por leitura do arquivo), então não há impacto na análise. Se `merge_dataframes` (Passo 5 abaixo) ou o quadro de variáveis do artigo (Task 5) mencionarem essa coluna, remover a menção.

- [ ] **Passo 4: Atualizar `main()` (linhas 146-174)**

```python
def main() -> None:
  TRUSTED_DIR.mkdir(parents=True, exist_ok=True)

  print("Transformação do IDEB 2025...")
  df_ideb = transform_indicadores_municipais_ma_ideb_2025()
  print(df_ideb.head())

  print("Transformação do CENSO 2025...")
  df_censo = transform_indicadores_municipais_ma_censo_2025()

  print("Transformação da renda per capita — Censo 2022...")
  df_ibge = transform_indicadores_municipais_ma_ibge_2022()

  print("Transformação do IDHM 2010...")
  df_idhm = transform_indicadores_municipais_ma_idhm_2010()
  print(df_idhm.info())

  print("Realizando merge dos indicadores...")
  df_merged = merge_dataframes(df_ideb, df_censo, df_ibge, df_idhm)
  print(df_merged.info())
  output_path_trusted = TRUSTED_DIR / "indicadores_municipais_ma.csv"
  df_merged.to_csv(output_path_trusted, index=False, sep=";")

if __name__ == "__main__":
	main()
```

`merge_dataframes` (linhas 128-144) não precisa mudar — ela já trabalha por nome de coluna genérico (`NO_MUNICIPIO`), não por ano.

- [ ] **Passo 5: Rodar e verificar**

```bash
uv run python src/transform.py
```

Esperado: `data/trusted/indicadores_municipais_ma.csv` gerado, com colunas `VL_OBSERVADO_2025` e `RENDA_PER_CAPITA_2022` (conferir com `pd.read_csv(..., sep=';').columns.tolist()`) e sem perda de linhas em relação aos 217 municípios da Task 2.

- [ ] **Passo 6: Commit**

```bash
git add src/transform.py
git commit -m "Atualiza transform.py para Ideb 2025, Censo Escolar 2025 e renda per capita Censo 2022"
```

---

## Fase D — Análise (`src/analytics.py` e notebook)

### Task 4: Renomear as colunas-alvo (Ideb e renda) e rodar a análise completa com os dados de 2025/2022

**Files:**
- Modify: `src/analytics.py` (linhas 18, 43-44, 155, 160, 169, 173-176, 186-187, 279-283, 294-311, 338, 342, 346, 472, 503, 519, 537, 557, 567, 574)
- Modify: `src/analytics.ipynb` (mesmas referências, na versão notebook)
- Regenerate: `reports/figures/*.png`, `reports/analytics-executado.html`

**Interfaces:**
- Consumes: `data/trusted/indicadores_municipais_ma.csv` (produzido pela Task 3), com as colunas `VL_OBSERVADO_2025` e `RENDA_PER_CAPITA_2022`.
- Produces: os mesmos artefatos de antes (figuras PNG, HTML executado), agora com números de 2025/2022. Estes números alimentam a Task 5 (reescrita do artigo).

- [ ] **Passo 1: Substituir `VL_OBSERVADO_2023` por `VL_OBSERVADO_2025`, e `RENDA_PER_CAPITA_2010` por `RENDA_PER_CAPITA_2022`, em todo `src/analytics.py`**

```bash
cd src && sed -i \
  -e 's/VL_OBSERVADO_2023/VL_OBSERVADO_2025/g' \
  -e 's/RENDA_PER_CAPITA_2010/RENDA_PER_CAPITA_2022/g' \
  analytics.py
```

Confirmar antes que os nomes reais das colunas no CSV são exatamente `VL_OBSERVADO_2025` (Task 3, Passo 5) e `RENDA_PER_CAPITA_2022` (Task 3, Passo 5) — se algum vier diferente, usar o nome real no `sed`. Note que `IDHM_2010` **não muda** (fica como está, ver Global Constraints) — não incluir esse termo no `sed`.

- [ ] **Passo 2: Atualizar os textos fixos que mencionam "2023" nos títulos dos gráficos**

Em `src/analytics.py:537` (dentro de `distribuicao_quartis_cluster`) e `:567`/`:574` (dentro de `distribuicao_ideb`):

```python
ax.set_xlabel('IDEB 2025 (Anos Iniciais do Ensino Fundamental)')
```
```python
ax.set_title('Distribuição do IDEB 2025 — Municípios Maranhenses (Rede Municipal)', fontsize=13, fontweight='bold')
```
```python
print(f"\nDistribuição do IDEB 2025:")
```

- [ ] **Passo 3: Repetir os Passos 1-2 em `src/analytics.ipynb`**

O notebook espelha `analytics.py` célula a célula (conforme `.planning/codebase/STRUCTURE.md`). Abrir o notebook e aplicar as mesmas trocas de string nas células equivalentes — não há como usar `sed` num `.ipynb` com segurança por causa do JSON, então usar a ferramenta de edição de notebook célula por célula.

- [ ] **Passo 4: Rodar o pipeline de análise via script**

```bash
uv run python src/analytics.py
```

Ler a saída no terminal e registrar (para uso na Task 5): número de municípios com dado completo, IDEB médio/mediana/desvio, melhor `k` do KMeans e silhouette score, tamanho de cada cluster, variáveis significativas no Mann-Whitney por cluster (com p-valores), R² e importâncias do Random Forest.

- [ ] **Passo 5: Rodar o notebook (o "teste de integração" do projeto)**

```bash
uv run jupyter nbconvert --to html --execute src/analytics.ipynb --output-dir reports --output analytics-executado
```

Esperado: o comando termina sem erro (esse é o guard de integração que o projeto já usa, conforme `.planning/codebase/TESTING.md`) e `reports/analytics-executado.html` é regravado com as novas figuras.

- [ ] **Passo 6: Verificar visualmente as figuras regeneradas**

```bash
ls -la reports/figures/
```

Comparar timestamps para confirmar que todos os 5 PNGs foram regravados (`distribuicao_ideb.png`, `elbow_silhouette.png`, `pca_clusters.png`, `random_forest_importancia.png`, `cluster_<nome>_variaveis_relevantes_destaque.png`). Copiar os mesmos arquivos para `artigo/images/` (usado pelo LaTeX):

```bash
cp reports/figures/*.png artigo/images/
```

- [ ] **Passo 7: Commit**

```bash
git add src/analytics.py src/analytics.ipynb reports/figures artigo/images
git commit -m "Atualiza analytics.py/notebook para Ideb 2025 e regenera figuras"
```

---

## Fase E — Artigo (LaTeX)

### Task 5: Reescrever os números e referências do artigo para a edição 2025

**Files:**
- Modify: `artigo/metadados.tex` (resumos PT/EN/ES, linhas 21-28)
- Modify: `artigo/1_introducao.tex` (linhas 6, 12)
- Modify: `artigo/3_procedimentos_metodologicos.tex` (linhas 11-17, 41-64, itens do quadro de variáveis)
- Modify: `artigo/4_resultados_discussao.tex` (todos os números derivados da Task 4)
- Modify: `artigo/references.bib` (citação do Ideb/Censo/Sinopse: ano e possivelmente chave)

**Interfaces:**
- Consumes: os números impressos na Task 4 (Passo 4) e o novo total de municípios com dado completo.
- Produces: `artigo/main.pdf` e `artigo/main_identificado.pdf` recompilados.

- [ ] **Passo 1: Atualizar `3_procedimentos_metodologicos.tex` (fontes de dados)**

Na linha 11, trocar "utilizou-se a edição 2023 da rede municipal, que cobriu os 217 (todos) municípios" pela edição 2025 e o número real de municípios com dado completo (confirmado na Task 4). Na linha 13, trocar "Censo Escolar 2023" e "Sinopse Estatística da Educação Básica 2023" pelos nomes/anos de 2025, e o número da tabela de docentes confirmado na Task 1 (Passo 4), se diferente de 2.23.

Reescrever o item "Censo Demográfico 2010 (IBGE)" (linha 15) para refletir a troca para 2022. Texto atual:

> A renda \textit{per capita} municipal de 2010 foi extraída do Censo Demográfico do Instituto Brasileiro de Geografia e Estatística (IBGE) \parencite{ibge2010} e utilizada como \textit{proxy} da capacidade econômica dos municípios. Embora defasada, essa variável é o indicador de renda municipal mais desagregado disponível com cobertura universal para os 217 municípios analisados.

Nova versão:

> A renda \textit{per capita} municipal foi extraída do Censo Demográfico 2022 do Instituto Brasileiro de Geografia e Estatística (IBGE) \parencite{ibge2022}, tabela "Valor do rendimento nominal médio mensal domiciliar per capita" (Sidra, tabela 10295), e utilizada como \textit{proxy} da capacidade econômica dos municípios. Diferentemente da edição de 2010 utilizada em versões anteriores desta análise, o dado de 2022 é o mais recente disponível com cobertura universal por município.

Adicionar, imediatamente depois do item "IDHM 2010 (Atlas Brasil/PNUD)" (linha 17), uma frase nova explicando por que o IDHM não seguiu a mesma atualização (isso evita a leitura de que a defasagem do IDHM foi um descuido):

> A atualização do Atlas Brasil para o período 2022-2024 baseia-se na Pesquisa Nacional por Amostra de Domicílios Contínua (PNAD Contínua), cuja desagregação geográfica cobre apenas 146 estratos de municípios para todo o Brasil \parencite{ibge2022notatecnica}, não municípios individuais. Como a análise depende de diferenciar cada um dos 217 municípios maranhenses, manteve-se o IDHM calculado a partir do Censo Demográfico de 2010, a edição mais recente com desagregação municipal individual disponível.

- [ ] **Passo 2: Atualizar o quadro de variáveis (linhas 41-64) e a seção de coleta/pré-processamento (linhas 69-83)**

Trocar toda ocorrência de "Censo 2023" e "Sinopse 2023" pelo ano 2025 na coluna "Fonte" da tabela. Trocar a linha "Renda \textit{per capita} 2010 & IBGE 2010 & ..." para "Renda \textit{per capita} 2022 & IBGE/Censo 2022 & Rendimento domiciliar per capita médio mensal municipal (R\$)". Na descrição do pipeline de ingestão (linhas 71-83), trocar "Tabela 2.23 da Sinopse Estatística 2023" pelo identificador real confirmado na Task 1, e adicionar uma frase sobre a nova fonte de renda (Sidra, tabela 10295, Censo Demográfico 2022) no lugar da menção à planilha `ibge.xlsx`.

- [ ] **Passo 3: Reescrever `4_resultados_discussao.tex` com os novos números**

Ler o arquivo atual, localizar cada número (médias, desvios, tamanhos de cluster, p-valores, importâncias do Random Forest, R²) e substituí-lo pelo valor correspondente impresso na Task 4, Passo 4. Não copiar números "de memória" — usar exatamente o que saiu do `uv run python src/analytics.py` desta rodada.

- [ ] **Passo 4: Atualizar `1_introducao.tex`**

Linha 6: se o objetivo geral menciona "IDEB 2023", trocar para 2025. Linha 12: trocar "217 municípios maranhenses com dados disponíveis no IDEB 2023" e "Censo Escolar 2023" pelos números/anos confirmados.

- [ ] **Passo 5: Atualizar os três resumos em `metadados.tex` (PT, EN, ES)**

Nas linhas 21, 24, 27, trocar "2023" pelo ano 2025 em cada idioma, e o número de municípios se tiver mudado. Manter a mesma estrutura de frase — só troca de números/ano.

- [ ] **Passo 6: Atualizar `references.bib`**

Localizar a entrada citada como `\parencite{inep2023}` e `inep2024microdados`/`inep2024sinopse` (usadas em `3_procedimentos_metodologicos.tex:11,13`). Decidir: manter as chaves antigas apontando para a fonte 2025 atualizada (mais simples, mas engana quem olha o `.bib`) ou criar chaves novas (`inep2025`, `inep2026microdados`, `inep2026sinopse`) e atualizar todas as citações no texto. Recomendo criar chaves novas — evita citação com nome de ano errado no PDF final. Atualizar todos os `\parencite{}`/`\textcite{}` correspondentes nos arquivos da Fase E.

Adicionar também duas entradas novas para a renda per capita, usadas no Passo 1 acima:

```bibtex
@misc{ibge2022,
  author = {{Instituto Brasileiro de Geografia e Estatística}},
  title = {Censo Demográfico 2022: rendimento nominal médio mensal domiciliar per capita, por município},
  year = {2022},
  howpublished = {Sidra, tabela 10295},
  url = {https://sidra.ibge.gov.br/tabela/10295},
  urldate = {2026-09-27}
}

@misc{ibge2022notatecnica,
  author = {{Instituto Brasileiro de Geografia e Estatística}},
  title = {Nota Técnica 01/2022: estimativas para estratos de municípios na PNAD Contínua},
  year = {2022},
  url = {https://www.ibge.gov.br/novo-portal-destaques/33562-nota-tecnica-estimativas-para-estratos-de-municipios-na-pnad-continua.html},
  urldate = {2026-09-27}
}
```

Confirmar que a entrada `ibge2010` (citação antiga da renda 2010) não fica órfã: se não for mais citada em nenhum `.tex`, remover do `.bib`; se ainda for citada em algum outro ponto do texto (introdução, referencial teórico), manter.

- [ ] **Passo 7: Recompilar o PDF**

```bash
cd artigo && make
```

(ou, se não houver alvo `make` genérico, seguir a sequência documentada no `README.md` do projeto: `pdflatex → bibtex → pdflatex → pdflatex`, para `main.tex` e depois `main_identificado.tex`).

- [ ] **Passo 8: Verificar compilação sem erros**

```bash
grep -i "error" artigo/main.log | grep -v "^$"
```

Esperado: sem saída (nenhum erro). Confirmar visualmente as páginas de resultados no PDF gerado.

- [ ] **Passo 9: Commit**

```bash
git add artigo/*.tex artigo/references.bib artigo/main.pdf artigo/main_identificado.pdf artigo/images
git commit -m "Atualiza artigo para a edição Ideb 2025 e Censo Escolar 2025"
```

---

## Fase F — Memória do projeto

### Task 6: Atualizar a memória do projeto com o novo estado

**Files:**
- Modify: `/home/darlon/.claude/projects/-media-dados-aplicacoes-git-mestrado-Artigos-desempenho-educacional-maranhao/memory/project_article.md`

- [ ] **Passo 1: Atualizar a memória `project-article-maranhao`**

Substituir a seção "Estado atual" e "Resultados principais incorporados ao texto" pelos números de 2025/2022 confirmados na Task 4/5. Registrar explicitamente: "Ideb e Censo Escolar atualizados para 2025; renda per capita atualizada para o Censo 2022 (Sidra, tabela 10295); IDHM permanece 2010 porque a extensão do Atlas Brasil pra 2022-2024 usa PNAD Contínua com granularidade de apenas 146 estratos de municípios, não município individual" e a data da troca de edição (2026-09-27), para que uma sessão futura não pergunte de novo "por que não é a edição mais recente" ou "por que IDHM e renda estão em anos diferentes" sem saber que essas perguntas já foram resolvidas.

---

## Self-Review

**Spec coverage:** as seis fases cobrem os quatro scripts do pipeline (ingest, transform, analytics, notebook) e as cinco seções do artigo que citam ano/dados (introdução, métodos, resultados, resumos, referências), incluindo a troca da renda per capita para 2022 e a justificativa de por que o IDHM não acompanhou essa troca. Nenhuma menção a "2023" ou a "RENDA_PER_CAPITA_2010" nos arquivos `.tex`/`.py` deve sobrar fora do caso explicitamente mantido (IDHM 2010).

**Placeholder scan:** todos os passos de código mostram o código real a escrever; os pontos que dependem de confirmar um nome de coluna ou de arquivo antes de codificar (Review Focus) estão marcados como verificação explícita com comando a rodar, não como "ajustar conforme necessário" vago.

**Type consistency:** o nome de coluna `VL_OBSERVADO_2025` é usado de forma consistente entre Task 3 (produção) e Task 4 (consumo); se a Task 2 confirmar um nome diferente, esse nome deve ser propagado igual nas Tasks 3 e 4 (a Task 4, Passo 1, já avisa para conferir antes do `sed`).

**Review Focus:** os cinco riscos (mudança de colunas do Censo, tabela da Sinopse renumerada, nome de coluna do Ideb, queda no número de municípios com dado, ausência de metas oficiais em 2025) já têm um passo de verificação dedicado antes do código que depende deles.
