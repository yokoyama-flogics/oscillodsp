APPSRC = qtoscillo.py
SRCS = confman.py colorman.py ${APPSRC}
LIBSRCS = dsp.py oscillo.py utils.py
PYTESTSRCS = $(wildcard tests/test_*.py)
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

format:
	isort .
	black .

lint:
	vulture $(SRCS) $(WHITELIST)
	(cd oscillodsp; vulture $(LIBSRCS) $(WHITELIST))
	vulture $(PYTESTSRCS)
	pylint .

test:
	python -m pytest -v
