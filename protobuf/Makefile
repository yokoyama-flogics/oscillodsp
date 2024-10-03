# Define the protocol compiler and file names
protoc = nanopb_generator
base = oscillodsp
nanopb_out_workspace = ../workspace/oscillodemo
nanopb_out_pcsim = ../pcsim
python_out_dir = ../hostapp/oscillodsp

# Input files
proto_deps = $(base).proto $(base).options

.PHONY: all clean

# Main target
all: $(nanopb_out_workspace)/$(base).pb.c $(nanopb_out_workspace)/$(base).pb.h \
	$(nanopb_out_pcsim)/$(base).pb.c $(nanopb_out_pcsim)/$(base).pb.h \
	$(python_out_dir)/$(base)_pb2.py

# Rule for generating Nanopb files in the workspace directory
$(nanopb_out_workspace)/$(base).pb.c $(nanopb_out_workspace)/$(base).pb.h: $(proto_deps)
	$(protoc) --protoc-opt="--nanopb_out=$(nanopb_out_workspace)" $(base).proto

# Rule for generating Nanopb files in the pcsim directory
$(nanopb_out_pcsim)/$(base).pb.c $(nanopb_out_pcsim)/$(base).pb.h: $(proto_deps)
	$(protoc) --protoc-opt="--nanopb_out=$(nanopb_out_pcsim)" $(base).proto

# Rule for generating Python files
$(python_out_dir)/$(base)_pb2.py: $(proto_deps)
	$(protoc) --protoc-opt="--python_out=$(python_out_dir)" $(base).proto

# Clean target to remove generated files
clean:
	rm -f $(nanopb_out_workspace)/$(base).pb.c $(nanopb_out_workspace)/$(base).pb.h
	rm -f $(nanopb_out_pcsim)/$(base).pb.c $(nanopb_out_pcsim)/$(base).pb.h
	rm -f $(python_out_dir)/$(base)_pb2.py
