DOCBASE=qtoscillo
INPUTFILES=$(DOCBASE).md defaults.yaml metadata.yaml

.PNONY: all watch clean

all: $(DOCBASE).pdf

$(DOCBASE).pdf: ${DOCBASE}.tex
	latexmk -use-make -pdf -xelatex $<

$(DOCBASE).tex: $(INPUTFILES)
	pandoc -d defaults.yaml

watch:
	fswatch -0 $(INPUTFILES) |	\
	while read -d "" event;		\
	do				\
		make -f Makefile all;	\
	done

clean:
	rm -f $(DOCBASE).aux ${DOCBASE}.log ${DOCBASE}.nav ${DOCBASE}.pdf   \
		$(DOCBASE).snm ${DOCBASE}.tex ${DOCBASE}.toc ${DOCBASE}.vrb \
		$(DOCBASE).fdb_latexmk ${DOCBASE}.fls ${DOCBASE}.xdv
