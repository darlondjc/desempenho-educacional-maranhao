#!/usr/bin/env python3
"""Gera as versões Word (.docx) do artigo no template da revista Debates em Educação.

A revista só aceita submissões em Word, baseadas no template oficial
(template/template_debates_educacao_2026.docx). Este script usa os mesmos
arquivos .tex do PDF e produz, em submissao/:

  - artigo_sem_identificacao.docx  -> arquivo para avaliação às cegas;
  - artigo_identificado.docx       -> versão final, após aprovação;
  - informacao_autores.docx        -> dados de autoria (arquivo separado).

Cabeçalhos, rodapés, margens e logotipos vêm do próprio template; os estilos
de parágrafo seguem as especificações descritas nele.

Uso: python3 build_docx.py   (requer pandoc >= 3.0)
"""

import json
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

DIR = Path(__file__).resolve().parent
TEMPLATE = DIR / "template" / "template_debates_educacao_2026.docx"
CSL = DIR / "template" / "abnt.csl"
FILTRO = DIR / "template" / "filtro_docx.lua"
SAIDA = DIR / "submissao"

SECOES = [
    "1_introducao.tex",
    "2_referencial_teorico.tex",
    "3_procedimentos_metodologicos.tex",
    "4_resultados_discussao.tex",
    "5_consideracoes_finais.tex",
]
COMPLEMENTARES = "6_informacoes_complementares.tex"

# Definições para o leitor LaTeX do pandoc (equivalentes às de debates.sty).
MACROS_PANDOC = r"""
\newenvironment{grafico}{\begin{figure}}{\end{figure}}
\newenvironment{quadro}{\begin{table}}{\end{table}}
\newcommand{\corpodez}{}
\newcommand{\fonte}[1]{\begin{fontebloco}Fonte: #1\end{fontebloco}}
\newcommand{\nota}[1]{\begin{notabloco}Nota: #1\end{notabloco}}
"""

AZUL = "0000FE"
LINHA_EM_BRANCO = "414"  # uma linha de espaçamento 1,5 em Arial 12 (twips)


# ---------------------------------------------------------------------------
# Metadados
# ---------------------------------------------------------------------------
def ler_metadados():
    texto = (DIR / "metadados.tex").read_text(encoding="utf-8")
    meta, autores = {}, []
    for linha in texto.splitlines():
        m = re.match(r"^\\newcommand\{\\(\w+)\}\{(.*)\}\s*$", linha)
        if m:
            # itálico do LaTeX -> Markdown (o texto entra no front matter em Markdown)
            meta[m.group(1)] = re.sub(r"\\textit\{([^{}]*)\}", r"*\1*", m.group(2))
        m = re.match(r"^\\autor\{(.*?)\}\{(.*?)\}\{(.*)\}\s*$", linha)
        if m:
            autores.append(m.groups())
    return meta, autores


def bloco(estilo, texto, idioma=None):
    attrs = f'custom-style="{estilo}"'
    if idioma:
        attrs += f' lang="{idioma}"'
    return f"::: {{{attrs}}}\n{texto}\n:::\n\n"


def rotulo(texto):
    return f'[{texto}]{{custom-style="Rotulo Palavras-chave"}}'


def front_matter(meta, autores, identificado):
    md = bloco("Titulo PT", meta["tituloPT"])
    md += bloco("Titulo Estrangeiro", meta["tituloEN"], "en-US")
    md += bloco("Titulo Estrangeiro", meta["tituloES"], "es-ES")
    if identificado:
        for nome, inst, nota in autores:
            md += bloco("Autor", f"{nome}^[{nota}]")
            md += bloco("Autor Instituicao", inst)
    md += bloco("Resumo Titulo", "Resumo")
    md += bloco("Resumo Texto", meta["resumoPT"])
    md += bloco("Palavras-chave", f"{rotulo('Palavras-chave:')} {meta['palavrasPT']}")
    md += bloco("Resumo Titulo Estrangeiro", "Abstract", "en-US")
    md += bloco("Resumo Texto Estrangeiro", meta["resumoEN"], "en-US")
    md += bloco("Palavras-chave Estrangeiro", f"{rotulo('Keywords:')} {meta['palavrasEN']}", "en-US")
    md += bloco("Resumo Titulo Estrangeiro", "Resumen", "es-ES")
    md += bloco("Resumo Texto Estrangeiro", meta["resumoES"], "es-ES")
    md += bloco("Palavras-chave Estrangeiro", f"{rotulo('Palabras-clave:')} {meta['palavrasES']}", "es-ES")
    return md


# ---------------------------------------------------------------------------
# Conversão com pandoc
# ---------------------------------------------------------------------------
def pandoc_json(texto, formato):
    r = subprocess.run(
        ["pandoc", "-f", formato, "-t", "json"],
        input=texto, capture_output=True, text=True, check=True, cwd=DIR,
    )
    return json.loads(r.stdout)


def larguras_das_colunas(m):
    """Simplifica a especificação da tabular para o leitor do pandoc.

    O pandoc descarta o conteúdo de \\multicolumn quando as colunas têm
    prefixos >{...} e ignora larguras relativas a \\textwidth; as larguras
    são repassadas ao filtro Lua em um bloco "larguras".
    """
    spec = re.sub(r">\{[^{}]*\}", "", m.group(1))
    fracoes = re.findall(r"p\{([\d.]+)\\textwidth\}", spec)
    marcador = ""
    if fracoes and len(fracoes) == len(re.findall(r"[lcrp]", re.sub(r"\{[^{}]*\}", "", spec))):
        marcador = "\\begin{larguras}" + ";".join(fracoes) + "\\end{larguras}\n"
    return marcador + "\\begin{tabular}{" + spec + "}"


def ler_tex(nome, identificado):
    texto = (DIR / nome).read_text(encoding="utf-8")
    trecho = r"\1" if identificado else ""
    texto = re.sub(r"\\ifidentificado(.*?)\\fi", trecho, texto, flags=re.S)
    return re.sub(r"\\begin\{tabular\}\{((?:[^{}]|\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})*)\}",
                  larguras_das_colunas, texto)


def documento(meta, autores, identificado):
    doc = pandoc_json(front_matter(meta, autores, identificado), "markdown")
    corpo = MACROS_PANDOC + "\n".join(ler_tex(s, identificado) for s in SECOES)
    doc["blocks"] += pandoc_json(corpo, "latex")["blocks"]
    doc["blocks"] += pandoc_json("# REFERÊNCIAS\n\n::: {#refs}\n:::\n", "markdown")["blocks"]
    doc["blocks"] += pandoc_json(ler_tex(COMPLEMENTARES, identificado), "latex")["blocks"]
    return doc


def gerar_docx(doc, destino, referencia):
    subprocess.run(
        [
            "pandoc", "-f", "json", "-t", "docx",
            "--citeproc",
            "--lua-filter", str(FILTRO),
            "--reference-doc", str(referencia),
            "--resource-path", f"{DIR}:{DIR / 'images'}",
            "-M", "bibliography=references.bib",
            "-M", f"csl={CSL}",
            "-M", "lang=pt-BR",
            "-M", "link-citations=false",
            "-o", str(destino),
        ],
        input=json.dumps(doc), text=True, check=True, cwd=DIR,
    )
    ajustar_tabelas(destino)


# ---------------------------------------------------------------------------
# Documento de referência (template + estilos do pandoc)
# ---------------------------------------------------------------------------
def rpr(tamanho=24, negrito=False, italico=False, cor=None, sobrescrito=False):
    x = ""
    if negrito:
        x += "<w:b/><w:bCs/>"
    if italico:
        x += "<w:i/><w:iCs/>"
    if cor:
        x += f'<w:color w:val="{cor}"/>'
    if tamanho:
        x += f'<w:sz w:val="{tamanho}"/><w:szCs w:val="{tamanho}"/>'
    if sobrescrito:
        x += '<w:vertAlign w:val="superscript"/>'
    return f"<w:rPr>{x}</w:rPr>"


def ppr(alinhamento="both", linha=240, antes=0, depois=0, recuo=0, esquerda=0,
        manter_proximo=False, nivel=None):
    x = ""
    if manter_proximo:
        x += "<w:keepNext/><w:keepLines/>"
    x += (f'<w:spacing w:before="{antes}" w:after="{depois}" '
          f'w:line="{linha}" w:lineRule="auto"/>')
    x += f'<w:ind w:left="{esquerda}" w:firstLine="{recuo}"/>'
    x += f'<w:jc w:val="{alinhamento}"/>'
    if nivel is not None:
        x += f'<w:outlineLvl w:val="{nivel}"/>'
    return f"<w:pPr>{x}</w:pPr>"


def estilo_par(sid, nome, p, r, base="Normal"):
    return (f'<w:style w:type="paragraph" w:customStyle="1" w:styleId="{sid}">'
            f'<w:name w:val="{nome}"/><w:basedOn w:val="{base}"/><w:qFormat/>{p}{r}</w:style>')


def estilo_car(sid, nome, r):
    return (f'<w:style w:type="character" w:customStyle="1" w:styleId="{sid}">'
            f'<w:name w:val="{nome}"/><w:qFormat/>{r}</w:style>')


def estilos_debates():
    corpo = ppr(linha=360, recuo=709)
    titulo_secao = ppr(antes=LINHA_EM_BRANCO, depois=LINHA_EM_BRANCO, manter_proximo=True)
    return [
        # Corpo do texto: Arial 12, justificado, recuo 1,25 cm, espaçamento 1,5.
        estilo_par("BodyText", "Body Text", corpo, rpr()),
        estilo_par("FirstParagraph", "First Paragraph", corpo, rpr(), base="BodyText"),
        estilo_par("Compact", "Compact", ppr(linha=360), rpr(), base="BodyText"),
        estilo_par("BlockText", "Block Text", ppr(esquerda=2268, antes=240, depois=240), rpr(22)),
        # Títulos de seção e subseção: Arial 12, negrito, azul, sem numeração.
        estilo_par("Heading1", "heading 1", ppr(antes=LINHA_EM_BRANCO, depois=LINHA_EM_BRANCO,
                                                 manter_proximo=True, nivel=0), rpr(negrito=True, cor=AZUL)),
        estilo_par("Heading2", "heading 2", ppr(antes=LINHA_EM_BRANCO, depois=LINHA_EM_BRANCO,
                                                 manter_proximo=True, nivel=1), rpr(negrito=True, cor=AZUL)),
        estilo_par("Heading3", "heading 3", ppr(antes=LINHA_EM_BRANCO, depois=LINHA_EM_BRANCO,
                                                 manter_proximo=True, nivel=2), rpr(negrito=True, cor=AZUL)),
        # Títulos do artigo.
        estilo_par("TituloPT", "Titulo PT", ppr("center", depois=LINHA_EM_BRANCO),
                   rpr(28, negrito=True, cor=AZUL)),
        estilo_par("TituloEstrangeiro", "Titulo Estrangeiro", ppr("center", depois=LINHA_EM_BRANCO),
                   rpr(negrito=True, italico=True)),
        # Autoria (somente na versão identificada).
        estilo_par("Autor", "Autor", ppr("right"), rpr(cor=AZUL)),
        estilo_par("AutorInstituicao", "Autor Instituicao", ppr("right", depois=LINHA_EM_BRANCO), rpr(cor=AZUL)),
        # Resumos e palavras-chave.
        estilo_par("ResumoTitulo", "Resumo Titulo", titulo_secao, rpr(negrito=True, cor=AZUL)),
        estilo_par("ResumoTituloEstrangeiro", "Resumo Titulo Estrangeiro", titulo_secao,
                   rpr(negrito=True, italico=True, cor=AZUL)),
        estilo_par("ResumoTexto", "Resumo Texto", ppr(), rpr()),
        estilo_par("ResumoTextoEstrangeiro", "Resumo Texto Estrangeiro", ppr(), rpr(italico=True)),
        estilo_par("Palavraschave", "Palavras-chave", ppr("left", antes=LINHA_EM_BRANCO), rpr()),
        estilo_par("PalavraschaveEstrangeiro", "Palavras-chave Estrangeiro", ppr("left", antes=LINHA_EM_BRANCO),
                   rpr(italico=True)),
        estilo_car("RotuloPalavraschave", "Rotulo Palavras-chave", rpr(None, negrito=True, cor=AZUL)),
        # Ilustrações: título Arial 11 acima; fonte e nota Arial 10 abaixo.
        estilo_par("Legenda", "Legenda", ppr("center", antes=LINHA_EM_BRANCO, depois=60, manter_proximo=True),
                   rpr(22)),
        estilo_par("FiguraImagem", "Figura Imagem", ppr("center", manter_proximo=True), rpr()),
        estilo_par("Nota", "Nota", ppr("center", antes=60), rpr(20)),
        estilo_par("Fonte", "Fonte", ppr("center", antes=60, depois=LINHA_EM_BRANCO), rpr(20)),
        estilo_par("TabelaTexto", "Tabela Texto", ppr("left"), rpr(20)),
        estilo_par("Lista", "Lista", ppr(linha=360), rpr()),
        # Notas de rodapé: Arial 10, espaço simples, justificadas.
        estilo_par("FootnoteText", "footnote text", ppr(), rpr(20)),
        estilo_car("FootnoteReference", "footnote reference", rpr(None, sobrescrito=True)),
        # Referências: Arial 12, alinhadas à esquerda, espaço simples, separadas por uma linha.
        estilo_par("Bibliography", "Bibliography", ppr("left", depois=240), rpr()),
        (
            '<w:style w:type="table" w:styleId="Table"><w:name w:val="Table"/>'
            '<w:basedOn w:val="TableNormal"/><w:tblPr><w:jc w:val="center"/>'
            '<w:tblCellMar><w:left w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/>'
            '</w:tblCellMar></w:tblPr></w:style>'
        ),
    ]


def substituir_estilos(xml):
    ids = ["Heading1", "Heading2", "Heading3", "Title", "Subtitle", "Table"]
    for sid in ids:
        xml = re.sub(rf'<w:style [^>]*w:styleId="{sid}"[^>]*>.*?</w:style>', "", xml, flags=re.S)
    xml = xml.replace('w:val="pt_BR"', 'w:val="pt-BR"')
    return xml.replace("</w:styles>", "".join(estilos_debates()) + "</w:styles>")


def selecionar_tipo_artigo(xml):
    """No cabeçalho da 1ª página, mantém apenas o tipo 'Artigo | Article'."""
    for par in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        textos = re.findall(r"<w:t(?: [^>]*)?>[^<]*</w:t>", par)
        conteudo = "".join(re.sub(r"<[^>]+>", "", t) for t in textos)
        if conteudo.startswith("Artigo | Article ou"):
            novo = par
            for i, t in enumerate(textos):
                valor = "Artigo | Article" if i == 0 else ""
                novo = novo.replace(t, f'<w:t xml:space="preserve">{valor}</w:t>', 1)
            xml = xml.replace(par, novo)
    return xml


def esvaziar_corpo(xml):
    corpo = re.search(r"<w:body>(.*)</w:body>", xml, flags=re.S).group(1)
    sect = re.findall(r"<w:sectPr.*?</w:sectPr>", corpo, flags=re.S)[-1]
    return xml.replace(corpo, "<w:p/>" + sect)


def criar_referencia(destino):
    with zipfile.ZipFile(TEMPLATE) as zin, zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            dados = zin.read(item.filename)
            if item.filename == "word/styles.xml":
                dados = substituir_estilos(dados.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/document.xml":
                dados = esvaziar_corpo(dados.decode("utf-8")).encode("utf-8")
            elif re.match(r"word/header\d+\.xml", item.filename):
                dados = selecionar_tipo_artigo(dados.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/fontTable.xml":
                # O pandoc não copia word/fonts/; remove as fontes embutidas
                # (Garamond, não usada no texto) para não deixar referências quebradas.
                dados = re.sub(r"<w:embed\w+ [^>]*/>", "", dados.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/_rels/fontTable.xml.rels" or item.filename.startswith("word/fonts/"):
                continue
            zout.writestr(item, dados)


# ---------------------------------------------------------------------------
# Bordas: quadros com bordas internas e externas; tabelas (padrão IBGE) só
# com as linhas do cabeçalho e de fechamento.
# ---------------------------------------------------------------------------
def borda(lado, espessura=6):
    return f'<w:{lado} w:val="single" w:sz="{espessura}" w:space="0" w:color="000000"/>'


def ajustar_tabelas(caminho):
    with zipfile.ZipFile(caminho) as z:
        itens = {i.filename: (i, z.read(i.filename)) for i in z.infolist()}
    xml = itens["word/document.xml"][1].decode("utf-8")

    def ajustar(m):
        antes, tabela = m.group(1), m.group(2)
        # conteúdo de quadros e tabelas em Arial 10, espaço simples
        tabela = tabela.replace('<w:pStyle w:val="Compact" />', '<w:pStyle w:val="TabelaTexto" />')
        legenda = re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", antes)
        tipo = legenda[0] if legenda else ""
        if tipo.startswith("Quadro"):
            bordas = "".join(borda(l) for l in ("top", "left", "bottom", "right", "insideH", "insideV"))
            tabela = re.sub(r"<w:tblBorders>.*?</w:tblBorders>", "", tabela, flags=re.S)
            tabela = tabela.replace("<w:tblPr>", f"<w:tblPr><w:tblBorders>{bordas}</w:tblBorders>", 1)
        elif tipo.startswith("Tabela"):
            bordas = borda("top") + borda("bottom")
            tabela = re.sub(r"<w:tblBorders>.*?</w:tblBorders>", "", tabela, flags=re.S)
            tabela = tabela.replace("<w:tblPr>", f"<w:tblPr><w:tblBorders>{bordas}</w:tblBorders>", 1)
            linhas = re.findall(r"<w:tr[ >].*?</w:tr>", tabela, flags=re.S)
            if linhas:
                cab = linhas[0]
                novo = re.sub(r"<w:tcPr>", f"<w:tcPr><w:tcBorders>{borda('bottom')}</w:tcBorders>", cab)
                novo = re.sub(r"<w:tc>(?!<w:tcPr>)", f"<w:tc><w:tcPr><w:tcBorders>{borda('bottom')}</w:tcBorders></w:tcPr>", novo)
                tabela = tabela.replace(cab, novo, 1)
        return antes + tabela

    # parágrafo de legenda imediatamente anterior a cada tabela
    xml = re.sub(r"(<w:p>(?:(?!<w:p>).)*?</w:p>)(<w:tbl>.*?</w:tbl>)", ajustar, xml, flags=re.S)

    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, (info, dados) in itens.items():
            if nome == "word/document.xml":
                dados = xml.encode("utf-8")
            z.writestr(info, dados)


# ---------------------------------------------------------------------------
# Arquivo com os dados de autoria
# ---------------------------------------------------------------------------
def informacao_autores(meta, autores):
    md = bloco("Resumo Titulo", "Informação dos autores")
    md += bloco("Titulo PT", meta["tituloPT"])
    for nome, inst, nota in autores:
        md += bloco("Resumo Titulo", nome)
        md += bloco("Resumo Texto", f"**Instituição de vínculo:** {inst}")
        md += bloco("Resumo Texto", f"**Titulação, instituição, ORCID e e-mail:** {nota}")
    return pandoc_json(md, "markdown")


def main():
    SAIDA.mkdir(exist_ok=True)
    meta, autores = ler_metadados()
    with tempfile.TemporaryDirectory() as tmp:
        referencia = Path(tmp) / "referencia.docx"
        criar_referencia(referencia)
        gerar_docx(documento(meta, autores, False), SAIDA / "artigo_sem_identificacao.docx", referencia)
        gerar_docx(documento(meta, autores, True), SAIDA / "artigo_identificado.docx", referencia)
        gerar_docx(informacao_autores(meta, autores), SAIDA / "informacao_autores.docx", referencia)
    for arq in sorted(SAIDA.glob("*.docx")):
        print(f"gerado: {arq.relative_to(DIR)}")


if __name__ == "__main__":
    main()
