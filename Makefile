VENV := $(CURDIR)/.venv
PYTHON := $(VENV)/bin/python
STAMP := $(VENV)/.installed

.PHONY: all setup anker-powerexpand-elite-holder ore ipad-pro-11-tray

all: anker-powerexpand-elite-holder ore ipad-pro-11-tray

setup: $(STAMP)

$(STAMP): requirements.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -q -r requirements.txt
	touch $(STAMP)

anker-powerexpand-elite-holder: $(STAMP)
	cd $@ && for s in stripe lattice; do \
		$(PYTHON) holder.py --style $$s -o stl/holder-$$s.stl && \
		$(PYTHON) ../tools/preview.py stl/holder-$$s.stl images/preview-$$s.png && \
		$(PYTHON) holder.py --style $$s --mount tape --floor --wall 3.2 --rib 4 -o stl/holder-$$s-tape.stl && \
		$(PYTHON) ../tools/preview.py stl/holder-$$s-tape.stl images/preview-$$s-tape.png; \
	done

ore: $(STAMP)
	cd $@ && $(PYTHON) ore.py -o stl/ore.stl && \
		$(PYTHON) ../tools/preview.py stl/ore.stl images/preview.png

ipad-pro-11-tray: $(STAMP)
	cd $@ && $(PYTHON) tray.py -o stl/tray.stl && \
		$(PYTHON) ../tools/preview.py stl/tray.stl images/preview-parts.png && \
		$(PYTHON) tray.py --assembled -o $(VENV)/assembled.stl && \
		$(PYTHON) ../tools/preview.py $(VENV)/assembled.stl images/preview.png
