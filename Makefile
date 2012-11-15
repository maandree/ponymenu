PREFIX=/usr

all:
	@: do nothing

install:
	mkdir -p "$(DESTDIR)$(PREFIX)/bin"
	mkdir -p "$(DESTDIR)/etc"
	install -m 755 ponymenu.py "$(DESTDIR)$(PREFIX)/bin/ponymenu"
	install -m 644 ponymenu.example "$(DESTDIR)/etc/ponymenu"

clean:
	@echo nothing to clean

.PHONY: clean
