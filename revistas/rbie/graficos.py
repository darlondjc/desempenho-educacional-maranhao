"""Gera as figuras vetoriais (PDF) do artigo da RBIE a partir dos CSVs em
dados_graficos/, exportados por src/analytics.py.

A RBIE pede figuras vetoriais e que a informação não dependa só da cor,
por isso cada grupo tem cor e marcador próprios.
Uso: uv run python revistas/rbie/graficos.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

AQUI = Path(__file__).parent
DADOS, SAIDA = AQUI / "dados_graficos", AQUI / "images"

plt.rcParams.update({"font.family": "serif", "font.size": 9,
                     "axes.formatter.use_locale": False})


def br(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def pca_clusters():
    df = pd.read_csv(DADOS / "pca_clusters.csv", sep=";")
    var1 = df["pc1"].var() / (df["pc1"].var() + df["pc2"].var()) * 100
    estilos = [("vulneráveis", "Vulnerável", "#b2182b", "o"),
               ("intermediários", "Intermediário", "#2166ac", "s"),
               ("alta renda", "Alta renda", "#1b7837", "^")]
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    for grupo, rotulo, cor, marca in estilos:
        sub = df[df["grupo"] == grupo]
        ax.scatter(sub["pc1"], sub["pc2"], c=cor, marker=marca, s=14, alpha=0.75,
                   linewidths=0, label=f"{rotulo} (n = {len(sub)})")
    ax.set_xlabel(f"PC1 ({br(var1)}% da variância)")
    ax.set_ylabel(f"PC2 ({br(100 - var1)}% da variância)")
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: br(v, 1) if v % 1 else f"{v:.0f}")
    ax.xaxis.set_major_formatter(fmt)
    ax.yaxis.set_major_formatter(fmt)
    ax.legend(frameon=False, fontsize=7.5, handletextpad=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    SAIDA.mkdir(exist_ok=True)
    fig.savefig(SAIDA / "pca_clusters.pdf")
    plt.close(fig)


def distribuicao_ideb():
    df = pd.read_csv(DADOS / "distribuicao_ideb.csv", sep=";")
    fig, ax = plt.subplots(figsize=(3.4, 2.2))
    ax.bar(df["inicio"], df["municipios"], width=df["fim"] - df["inicio"], align="edge",
           color="#4d4d4d", edgecolor="white", linewidth=0.6)
    ax.axvline(5.39, color="#b2182b", linestyle="--", linewidth=1, label="Média (5,39)")
    ax.axvline(5.30, color="#2166ac", linestyle=":", linewidth=1.2, label="Mediana (5,30)")
    ax.set_xlabel("IDEB 2025 (anos iniciais, rede municipal)")
    ax.set_ylabel("Número de municípios")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: br(v, 1)))
    ax.legend(frameon=False, fontsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(SAIDA / "distribuicao_ideb.pdf")
    plt.close(fig)


def elbow_silhouette():
    df = pd.read_csv(DADOS / "elbow_silhouette.csv", sep=";")
    melhor = df.loc[df["silhouette"].idxmax()]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.4, 2.2))
    a1.plot(df["k"], df["inercia"], marker="o", ms=3.5, color="#4d4d4d", linewidth=1.2)
    a1.set_xlabel("Número de grupos ($k$)")
    a1.set_ylabel("Inércia")
    a1.set_title("(a) Inércia (cotovelo)", fontsize=9)
    a2.plot(df["k"], df["silhouette"], marker="s", ms=3.5, color="#2166ac", linewidth=1.2)
    a2.axvline(melhor["k"], color="#b2182b", linestyle="--", linewidth=1,
               label=f"$k = {int(melhor['k'])}$ ({br(melhor['silhouette'], 3)})")
    a2.set_xlabel("Número de grupos ($k$)")
    a2.set_ylabel("Silhouette médio")
    a2.set_title("(b) Silhouette Score", fontsize=9)
    a2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: br(v, 2)))
    a2.legend(frameon=False, fontsize=7.5)
    for ax in (a1, a2):
        ax.set_xticks(df["k"])
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(SAIDA / "elbow_silhouette.pdf")
    plt.close(fig)


if __name__ == "__main__":
    SAIDA.mkdir(exist_ok=True)
    pca_clusters()
    distribuicao_ideb()
    elbow_silhouette()
    print("figuras geradas em images/")
