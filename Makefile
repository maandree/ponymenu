PREFIX=/usr
BINDIR=/bin
SYSCONFDIR=/etc

all:

install:
	mkdir -p "$(DESTDIR)$(PREFIX)$(BINDIR)"
	mkdir -p "$(DESTDIR)$(SYSCONFDIR)"
	install -m 755 ponymenu.py "$(DESTDIR)$(PREFIX)$(BINDIR)/ponymenu"
	install -m 644 ponymenu.example "$(DESTDIR)$(SYSCONFDIR)/ponymenu"

uninstall:
	unlink "$(PREFIX)$(BINDIR)/ponymenu"
	unlink "$(SYSCONFDIR)/ponymenu"

clean:
	@echo nothing to clean

.PHONY: clean

