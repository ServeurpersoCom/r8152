KDIR ?= /lib/modules/$(shell uname -r)/build

modules clean:
	$(MAKE) -C $(KDIR) M=$(CURDIR) $@

.PHONY: modules clean
