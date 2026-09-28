# Compilação do artigo no template da revista Debates em Educação.
#   make        -> PDFs (prévia) e .docx (submissão) em submissao/
#   make pdf    -> somente os PDFs
#   make docx   -> somente os .docx
LATEXMK = latexmk -lualatex -interaction=nonstopmode -halt-on-error

.PHONY: all pdf docx clean

all: pdf docx

pdf:
	$(LATEXMK) main.tex
	$(LATEXMK) -jobname=main_identificado -usepretex='\def\versaoidentificada{}' main.tex
	mkdir -p submissao
	cp main.pdf submissao/artigo_sem_identificacao.pdf
	cp main_identificado.pdf submissao/artigo_identificado.pdf

docx:
	python3 build_docx.py

clean:
	latexmk -c main.tex
	latexmk -c -jobname=main_identificado main.tex
