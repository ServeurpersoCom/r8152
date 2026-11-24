# r8152 mainline backport for Debian stable

The mainline Linux `r8152` driver for Realtek USB Ethernet adapters, from
RTL8152 (1G) to RTL8159 (10G, `0bda:815a`), built out of tree with DKMS for
older kernels.

Debian stable (trixie, Linux 6.12) ships an `r8152` without RTL8159 support,
which arrived in Linux 7.2. Without it the adapter falls back to `cdc_ncm`,
far below 10G.

* `r8152.c`: `drivers/net/usb/r8152.c` from Linux v7.4-rc4, unmodified except
  for the `compat.h` include.
* `compat.h`: the kernel APIs the mainline driver uses that older kernels lack
  or spell differently.

## Install

```
dkms add .
dkms install r8152/7.4-rc4
```

## Firmware

The RTL8159 needs `rtl_nic/rtl8159-1.fw` in `/lib/firmware` for 10G; without
it the link stays at 5G. The file is not in linux-firmware: it is generated
from the `ram17` array of Realtek's out-of-tree driver.
