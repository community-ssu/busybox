
OBJS = disksize.o i386_sys_types.o partname.o sfdisk.o 

#OBJS = sfdisk.o

CFLAGS ?= -fomit-frame-pointer -Os

all: sfdisk


sfdisk: $(OBJS)
	$(CC) -o $@ $(OBJS)

clean:
	rm -f *.o *~ sfdisk
