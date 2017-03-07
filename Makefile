SCRIPTS= geodns

prefix ?= /opt/ogslb
bindir ?= $(prefix)/bin
etcdir ?= $(prefix)/etc
libdir ?= $(prefix)/lib
protodir ?= $(prefix)/proto

all:

clean:

install:
	install -d -o root -g root $(DESTDIR)$(bindir)
	install -d -o root -g root $(DESTDIR)$(etcdir)
	install -d -o root -g root $(DESTDIR)$(libdir)
	install -d -o root -g root $(DESTDIR)$(protodir)
	install -o root -g root -m 755 -t $(DESTDIR)$(bindir) bin/*
	install -o root -g root -m 644 -t $(DESTDIR)$(etcdir) etc/*
	install -o root -g root -m 644 -t $(DESTDIR)$(libdir) lib/*
	install -o root -g root -m 644 -t $(DESTDIR)$(protodir) proto/*

