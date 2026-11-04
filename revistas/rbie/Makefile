# Artigo no template rbie2026 (RBIE).
#   make               -> versão anônima (submissão) e identificada, em submissao/
#   make anonimo       -> só a versão anônima
#   make identificado  -> só a versão identificada
#   make graficos      -> regenera as figuras vetoriais a partir de dados_graficos/
LATEXMK = latexmk -lualatex -interaction=nonstopmode -halt-on-error

.PHONY: all anonimo identificado graficos clean carta

all: anonimo identificado

anonimo:
	$(LATEXMK) main.tex
	mkdir -p submissao
	cp main.pdf submissao/artigo_anonimo.pdf

identificado:
	$(LATEXMK) -jobname=main_identificado -usepretex='\def\versaoidentificada{}' main.tex
	mkdir -p submissao
	cp main_identificado.pdf submissao/artigo_identificado.pdf

graficos:
	cd ../.. && uv run python revistas/rbie/graficos.py

clean:
	latexmk -c main.tex
	latexmk -c -jobname=main_identificado main.tex
	latexmk -c coverletter.tex

carta:
	latexmk -lualatex -interaction=nonstopmode coverletter.tex
	mkdir -p submissao
	cp coverletter.pdf submissao/carta_apresentacao.pdf
