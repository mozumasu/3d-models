VENV := $(CURDIR)/.venv
PYTHON := $(VENV)/bin/python
STAMP := $(VENV)/.installed

.PHONY: all setup anker-powerexpand-elite-holder ore

all: anker-powerexpand-elite-holder ore

setup: $(STAMP)

$(STAMP): requirements.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -q -r requirements.txt
	touch $(STAMP)

anker-powerexpand-elite-holder: $(STAMP)
	cd $@ && for s in stripe lattice; do \
		$(PYTHON) holder.py --style $$s -o stl/holder-$$s.stl && \
		$(PYTHON) ../tools/preview.py stl/holder-$$s.stl images/preview-$$s.png; \
	done

ore: $(STAMP)
	cd $@ && $(PYTHON) ore.py -o stl/ore.stl && \
		$(PYTHON) ../tools/preview.py stl/ore.stl images/preview.png
