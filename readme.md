# r8152: mainline Realtek USB Ethernet driver for Debian stable

The Linux kernel's own `r8152` driver, packaged with DKMS for kernels that
predate it, so that Realtek USB adapters up to the 10GbE RTL8159 run at full
speed on Debian stable.

| Chip    | Speed | USB ID      |
|---------|-------|-------------|
| RTL8152 | 100M  | `0bda:8152` |
| RTL8153 | 1G    | `0bda:8153` |
| RTL8156 | 2.5G  | `0bda:8156` |
| RTL8157 | 5G    | `0bda:8157` |
| RTL8159 | 10G   | `0bda:815a` |

## Why

Debian 13 (trixie) ships Linux 6.12, whose `r8152` has no RTL8159 support:
the adapter falls back to the generic `cdc_ncm` driver at around 100 MB/s.
Mainline support arrived in Linux 7.2.

Realtek's out-of-tree driver (`r8152` 2.x) reaches 10G, but its RTL8157/8159
path can lock up the chip under load: `NETDEV WATCHDOG` on the transmit
queue, register reads failing with `-110`, and a dead adapter that only a
power cut brings back. This repository runs the mainline driver instead.

## Contents

* `r8152.c`: `drivers/net/usb/r8152.c` from Linux v7.4-rc4, unmodified
  except for the `compat.h` include.
* `compat.h`: the kernel APIs the mainline driver uses that older kernels
  lack or spell differently, each guarded by the version that introduced it.
* `Kbuild`, `Makefile`, `dkms.conf`: out-of-tree build and DKMS packaging.

## Install

Remove Realtek's driver first if it is installed, since both build a module
named `r8152`:

```
dkms status r8152
dkms remove r8152/<version> --all
```

Then, from this directory:

```
dkms add .
dkms install r8152/7.4-rc4
```

DKMS rebuilds the module for every new kernel.

## RTL8159 firmware

The RTL8159 needs its PHY firmware for 10G; without it the link stops at 5G.
The driver loads it from `/lib/firmware/rtl_nic/rtl8159-1.fw`, but that file
is not in linux-firmware: the microcode only exists as the `ram17` array of
Realtek's GPL driver source.

[rtlnic_fw](https://gitlab.com/koblitz-rtlnic/rtlnic_fw) by Birger Koblitz,
author of the mainline RTL8159 support, builds the file from that array:

1. Copy `ram17[]` from Realtek's `r8152.c` into `rtl_fw.c`.
2. In `speedup_17`, set `.version` to that driver's `code_ver` for `ram17`
   (`0x0022` for 2.22.1). The driver compares it with the version the chip
   reports after loading, so it must match.
3. Build and write the file, then install it:

```
gcc rtl_fw.c -o rtl_fw -lssl -lcrypto
./rtl_fw -w 17
cp rtl8159-1.fw /lib/firmware/rtl_nic/
```

`./rtl_fw rtl8159-1.fw` dumps a firmware file and checks its SHA-256.

## Check

```
modinfo -n r8152
ethtool -i <iface>
ethtool <iface> | grep Speed
```

The module path must be under `updates/dkms`, and the speed `10000Mb/s` on
a 10G link.

## Updating

Copy `drivers/net/usb/r8152.c` from a newer kernel, keep the
`#include "compat.h"` line, build, add a `compat.h` entry for each new API
the compiler rejects, and bump `PACKAGE_VERSION` in `dkms.conf`.
