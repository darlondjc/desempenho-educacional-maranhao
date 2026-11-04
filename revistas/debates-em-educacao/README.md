# Artigo — template da revista Debates em Educação

Adaptação do artigo ao [template 2026 da revista Debates em Educação](https://periodicos.ufal.br/debateseducacao/template)
(PPGE/Ufal, ISSN 2175-6600). A revista só aceita submissões em Word; o texto continua sendo
mantido em LaTeX e os arquivos `.docx` são gerados a partir dele.

## Estrutura

| Arquivo | Conteúdo |
| --- | --- |
| `metadados.tex` | títulos (PT/EN/ES), autoria, resumos e palavras-chave |
| `1_introducao.tex` … `5_consideracoes_finais.tex` | seções do artigo |
| `6_informacoes_complementares.tex` | declaração de IA, dados e CRediT (este só na versão identificada) |
| `debates.sty` | formatação do template em LaTeX |
| `build_docx.py` | gera os `.docx` usando o template oficial como base |
| `template/` | template oficial (`.docx`), estilo ABNT (`abnt.csl`) e filtro do pandoc |
| `submissao/` | arquivos gerados para a submissão |

## Compilação

Requer LuaLaTeX, Biber, biblatex-abnt e pandoc (>= 3.0).

```bash
make        # PDFs de prévia e .docx de submissão em submissao/
```

Arquivos gerados em `submissao/`:

- `artigo_sem_identificacao.docx` — **enviar na submissão** (avaliação às cegas);
- `informacao_autores.docx` — dados de autoria (arquivo separado);
- `artigo_identificado.docx` — versão final, após aprovação;
- `artigo_*.pdf` — prévias geradas pelo LaTeX.

## Convenções do template

- Seções em caixa alta (`\section{INTRODUÇÃO}`), subseções só com a inicial maiúscula; sem numeração.
- Ilustrações com legenda acima e fonte abaixo, usando os ambientes `grafico`, `quadro`,
  `figure` e `table` e os comandos `\fonte{...}` e `\nota{...}`. O prefixo do rótulo define
  o tipo no Word: `graf:`, `qua:`, `fig:`, `tab:`.
- Citações com `\parencite` e `\textcite` (autor-data, NBR 10520:2023).
- As considerações finais não devem conter citações.
