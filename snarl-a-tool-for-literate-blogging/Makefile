SRC = 2020-01-15-snarl-a-tool-for-literate-blog.snarl.md
MDDOC = $(SRC:.snarl.md=.md)
HTMLDOC = $(SRC:.snarl.md=.html)

POSTS = $(HOME)/projects/blog.oddbit.com-hugo/content/post/

%.md: %.snarl.md
	snarl weave -o $@ $<

%.html: %.md
	pandoc $(PANDOCFLAGS) -s -o $@ $<

all: $(MDDOC) $(HTMLDOC)

$(MDDOC): $(SRC) hello.c hello.md
	snarl weave -o $@ $<

install: all
	install -m 644 $(MDDOC) $(POSTS)

hello.c: hello.snarl.md
	snarl tangle -w hello.snarl.md

clean:
	rm -f $(MDDOC) $(HTMLDOC) hello.c hello.md
