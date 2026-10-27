VENV := $(CURDIR)/.venv
PYTHON := $(VENV)/bin/python
STAMP := $(VENV)/.installed

.PHONY: all setup anker-powerexpand-elite-holder ore ipad-pro-11-tray desk-audio-hanger

all: anker-powerexpand-elite-holder ore ipad-pro-11-tray desk-audio-hanger

setup: $(STAMP)

$(STAMP): requirements.txt
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install -q -r requirements.txt
	touch $(STAMP)

anker-powerexpand-elite-holder: $(STAMP)
	cd $@ && for s in stripe lattice; do \
		$(PYTHON) holder.py --style $$s -o stl/holder-$$s.stl && \
		$(PYTHON) ../tools/preview.py stl/holder-$$s.stl images/preview-$$s.png && \
		$(PYTHON) holder.py --style $$s --mount tape --floor --fence --wall 3.2 --rib 4 -o stl/holder-$$s-tape.stl && \
		$(PYTHON) ../tools/preview.py stl/holder-$$s-tape.stl images/preview-$$s-tape.png; \
	done

ore: $(STAMP)
	cd $@ && $(PYTHON) ore.py -o stl/ore.stl && \
		$(PYTHON) ../tools/preview.py stl/ore.stl images/preview.png

ipad-pro-11-tray: $(STAMP)
	mkdir -p $@/stl && cd $@ && for p in rails plate; do \
		$(PYTHON) tray.py --part $$p -o stl/$$p.stl && \
		$(PYTHON) ../tools/preview.py stl/$$p.stl images/preview-$$p.png; \
	done && \
	$(PYTHON) tray.py --part assembled -o $(VENV)/assembled.stl && \
	$(PYTHON) ../tools/preview.py $(VENV)/assembled.stl images/preview.png

desk-audio-hanger: $(STAMP)
	mkdir -p $@/stl $@/images && cd $@ && for p in hanger cradle hook; do \
		$(PYTHON) hanger.py --part $$p -o stl/$$p.stl && \
		$(PYTHON) ../tools/preview.py stl/$$p.stl images/preview-$$p.png; \
	done
