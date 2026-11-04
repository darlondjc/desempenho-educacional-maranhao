"""Converte o references.bib (biblatex/ABNT, revista Debates) para o refs.bib
da RBIE (BibTeX + apalike-sol.bst, que não tem campo url).

Regras: com DOI, a URL sai; sem DOI, a URL vai para howpublished (@misc) ou
note (demais tipos). Campos que o BibTeX ignora (urldate, editortype, venue,
eventtitle) são removidos.
Uso: python3 converter_bib.py ../debates-em-educacao/references.bib refs.bib
"""
import re
import sys

BOOKTITLE = {
    "benhur2002": "Proceedings of the Pacific Symposium on Biocomputing 2002",
    "macqueen1967": "Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability",
}
REMOVER = {"urldate", "editortype", "venue", "eventtitle"}

def campos(corpo):
    out, pos = [], 0
    while True:
        m = re.compile(r"\s*(\w+)\s*=\s*\{").match(corpo, pos)
        if not m:
            break
        nome, j, nivel = m.group(1).lower(), m.end(), 1
        while nivel:
            c = corpo[j]
            nivel += c == "{"
            nivel -= c == "}"
            j += 1
        out.append([nome, corpo[m.end():j - 1]])
        pos = j
        m2 = re.compile(r"\s*,").match(corpo, pos)
        if m2:
            pos = m2.end()
    return out

src, dst = sys.argv[1], sys.argv[2]
texto = open(src, encoding="utf-8").read()
saida = []
for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", texto, re.S):
    tipo, chave, corpo = m.group(1).lower(), m.group(2).strip(), m.group(3)
    f = dict(campos(corpo))
    ordem = [k for k, _ in campos(corpo)]
    url = f.pop("url", None)
    for k in REMOVER:
        f.pop(k, None)
    if chave in BOOKTITLE:
        f["booktitle"] = BOOKTITLE[chave]
    if url and "doi" not in f:
        if tipo == "misc":
            partes = [f.pop("publisher", None), f.pop("note", None)]
            f.pop("address", None)
            f["howpublished"] = ", ".join(p for p in partes if p) + (", " if any(partes) else "") + r"\url{" + url + "}"
        else:
            f["note"] = (f["note"] + ". " if "note" in f else "") + r"\url{" + url + "}"
    chaves = [k for k in ordem if k in f] + [k for k in f if k not in ordem]
    largura = max(len(k) for k in chaves)
    linhas = ",\n".join(f"  {k.ljust(largura)} = {{{f[k]}}}" for k in chaves)
    saida.append(f"@{tipo}{{{chave},\n{linhas}\n}}\n")

open(dst, "w", encoding="utf-8").write("\n".join(saida))
print(f"{len(saida)} entradas convertidas")
