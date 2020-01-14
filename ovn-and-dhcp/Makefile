SRC = 2019-12-19-ovn-and-dhcp.snarl.md
MDDOC = $(SRC:.snarl.md=.md)
HTMLDOC = $(SRC:.snarl.md=.html)

POSTS = $(HOME)/projects/blog.oddbit.com-hugo/content/post/

FILES = $(shell snarl files $(SRC))

%.md: %.snarl.md
	snarl weave -o $@ $<

%.html: %.md
	pandoc -o $@ $<

all: $(MDDOC) $(FILES) $(HTMLDOC)

.NOTPARALLEL: $(FILES)
$(FILES): 2019-12-19-ovn-and-dhcp.snarl.md
	snarl -v tangle -w $<

install: $(MDDOC)
	install $(MDDOC) $(POSTS)

clean:
	rm -f $(FILES) $(MDDOC) $(HTMLDOC)
