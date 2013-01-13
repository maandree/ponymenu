# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.
# 
# [GNU All Permissive License]

#SHELL=sh

PREFIX=/usr
BINDIR=/bin
DATADIR=/share
SYSCONFDIR=/etc

PROGRAM=ponymenu
BOOK=ponymenu
BOOKDIR=
LANG=en_GB-ise-w_accents-only


all: info


info: $(BOOK).info.gz
%.info: $(BOOKDIR)%.texinfo
	$(MAKEINFO) "$<"
%.info.gz: %.info
	gzip -9c < "$<" > "$@"


pdf: $(BOOK).pdf
%.pdf: $(BOOKDIR)%.texinfo 
	texi2pdf "$<"
	make clean-tex clean.bak-

pdf.gz: $(BOOK).pdf.gz
%.pdf.gz: %.pdf
	gzip -9c < "$<" > "$@"

pdf.xz: $(BOOK).pdf.xz
%.pdf.xz: %.pdf
	xz -e9 < "$<" > "$@"


dvi: $(BOOK).dvi
%.dvi: $(BOOKDIR)%.texinfo 
	$(TEXI2DVI) "$<"
	make clean-tex clean.bak-

dvi.gz: $(BOOK).dvi.gz
%.dvi.gz: %.dvi
	gzip -9c < "$<" > "$@"

dvi.xz: $(BOOK).dvi.xz
%.dvi.xz: %.dvi
	xz -e9 < "$<" > "$@"


.PHONY: soft
soft: ; pdfjam --pagecolor 249,249,249 -o "$(BOOK).pdf" "$(BOOK).pdf"

.PHONY: softer
softer: ; pdfjam --pagecolor 249,246,240 -o "$(BOOK).pdf" "$(BOOK).pdf"

.PHONY: spell
spell: ; aspell --lang="$(LANG)" check "$(BOOKDIR)$(BOOK).texinfo"

.PHONY: grammar
grammar: ; link-parser < "$(BOOK).texinfo" 2>&1 | sed -e  \
	   s/'No complete linkages found'/'\x1b[1;31mNo complete linkage found\x1b[m'/g | less -r


install:
	mkdir -p "$(DESTDIR)$(PREFIX)$(BINDIR)"
	mkdir -p "$(DESTDIR)$(SYSCONFDIR)"
	mkdir -p "$(DESTDIR)$(PREFIX)$(DATADIR)/licenses/$(PROGRAM)"
	install -m 755 ponymenu.py "$(DESTDIR)$(PREFIX)$(BINDIR)/$(PROGRAM)"
	install -m 644 ponymenu.example "$(DESTDIR)$(SYSCONFDIR)/$(PROGRAM)"
	install -m 644 ponymenu.info.gz "$(DESTDIR)$(PREFIX)$(DATADIR)/info/$(PROGRAM).info.gz"
	install -m 644 COPYING "$(DESTDIR)$(PREFIX)$(DATADIR)/licenses/$(PROGRAM)/COPYING"
	install -m 644 LICENSE "$(DESTDIR)$(PREFIX)$(DATADIR)/licenses/$(PROGRAM)/LICENSE"

uninstall:
	unlink "$(PREFIX)$(BINDIR)/ponymenu"
	unlink "$(SYSCONFDIR)/ponymenu"
	unlink "$(PREFIX)$(DATADIR)/info/$(PROGRAM).info.gz"
	unlink "$(PREFIX)$(DATADIR)/licenses/$(PROGRAM)/COPYING"
	unlink "$(PREFIX)$(DATADIR)/licenses/$(PROGRAM)/LICENSE"


.PHONY: clean
clean: clean-tex clean.bak-
	@echo nothing to clean


.PHONY: clean-tex
clean-tex: clean.t2d- clean.aux- clean.cp- clean.cps- clean.fn- clean.ky- clean.log- clean.pg-  \
	   clean.pgs- clean.toc- clean.tp- clean.vr- clean.vrs- clean.op- clean.ops-

.PHONY: clean.%-
clean.%-:
	@echo -e 'Cleaning \e[34m.$*\e[m'
	@find ./ | grep '\.$*$$' | while read file; do  \
	    if [ -L "$$file" ]; then  file=$$(readlink "$$file");  fi;            \
	    if [ -f "$$file" ]; then  $(RM)    "$$file";  fi;                     \
	    if [ -d "$$file" ]; then  $(RM) -r "$$file";  fi;                     \
	done


.PHONY: view
view: $(BOOK).pdf
	if [ ! "$$PDF_VIEWER" = '' ]; then  \
	    "$$PDF_VIEWER" "$<";            \
	else                                \
	    xpdf "$<";                      \
	fi

.PHONY: atril
atril: $(BOOK).pdf ; atril "$<"

.PHONY: evince
evince: $(BOOK).pdf ; evince "$<"

.PHONY: xpdf
xpdf: $(BOOK).pdf ; xpdf "$<"

.PHONY: okular
okular: $(BOOK).pdf ; okular "$<"

.PHONY: gs
gs: $(BOOK).pdf ; gs "$<"

.PHONY: jfbview
jfbview: $(BOOK).pdf
	jfbview "$<"
	echo -en '\e[H\e[2J'

