CC := gcc
CFLAGS := -I. -Wall -g

TARGET := pcsim
SRCS := main.c \
	oscillo.c \
	com.c \
	comdrv.c \
	pb_common.c \
	pb_encode.c \
	pb_decode.c \
	oscillodsp.pb.c \

OBJS := $(addsuffix .o, $(basename $(SRCS)))

$(TARGET): $(OBJS)
	$(CC) -o $@ $(OBJS) -lm

.PHONY: all
all: $(TARGET)

.PHONY: clean
clean:
	@rm -f $(TARGET) $(OBJS)
