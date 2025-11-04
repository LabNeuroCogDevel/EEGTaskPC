.SUFFIXES:
.SECONDARY:
.PHONY: all

# all desktop files to desktop
all: $(patsubst %,$(HOME)/Desktop/%,$(wildcard *.desktop))

$(HOME)/Desktop/%.desktop: %.desktop
	ln -sf $(PWD)/$< $@

# disable lp so parallel port works; ftdi_sio so cedrus button box works
/etc/modprobe.d/blacklist-lp_ftdi.conf: blacklist-lp_ftdi.conf
	cp $< $@

