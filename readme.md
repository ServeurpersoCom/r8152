# r8152: mainline Realtek USB Ethernet driver for Debian stable

The Linux kernel's own `r8152` driver, packaged with DKMS for kernels that
predate it, so that Realtek USB adapters up to the 10GbE RTL8159 run at full
speed on Debian stable.

> **Firmware not included.** Like the kernel itself, this repository ships
> the driver only. The RTL8159 needs its PHY firmware for 10G, which you
> build yourself from Realtek's driver source: see
> [RTL8159 firmware](#rtl8159-firmware).

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
* `rtl8159-fw.py`: builds the RTL8159 firmware file from Realtek's source.

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
The driver loads it from `/lib/firmware/rtl_nic/rtl8159-1.fw`, a separate
file like any other device firmware, which the kernel does not ship.

That file is in neither linux-firmware nor this repository. Realtek publishes
the microcode only as the `ram17` array inside its GPL driver source, with no
firmware license that would allow redistributing the binary on its own. So
each user generates it locally from Realtek's source, with `rtl8159-fw.py`
(Python 3, standard library only).

1. Get Realtek's `r8152.c`, for example 2.22.1 as mirrored by bb-qq:

   ```
   wget https://raw.githubusercontent.com/bb-qq/r8152/generic/2.22.1/r8152.c -O realtek-r8152.c
   ```

2. Generate the firmware:

   ```
   ./rtl8159-fw.py realtek-r8152.c
   ```

   It prints the Realtek version, the PHY `code_ver` and the microcode size,
   e.g. `Realtek v2.22.1, PHY code_ver 0x0022, 17376 bytes of microcode`.
   From 2.22.1, `rtl8159-1.fw` has SHA-256
   `3113cdf4bce6b8c8bdf8a2b78d2aa85234ae1a0ab4739b965da2405fb9dc5f66`.

3. Install it:

   ```
   mkdir -p /lib/firmware/rtl_nic
   cp rtl8159-1.fw /lib/firmware/rtl_nic/
   ```

4. If `r8152` is in your initramfs (`lsinitramfs /boot/initrd.img-$(uname -r) | grep r8152`),
   rebuild it so the firmware goes in too:

   ```
   update-initramfs -u
   ```

The script follows the format of
[rtlnic_fw](https://gitlab.com/koblitz-rtlnic/rtlnic_fw) by Birger Koblitz,
author of the mainline RTL8159 support: a SHA-256 checked header, one
`PHY_SPEED_UP` block written at register `0x9a00`, and the `code_ver` that
Realtek's driver pairs with `ram17`. The driver compares that version with
the one the chip reports after loading, so it must come from the same
source as the microcode.

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
the compiler rejects, and bump both `PACKAGE_VERSION` in `dkms.conf` and
`MODULE_VERSION` in `compat.h`.
