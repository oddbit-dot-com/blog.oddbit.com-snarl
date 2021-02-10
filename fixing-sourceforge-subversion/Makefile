SRC = $(wildcard *.snarl.md)
MDDOC = $(SRC:.snarl.md=.md)
HTMLDOC = $(SRC:.snarl.md=.html)

POSTS = $(HOME)/projects/blog.oddbit.com-hugo/content/post/
ASSETS = $(HOME)/projects/blog.oddbit.com-hugo/content/assets/2020/01/31

FILES = $(shell snarl -i files $(SRC))

BUILDS = \
	force_open_fail.so \
	fail_only_target.so

IMAGES =

PANDOC = pandoc

LDFLAGS = -shared
CFLAGS  = -fPIC
LIBS    = -ldl

%.so: %.o
	$(LD) $(LDFLAGS) -o $@ $< $(LIBS)

%.md: %.snarl.md
	snarl weave -o $@ $<

%.html: %.md
	$(PANDOC) $(PANDOCFLAGS) -s -o $@ $<

all: $(MDDOC) $(FILES) $(HTMLDOC) $(BUILDS)

.NOTPARALLEL: $(FILES)
$(FILES): $(SRC)
	snarl -vi tangle -w $<

$(MDDOC): $(IMAGES)

install: $(MDDOC)
	install -d -m 755 $(POSTS)
	install $(MDDOC) $(POSTS)

clean:
	rm -f $(FILES) $(MDDOC) $(HTMLDOC) $(OUTPUTS) $(BUILDS)
