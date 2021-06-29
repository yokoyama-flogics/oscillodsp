APPSRC = qtoscillo.py
SRCS = confman.py colorman.py ${APPSRC}
LIBSRCS = dsp.py oscillo.py utils.py
PYTESTSRCS = $(wildcard tests/test_*.py)
FLAKE8SRCS = ${SRCS} $(addprefix oscillodsp/, $(LIBSRCS))
ALLSRCS = ${FLAKE8SRCS} $(PYTESTSRCS)
WHITELIST = whitelist.py

PROTOC = ../protoc-3.12.2/bin/protoc
PROTOBUF_PY = oscillodsp/oscillodsp_pb2.py

.PHONY: default run lint test

default: run

$(PROTOBUF_PY): $(wildcard ../protobuf/oscillodsp.*)
	$(PROTOC) --proto_path=../protobuf \
		--python_out=oscillodsp/ \
		oscillodsp.proto

run: $(PROTOBUF_PY)
	python ${APPSRC}

lint:
	yapf -d $(ALLSRCS)
	flake8 $(FLAKE8SRCS)
	flake8 --ignore=F403,F405 $(PYTESTSRCS)
	vulture $(SRCS) $(WHITELIST)
	(cd oscillodsp; vulture $(LIBSRCS) $(WHITELIST))
	vulture $(PYTESTSRCS)

test:
	python -m pytest -v
