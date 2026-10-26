PYTHON := .venv/bin/python

.PHONY: all setup clean

all: anker-powerexpand-elite-holder

setup: $(PYTHON)

$(PYTHON): requirements.txt
	python3 -m venv .venv
	$(PYTHON) -m pip install -q -r requirements.txt
	touch $(PYTHON)

.PHONY: anker-powerexpand-elite-holder
anker-powerexpand-elite-holder: $(PYTHON)
	cd $@ && for s in stripe lattice; do \
		../$(PYTHON) holder.py --style $$s -o stl/holder-$$s.stl && \
		../$(PYTHON) ../tools/preview.py stl/holder-$$s.stl images/preview-$$s.png; \
	done
