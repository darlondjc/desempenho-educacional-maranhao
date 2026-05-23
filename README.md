## Desempenho Educacional nos Municípios Maranhenses

Projeto de análise e modelagem dos fatores associados ao desempenho educacional municipal no Maranhão, com foco em segmentação socioeconômica e identificação de variáveis explicativas do IDEB.

### Objetivo
Segmentar municípios por contexto socioeconômico e, dentro de cada grupo, identificar fatores associados aos destaques de IDEB, utilizando Python e pipeline reprodutível.

---

## Estrutura do Projeto

- **src/**: scripts de ingestão, transformação e análise
- **data/**: bases em diferentes estágios (base, raw, trusted)
- **reports/**: relatórios, slides e figuras

---

## Execução do Pipeline Analítico

### 1. Instalação das dependências

Requer Python >= 3.12 e [uv](https://github.com/astral-sh/uv):

```bash
uv sync
```

### 2. Execução do notebook de análise

Execute e gere o notebook com outputs atualizados:

```bash
uv run jupyter nbconvert --to html --execute src/analytics.ipynb --output analytics-executado --output-dir reports
```

Para gerar PDF (requer Chromium):

```bash
uv run jupyter nbconvert --to webpdf --execute src/analytics.ipynb --output analytics-executado --output-dir reports --allow-chromium-download
```

O arquivo gerado estará em `reports/analytics-executado.html` ou `.pdf`.

---

## Configuração e Execução do Quarto (Seminário)

### 1. Instale o Quarto (https://quarto.org/docs/get-started/)

No Linux:
```bash
sudo apt install quarto-cli
```
Ou baixe do site oficial.

### 2. Renderize o arquivo do seminário

No diretório do projeto:

```bash
quarto render reports/seminario_slides.qmd
```

O HTML será gerado em `reports/seminario_slides.html`.

Para abrir localmente:
```bash
xdg-open reports/seminario_slides.html
```

---

## Referências e Créditos

- Dados: INEP, IBGE, Censo Escolar, IDEB EFAI
- Código: Darlon Coqueiro (PPGCA/IFMA)

---

> Para dúvidas ou reprodutibilidade, consulte os scripts em `src/` e o notebook principal em `src/analytics.ipynb`.
