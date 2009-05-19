
all: lcdinit.py lcdinit.c

lcdinit.py: initroutines.py master.py classes.py
	python master.py python > $@

lcdinit.c: initroutines.py master.py classes.py
	python master.py c > $@

initroutines.py : initroutines.txt process.py
	python process.py $< $@

