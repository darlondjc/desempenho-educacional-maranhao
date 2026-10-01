"""Gráficos nativos (editáveis) no .docx.

O template da revista Debates em Educação não aceita gráfico em imagem: o
gráfico deve ser editável no próprio arquivo, com os dados em planilha. O LaTeX
continua usando os PNGs; este módulo, chamado por build_docx.py depois do
pandoc, troca no .docx a imagem de cada gráfico por um gráfico nativo do Word,
com a planilha de dados embutida ("Editar dados" no Word).

Os dados vêm de dados_graficos/*.csv, gerados por src/analytics.py junto com os
PNGs. A legenda (“Gráfico N – título”) identifica o gráfico a substituir.
"""

import csv
import io
import re
import statistics
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

DADOS = Path(__file__).resolve().parent / "dados_graficos"

NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
FOLHA = "Planilha1"

LARGURA = 4896000  # 13,6 cm (85% da largura útil do texto), em EMU
ALTURA = 2880000   # 8 cm


# ---------------------------------------------------------------------------
# Leitura dos dados
# ---------------------------------------------------------------------------
def _ler(nome):
    with open(DADOS / f"{nome}.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _br(valor, casas):
    return f"{valor:.{casas}f}".replace(".", ",")


# ---------------------------------------------------------------------------
# Planilha embutida (xlsx mínimo, só biblioteca padrão)
# ---------------------------------------------------------------------------
def _coluna(i):
    return chr(ord("A") + i)


def _xlsx(cabecalho, linhas):
    def celula(ref, valor):
        if valor is None:
            return ""
        if isinstance(valor, str):
            return f'<c r="{ref}" t="inlineStr"><is><t>{escape(valor)}</t></is></c>'
        return f'<c r="{ref}"><v>{valor!r}</v></c>'

    todas = [cabecalho] + linhas
    corpo = "".join(
        f'<row r="{n}">' + "".join(celula(f"{_coluna(i)}{n}", v) for i, v in enumerate(linha)) + "</row>"
        for n, linha in enumerate(todas, start=1)
    )
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    partes = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            "</Types>"
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{NS_PKG}">'
            f'<Relationship Id="rId1" Type="{NS_R}/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>"
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<workbook xmlns="{ns}" xmlns:r="{NS_R}"><sheets>'
            f'<sheet name="{FOLHA}" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{NS_PKG}">'
            f'<Relationship Id="rId1" Type="{NS_R}/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>"
        ),
        "xl/worksheets/sheet1.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<worksheet xmlns="{ns}"><sheetData>{corpo}</sheetData></worksheet>'
        ),
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, dados in partes.items():
            z.writestr(nome, dados)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Blocos de XML de gráfico (ordem dos elementos segue o esquema DrawingML)
# ---------------------------------------------------------------------------
def _fonte(sz=1000, rot=None):
    corpo = f'<a:bodyPr rot="{rot}" vert="horz"/>' if rot is not None else "<a:bodyPr/>"
    return (
        f'<c:txPr>{corpo}<a:lstStyle/><a:p><a:pPr><a:defRPr sz="{sz}" b="0">'
        '<a:solidFill><a:srgbClr val="000000"/></a:solidFill><a:latin typeface="Arial"/>'
        '</a:defRPr></a:pPr><a:endParaRPr lang="pt-BR"/></a:p></c:txPr>'
    )


def _titulo_eixo(texto, vertical=False):
    rot = ' rot="-5400000" vert="horz"' if vertical else ""
    return (
        f'<c:title><c:tx><c:rich><a:bodyPr{rot}/><a:lstStyle/><a:p><a:pPr><a:defRPr sz="1000" b="0">'
        '<a:latin typeface="Arial"/></a:defRPr></a:pPr>'
        f'<a:r><a:rPr lang="pt-BR" sz="1000" b="0"><a:solidFill><a:srgbClr val="000000"/></a:solidFill>'
        f'<a:latin typeface="Arial"/></a:rPr><a:t>{escape(texto)}</a:t></a:r></a:p></c:rich></c:tx>'
        '<c:overlay val="0"/></c:title>'
    )


def _intervalo(coluna, n, inicio=2):
    return f"{FOLHA}!${coluna}${inicio}:${coluna}${inicio + n - 1}"


def _cache_texto(valores):
    pts = "".join(f'<c:pt idx="{i}"><c:v>{escape(str(v))}</c:v></c:pt>' for i, v in enumerate(valores))
    return f'<c:strCache><c:ptCount val="{len(valores)}"/>{pts}</c:strCache>'


def _ref_texto(ref, valores):
    return f"<c:strRef><c:f>{ref}</c:f>{_cache_texto(valores)}</c:strRef>"


def _ref_num(ref, valores):
    pts = "".join(f'<c:pt idx="{i}"><c:v>{v!r}</c:v></c:pt>' for i, v in enumerate(valores) if v is not None)
    return (
        f"<c:numRef><c:f>{ref}</c:f><c:numCache><c:formatCode>General</c:formatCode>"
        f'<c:ptCount val="{len(valores)}"/>{pts}</c:numCache></c:numRef>'
    )


def _nome_serie(coluna, nome):
    return f"<c:tx>{_ref_texto(f'{FOLHA}!${coluna}$1', [nome])}</c:tx>"


def _cor(hexa):
    return f'<a:solidFill><a:srgbClr val="{hexa}"/></a:solidFill>'


def _eixo_cat(id_, cruza, titulo=None, rot=None, apagado=False, tickskip=None):
    return (
        f'<c:catAx><c:axId val="{id_}"/><c:scaling><c:orientation val="minMax"/></c:scaling>'
        f'<c:delete val="{int(apagado)}"/><c:axPos val="b"/>'
        + (_titulo_eixo(titulo) if titulo else "")
        + '<c:numFmt formatCode="General" sourceLinked="0"/><c:majorTickMark val="out"/>'
        '<c:minorTickMark val="none"/><c:tickLblPos val="nextTo"/>'
        '<c:spPr><a:ln w="9525">' + _cor("595959") + "</a:ln></c:spPr>"
        + _fonte(900 if rot is not None else 1000, rot)
        + f'<c:crossAx val="{cruza}"/><c:crosses val="autoZero"/><c:auto val="1"/>'
        '<c:lblAlgn val="ctr"/><c:lblOffset val="100"/>'
        + (f'<c:tickLblSkip val="{tickskip}"/>' if tickskip else "")
        + '<c:noMultiLvlLbl val="0"/></c:catAx>'
    )


def _eixo_val(id_, cruza, titulo, posicao="l", grade=True, cruza_em="autoZero", rotulos="nextTo", min_=None):
    escala = '<c:scaling><c:orientation val="minMax"/>' + (f'<c:min val="{min_}"/>' if min_ is not None else "") + "</c:scaling>"
    return (
        f'<c:valAx><c:axId val="{id_}"/>{escala}<c:delete val="0"/><c:axPos val="{posicao}"/>'
        + ('<c:majorGridlines><c:spPr><a:ln w="6350">' + _cor("D9D9D9") + "</a:ln></c:spPr></c:majorGridlines>" if grade else "")
        + _titulo_eixo(titulo, vertical=posicao in ("l", "r"))
        + '<c:numFmt formatCode="General" sourceLinked="0"/><c:majorTickMark val="out"/>'
        f'<c:minorTickMark val="none"/><c:tickLblPos val="{rotulos}"/>'
        '<c:spPr><a:ln w="9525">' + _cor("595959") + "</a:ln></c:spPr>"
        + _fonte()
        + f'<c:crossAx val="{cruza}"/><c:crosses val="{cruza_em}"/><c:crossBetween val="between"/></c:valAx>'
    )


def _legenda(posicao="b"):
    return f'<c:legend><c:legendPos val="{posicao}"/><c:overlay val="0"/>{_fonte()}</c:legend>'


def _espaco_grafico(plot, legenda=""):
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<c:chartSpace xmlns:c="{NS_C}" xmlns:a="{NS_A}" xmlns:r="{NS_R}">'
        '<c:date1904 val="0"/><c:roundedCorners val="0"/>'
        f'<c:chart><c:autoTitleDeleted val="1"/><c:plotArea><c:layout/>{plot}</c:plotArea>{legenda}'
        '<c:plotVisOnly val="1"/><c:dispBlanksAs val="gap"/></c:chart>'
        '<c:spPr><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'
        f'{_fonte()}<c:externalData r:id="rId1"><c:autoUpdate val="0"/></c:externalData></c:chartSpace>'
    )


# ---------------------------------------------------------------------------
# Os três gráficos do artigo
# ---------------------------------------------------------------------------
def _grafico_distribuicao():
    linhas = _ler("distribuicao_ideb")
    faixas = [f"{_br(float(l['inicio']), 1)}–{_br(float(l['fim']), 1)}" for l in linhas]
    contagem = [int(l["municipios"]) for l in linhas]
    n = len(linhas)
    serie = (
        '<c:ser><c:idx val="0"/><c:order val="0"/>' + _nome_serie("B", "Número de municípios")
        + "<c:spPr>" + _cor("4682B4") + '<a:ln w="9525">' + _cor("FFFFFF") + "</a:ln></c:spPr>"
        '<c:invertIfNegative val="0"/>'
        f"<c:cat>{_ref_texto(_intervalo('A', n), faixas)}</c:cat>"
        f"<c:val>{_ref_num(_intervalo('B', n), contagem)}</c:val></c:ser>"
    )
    plot = (
        '<c:barChart><c:barDir val="col"/><c:grouping val="clustered"/><c:varyColors val="0"/>'
        f'{serie}<c:gapWidth val="0"/><c:axId val="101"/><c:axId val="102"/></c:barChart>'
        + _eixo_cat(101, 102, "IDEB (anos iniciais do ensino fundamental)", rot=-2700000)
        + _eixo_val(102, 101, "Número de municípios")
    )
    planilha = _xlsx(["Faixa do IDEB", "Número de municípios"], [[f, c] for f, c in zip(faixas, contagem)])
    return _espaco_grafico(plot), planilha


def _grafico_elbow():
    linhas = _ler("elbow_silhouette")
    ks = [int(l["k"]) for l in linhas]
    inercia = [round(float(l["inercia"]), 4) for l in linhas]
    silhouette = [round(float(l["silhouette"]), 4) for l in linhas]
    n = len(linhas)
    nomes = ("Inércia (eixo esquerdo)", "Silhouette Score médio (eixo direito)")

    def linha(idx, coluna, nome, valores, cor):
        return (
            f'<c:ser><c:idx val="{idx}"/><c:order val="{idx}"/>{_nome_serie(coluna, nome)}'
            f'<c:spPr><a:ln w="28575" cap="rnd">{_cor(cor)}<a:round/></a:ln></c:spPr>'
            f'<c:marker><c:symbol val="circle"/><c:size val="6"/><c:spPr>{_cor(cor)}<a:ln w="9525">{_cor(cor)}</a:ln></c:spPr></c:marker>'
            f"<c:cat>{_ref_num(_intervalo('A', n), ks)}</c:cat>"
            f"<c:val>{_ref_num(_intervalo(coluna, n), valores)}</c:val><c:smooth val=\"0\"/></c:ser>"
        )

    plot = (
        '<c:lineChart><c:grouping val="standard"/><c:varyColors val="0"/>'
        + linha(0, "B", nomes[0], inercia, "4682B4")
        + '<c:marker val="1"/><c:axId val="201"/><c:axId val="202"/></c:lineChart>'
        '<c:lineChart><c:grouping val="standard"/><c:varyColors val="0"/>'
        + linha(1, "C", nomes[1], silhouette, "FF8C00")
        + '<c:marker val="1"/><c:axId val="203"/><c:axId val="204"/></c:lineChart>'
        + _eixo_cat(201, 202, "Número de clusters (k)")
        + _eixo_val(202, 201, "Inércia")
        + _eixo_cat(203, 204, apagado=True)
        + _eixo_val(204, 203, "Silhouette Score médio", posicao="r", grade=False, cruza_em="max", min_=0)
    )
    planilha = _xlsx(["k", nomes[0], nomes[1]], [[k, i, s] for k, i, s in zip(ks, inercia, silhouette)])
    return _espaco_grafico(plot, _legenda()), planilha


def _grafico_pca():
    linhas = _ler("pca_clusters")
    pc1 = [float(l["pc1"]) for l in linhas]
    pc2 = [float(l["pc2"]) for l in linhas]
    # com duas componentes, a variância explicada é a razão entre as variâncias amostrais
    v1, v2 = statistics.variance(pc1), statistics.variance(pc2)
    expl1, expl2 = 100 * v1 / (v1 + v2), 100 * v2 / (v1 + v2)

    # leiaute usual do Excel: uma coluna de X compartilhada e uma coluna de Y por grupo (vazia fora do grupo)
    grupos = [("vulneráveis", "Vulneráveis", "D62728"), ("intermediários", "Intermediários", "1F77B4"),
              ("alta renda", "Alta renda", "2CA02C")]
    n = len(linhas)
    x = [round(v, 5) for v in pc1]
    colunas_y = [[round(float(l["pc2"]), 5) if l["grupo"] == chave else None for l in linhas]
                 for chave, _, _ in grupos]
    series = []
    for idx, ((_, rotulo, cor), y) in enumerate(zip(grupos, colunas_y)):
        coluna = _coluna(2 + idx)
        series.append(
            f'<c:ser><c:idx val="{idx}"/><c:order val="{idx}"/>{_nome_serie(coluna, rotulo)}'
            '<c:spPr><a:ln w="19050"><a:noFill/></a:ln></c:spPr>'
            f'<c:marker><c:symbol val="circle"/><c:size val="6"/><c:spPr>{_cor(cor)}<a:ln w="9525">{_cor("FFFFFF")}</a:ln></c:spPr></c:marker>'
            f"<c:xVal>{_ref_num(_intervalo('B', n), x)}</c:xVal>"
            f"<c:yVal>{_ref_num(_intervalo(coluna, n), y)}</c:yVal><c:smooth val=\"0\"/></c:ser>"
        )
    plot = (
        '<c:scatterChart><c:scatterStyle val="lineMarker"/><c:varyColors val="0"/>'
        + "".join(series) + '<c:axId val="301"/><c:axId val="302"/></c:scatterChart>'
        + _eixo_val(301, 302, f"PC1 ({_br(expl1, 1)}% da variância)", posicao="b", grade=False, rotulos="low")
        + _eixo_val(302, 301, f"PC2 ({_br(expl2, 1)}% da variância)", rotulos="low")
    )
    planilha = _xlsx(
        ["Município", "PC1"] + [r for _, r, _ in grupos],
        [[l["municipio"], a] + [col[i] for col in colunas_y] for i, (l, a) in enumerate(zip(linhas, x))],
    )
    return _espaco_grafico(plot, _legenda()), planilha


# trecho inicial do título da legenda -> construtor do gráfico
GRAFICOS = [
    ("Distribuição do IDEB", _grafico_distribuicao),
    ("Curvas de inércia", _grafico_elbow),
    ("Projeção dos clusters", _grafico_pca),
]


# ---------------------------------------------------------------------------
# Pós-processamento do .docx
# ---------------------------------------------------------------------------
def _desenho(rid, numero, descricao):
    return (
        "<w:drawing><wp:inline distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\">"
        f'<wp:extent cx="{LARGURA}" cy="{ALTURA}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{9000 + numero}" name="Gráfico {numero}" descr="{escape(descricao, {chr(34): "&quot;"})}"/>'
        "<wp:cNvGraphicFramePr/>"
        f'<a:graphic xmlns:a="{NS_A}"><a:graphicData uri="{NS_C}">'
        f'<c:chart xmlns:c="{NS_C}" xmlns:r="{NS_R}" r:id="{rid}"/>'
        "</a:graphicData></a:graphic></wp:inline></w:drawing>"
    )


def incorporar_graficos(caminho):
    """Troca as imagens dos gráficos do .docx por gráficos nativos; sem efeito se não houver gráficos."""
    with zipfile.ZipFile(caminho) as z:
        itens = {i.filename: (i, z.read(i.filename)) for i in z.infolist()}
    xml = itens["word/document.xml"][1].decode("utf-8")
    rels = itens["word/_rels/document.xml.rels"][1].decode("utf-8")
    tipos = itens["[Content_Types].xml"][1].decode("utf-8")

    novos, removidos = {}, []
    paragrafos = list(re.finditer(r"<w:p>.*?</w:p>", xml, flags=re.S))
    substituicoes = []  # (início, fim, novo texto do parágrafo da imagem)
    numero = 0
    for i, p in enumerate(paragrafos[:-1]):
        texto = "".join(re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", p.group(0)))
        m = re.match(r"Gráfico (\d+)\s*–\s*(.*)", texto)
        proximo = paragrafos[i + 1]
        if not m or "<w:drawing>" not in proximo.group(0):
            continue
        for prefixo, construtor in GRAFICOS:
            if m.group(2).startswith(prefixo):
                break
        else:
            continue
        numero += 1
        grafico, planilha = construtor()
        rid = f"rIdGrafico{numero}"
        novos[f"word/charts/chart{numero}.xml"] = grafico.encode("utf-8")
        novos[f"word/charts/_rels/chart{numero}.xml.rels"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<Relationships xmlns="{NS_PKG}"><Relationship Id="rId1" Type="{NS_R}/package" '
            f'Target="../embeddings/Microsoft_Excel_Sheet{numero}.xlsx"/></Relationships>'
        ).encode("utf-8")
        novos[f"word/embeddings/Microsoft_Excel_Sheet{numero}.xlsx"] = planilha
        rels = rels.replace("</Relationships>", f'<Relationship Id="{rid}" Type="{NS_R}/chart" Target="charts/chart{numero}.xml"/></Relationships>')
        tipos = tipos.replace(
            "</Types>",
            f'<Override PartName="/word/charts/chart{numero}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.drawingml.chart+xml"/></Types>',
        )
        antigo = proximo.group(0)
        removidos += re.findall(r'r:embed="([^"]+)"', antigo)
        novo = re.sub(r"<w:drawing>.*?</w:drawing>", lambda _: _desenho(rid, numero, m.group(2)), antigo, flags=re.S)
        substituicoes.append((proximo.start(), proximo.end(), novo))

    if not substituicoes:
        return
    for inicio, fim, novo in reversed(substituicoes):
        xml = xml[:inicio] + novo + xml[fim:]
    if 'Extension="xlsx"' not in tipos:
        tipos = tipos.replace(
            "<Override",
            '<Default Extension="xlsx" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"/><Override',
            1,
        )

    # remove as imagens que deixaram de ser usadas
    descartados = set()
    for rid in removidos:
        if f'r:embed="{rid}"' in xml:
            continue
        m = re.search(rf'<Relationship\b[^>]*\bId="{rid}"[^>]*/>', rels)
        if not m:
            continue
        alvo = re.search(r'Target="([^"]+)"', m.group(0)).group(1)
        rels = rels.replace(m.group(0), "")
        if len(re.findall(rf'Target="{re.escape(alvo)}"', rels)) == 0:
            descartados.add(f"word/{alvo}")

    itens["word/document.xml"] = (itens["word/document.xml"][0], xml.encode("utf-8"))
    itens["word/_rels/document.xml.rels"] = (itens["word/_rels/document.xml.rels"][0], rels.encode("utf-8"))
    itens["[Content_Types].xml"] = (itens["[Content_Types].xml"][0], tipos.encode("utf-8"))
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, (info, dados) in itens.items():
            if nome not in descartados:
                z.writestr(info, dados)
        for nome, dados in novos.items():
            z.writestr(nome, dados)
