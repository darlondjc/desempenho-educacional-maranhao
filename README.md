# Projeto desempenho-educacional-maranhao

Pipeline de ingestão em Python para coleta de dados da API de dados, com foco em confiabilidade de carga, idempotência por registro e controle de execução incremental.

## De-Para IDEB Anos Iniciais

Base: *IDEB Resultados* (Dados agregados por município). Disponível no [link](https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados).

| Campo | Descrição |
|---|---|
| `SG_UF` | Sigla da UF |
| `CO_MUNICIPIO` | Código do município |
| `NO_MUNICIPIO` | Nome do município |
| `REDE` | Rede de ensino |
| `VL_APROVACAO_2023_SI_4` | Taxa de aprovação 2023 — Anos Iniciais (4ª série/5º ano) |
| `VL_APROVACAO_2023_SI` | Taxa de aprovação 2023 — Anos Iniciais (total) |
| `VL_APROVACAO_2023_1` | Taxa de aprovação 2023 — 1º ano |
| `VL_APROVACAO_2023_2` | Taxa de aprovação 2023 — 2º ano |
| `VL_APROVACAO_2023_3` | Taxa de aprovação 2023 — 3º ano |
| `VL_APROVACAO_2023_4` | Taxa de aprovação 2023 — 4º ano |
| `VL_INDICADOR_REND_2023` | Indicador de rendimento escolar 2023 |
| `VL_NOTA_MATEMATICA_2023` | Nota de Matemática 2023 (SAEB) |
| `VL_NOTA_PORTUGUES_2023` | Nota de Língua Portuguesa 2023 (SAEB) |
| `VL_NOTA_MEDIA_2023` | Nota média padronizada 2023 |
| `VL_OBSERVADO_2023` | IDEB observado 2023 |

## De-Para IDEB Anos Finais

| Campo | Descrição |
|---|---|

## De-Para Censo Escolar

Base: *Microdados da Educação Básica 2023* (INEP - dados agregados por município). Disponível no [link](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar).

| Campo | Descrição |
|---|---|
| `CO_MUNICIPIO` | Código do município (IBGE) |
| `SG_UF` | Sigla da unidade federativa |
| `NO_MUNICIPIO` | Nome do município |
| `QT_ESCOLAS` | Quantidade de escolas |
| `PCT_ESCOLAS_COM_INTERNET` | Percentual de escolas com internet |
| `PCT_ESCOLAS_COM_BIBLIOTECA_LEITURA` | Percentual de escolas com biblioteca/sala de leitura |
| `PCT_ESCOLAS_COM_LAB_INFORMATICA` | Percentual de escolas com laboratório de informática |
| `PCT_ESCOLAS_COM_QUADRA` | Percentual de escolas com quadra de esportes |
| `PCT_ESCOLAS_COM_AGUA_ADEQUADA` | Percentual de escolas com água da rede pública adequada |
| `PCT_ESCOLAS_COM_ESGOTO_ADEQUADO` | Percentual de escolas com esgoto sanitário adequado |
| `QT_DOC_BAS` | Quantidade total de docentes na educação básica |
| `QT_DOC_BAS_ESCO_SUP_GRAD` | Quantidade de docentes com escolaridade superior — graduação |
| `QT_DOC_BAS_ESCO_SUP_GRAD_LICEN` | Quantidade de docentes com escolaridade superior — licenciatura |
| `QT_MAT_BAS` | Quantidade total de matrículas na educação básica |
| `QT_MAT_FUND` | Quantidade de matrículas no ensino fundamental |
| `QT_MAT_MED` | Quantidade de matrículas no ensino médio |
| `QT_MAT_BAS_15_17` | Quantidade de matrículas — educação básica, idade 15–17 anos |
| `QT_MAT_BAS_18_MAIS` | Quantidade de matrículas — educação básica, idade 18+ anos |
| `QT_TUR_BAS` | Quantidade total de turmas na educação básica |
| `QT_TUR_FUND` | Quantidade de turmas no ensino fundamental |
| `QT_TUR_MED` | Quantidade de turmas no ensino médio |
| `QT_TUR_FUND_AF` | Quantidade de turmas — ensino fundamental — anos finais |
| `QT_TUR_FUND_AF_CORRFLUXO` | Quantidade de turmas — ensino fundamental — anos finais — correção de fluxo |
| `PCT_DOC_SUPERIOR_COMPLETO` | Percentual de docentes com educação superior completa |
| `PCT_DOC_LICENCIATURA_TOTAL` | Percentual de docentes com licenciatura (total, incluindo dupla formação) |
| `MEDIA_ALUNOS_POR_TURMA_BAS` | Média de alunos por turma — educação básica |
| `MEDIA_ALUNOS_POR_TURMA_FUND` | Média de alunos por turma — ensino fundamental |
| `MEDIA_ALUNOS_POR_TURMA_MED` | Média de alunos por turma — ensino médio |
| `PCT_MAT_15_ANOS_OU_MAIS_PROXY_DISTSERIE` | Percentual de matrículas com 15+ anos proxy de distorção série-idade |
| `PCT_TURMAS_CORRFLUXO_FUND_AF` | Percentual de turmas com correção de fluxo — ensino fundamental (anos finais) |

## De-Para IBGE

IDHM: disponível em [IDHM](https://dataimesc.imesc.ma.gov.br/series/875/show).

Outros indicadores IBGE: disponível em [Atlas Brasil](http://www.atlasbrasil.org.br/consulta/planilha).

| Campo | Descrição |
|---|---|

## Fonte de dados

A fonte escolhida é a API de dados do [Portal da Transparência](https://api.portaldatransparencia.gov.br) acessada por rotas sob o prefixo `/api-de-dados/`.

No estado atual do projeto, o pipeline consome o endpoint de permissionários com paginação:

- `/api-de-dados/permissionarios`

## Decisões de implementação

### Controle de protocolo HTTP

O acesso e as validações do protocolo HTTP foi centralizado na função `requisitar_resiliente`.

Essa função aplica:

- validação da URL para garantir o prefixo `/api-de-dados/`
- validação das credenciais obrigatórias em variáveis de ambiente
- validação do parâmetro obrigatório `pagina`
- timeout por requisição
- tratamento explícito de `401` e `403` sem retentativa
- tratamento de `429` com uso do header `Retry-After`
- retentativas com backoff exponencial para erros `5xx`

Com isso, o pipeline falha cedo em erros de configuração e se recupera de falhas transitórias de rede ou indisponibilidade da API.

### Estratégia de paginação

A paginação é feita no lado do cliente. Portanto é feita usando a estratégia de _offset_.

### Estratégia de carga Full Load

A carga adotada para permissionários é Full Load paginado, devido ao pequeno tamanho da carga de dados (<5G)

O processo começa na página `1` e continua até que uma página retorne sem registros. Isso evita depender de um total prévio informado pela API e simplifica o controle de parada.

### Idempotência

A idempotência foi implementada por hash de registro, e não por hash do lote inteiro.

Cada registro é serializado com `json.dumps(..., sort_keys=True)` e transformado em hash SHA-256. O inventário de hashes já vistos é mantido em:

- `data/control/hashes.json`

Na prática, isso permite:

- evitar duplicação de registros em reprocessamentos
- manter checkpoint incremental entre execuções
- continuar a carga por páginas sem regravar o que já foi persistido

### Raw imutável

O dado bruto persistido em JSON não deve ser reescrito de forma destrutiva para remover ou modificar registros já coletados. O método idempotente acrescenta somente novos registros ao arquivo de saída.

Além disso, o schema é salvo separadamente em arquivo `.schema.json`, sem duplicar a responsabilidade de persistência do dado bruto.

### Watermark

O pipeline mantém um watermark em:

- `data/control/watermark.json`

Esse arquivo registra:

- `ultimo_registro`
- `atualizado_em`

O objetivo é suportar controle temporal de execução e servir de base para evoluções futuras de carga incremental orientada por tempo.

### Hashes de registros

Os hashes são usados como mecanismo de deduplicação técnica. O controle é separado do dado bruto para que a lógica de idempotência fique explícita e auditável.

### Segurança de credenciais

As credenciais não ficam hardcoded no código.

O projeto usa `python-dotenv` para carregar variáveis a partir de um arquivo `.env` na raiz. As variáveis esperadas são:

- `API_KEY`
- `API_BASE_URL`

O `.gitignore` já está configurado para impedir versionamento do `.env`, reduzindo o risco de vazamento de credenciais.

## Estrutura de artefatos

Arquivos gerados e usados pelo pipeline:

- `data/raw/permissionarios.json`: dataset bruto acumulado com somente novos registros
- `data/raw/permissionarios.schema.json`: metadados de schema do dataset coletado
- `data/control/hashes.json`: inventário de hashes dos registros já persistidos
- `data/control/watermark.json`: controle temporal da última atualização

## Instrução de execução

### 1. Configurar ambiente

Crie um arquivo `.env` na raiz do projeto com:

```env
API_KEY=sua_chave
API_BASE_URL=https://sua-url-base
```

### 2. Instalar dependências

Se estiver usando `uv`:

```bash
uv sync
```

### 3. Executar o pipeline

```bash
uv run python main.py
```

## Comportamento esperado da execução

Durante a execução, o pipeline:

- inicia a ingestão de permissionários
- percorre as páginas sequencialmente
- persiste somente registros novos
- atualiza o schema do dataset
- atualiza o watermark de controle
- exibe a quantidade total de registros lidos e de novos registros persistidos

## Observações

- O método de requisição atual exige o parâmetro `pagina`, portanto está acoplado ao fluxo paginado atual.
- Se novos endpoints sem paginação forem incorporados, o ideal é separar a função HTTP genérica da função HTTP paginada.
