.PHONY: all test build

all: .venv/.make_success

ifeq ($(OS), Windows_NT)
activate=.venv/Scripts/activate
else
activate=.venv/bin/activate
endif

.venv/.make_success: requirements.txt dev-requirements.txt .venv
	. $(activate) &&\
		python -m pip install -U pip &&\
		python -m pip install -r requirements.txt -r dev-requirements.txt
	echo > .venv/.make_success

.venv:
	virtualenv .venv

test: .venv/.make_success
	. $(activate) && coverage erase && tox

build: .venv/.make_success
	rm -rf build
	. $(activate) && python setup.py sdist bdist_wheel
