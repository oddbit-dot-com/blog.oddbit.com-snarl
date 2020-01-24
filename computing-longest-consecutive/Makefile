SRC = $(wildcard *.snarl.md)
MDDOC = $(SRC:.snarl.md=.md)
HTMLDOC = $(SRC:.snarl.md=.html)

POSTS = $(HOME)/projects/blog.oddbit.com-hugo/content/post/
ASSETS = $(HOME)/projects/blog.oddbit.com-hugo/content/assets/2020/01/23

FILES = $(shell snarl -i files $(SRC))
OUTPUTS = \
	initial.txt \
	step1.txt \
	step2.txt \
	step3.txt \
	step4.txt \
	step5.txt

IMAGES = \
	sample-results.png

PANDOC = pandoc

%.md: %.snarl.md
	snarl weave -o $@ $<

%.html: %.md
	$(PANDOC) $(PANDOCFLAGS) -s -o $@ $<

all: $(MDDOC) $(FILES) $(HTMLDOC)

.NOTPARALLEL: $(FILES)
$(FILES): $(SRC)
	snarl -vi tangle -w $<

$(MDDOC): $(OUTPUTS) $(IMAGES)

$(IMAGES): weather.py
	python weather.py

$(OUTPUTS): sample.py
	python sample.py

install: $(MDDOC)
	install -d -m 755 $(POSTS)
	install -d -m 755 $(ASSETS)
	install $(MDDOC) $(POSTS)
	install $(IMAGES) $(ASSETS)

clean:
	rm -f $(FILES) $(MDDOC) $(HTMLDOC) $(OUTPUTS)
