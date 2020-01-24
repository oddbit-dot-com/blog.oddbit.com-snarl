SRC = $(wildcard *.snarl.md)
MDDOC = $(SRC:.snarl.md=.md)
HTMLDOC = $(SRC:.snarl.md=.html)

POSTS = $(HOME)/projects/blog.oddbit.com-hugo/content/post/

FILES = $(shell snarl -i files $(SRC))
OUTPUTS = initial.txt step1.txt step2.txt step3.txt step4.txt step5.txt

PANDOC = pandoc

%.md: %.snarl.md
	snarl weave -o $@ $<

%.html: %.md
	$(PANDOC) $(PANDOCFLAGS) -s -o $@ $<

all: $(MDDOC) $(FILES) $(HTMLDOC)

.NOTPARALLEL: $(FILES)
$(FILES): $(SRC)
	snarl -vi tangle -w $<

$(MDDOC): $(OUTPUTS)

$(OUTPUTS): sample.py
	python sample.py

install: $(MDDOC)
	install $(MDDOC) $(POSTS)

clean:
	rm -f $(FILES) $(MDDOC) $(HTMLDOC) $(OUTPUTS)
