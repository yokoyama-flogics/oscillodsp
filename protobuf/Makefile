protoc =  ../../nanopb/generator/protoc
base = oscillodsp

.PHONY: all

all: $(base).pb.c $(base)_pb2.py

$(base).pb.c $(base).pb.h: $(base).proto $(base).options
	$(protoc) --nanopb_out=../workspace/oscillodemo/ $(base).proto
	$(protoc) --nanopb_out=../pcsim/ $(base).proto

$(base)_pb2.py: $(base).proto $(base).options
	$(protoc) --python_out=../hostapp/oscillodsp/ $(base).proto

