#!/usr/bin/env python3
"""Build rtl_nic/rtl8159-1.fw from Realtek's out-of-tree r8152.c.

Realtek ships the RTL8159 PHY microcode only as the ram17[] array of its GPL
driver source. This script extracts it with its code_ver and writes the
firmware file the mainline r8152 driver loads: a SHA-256 checked header, one
RTL_FW_PHY_SPEED_UP block, and an RTL_FW_END block.

Usage: rtl8159-fw.py <realtek r8152.c> [output]
"""

import hashlib
import re
import struct
import sys

RTL_FW_END = 0
RTL_FW_PHY_SPEED_UP = 13
FW_OFFSET = 0x30
FW_REG = 0x9A00


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__.strip().splitlines()[-1])
    src = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    out = sys.argv[2] if len(sys.argv) == 3 else "rtl8159-1.fw"

    m = re.search(r"static u8 ram17\[\] = \{(.*?)\};\s*code_ver = (0x[0-9a-fA-F]+);", src, re.S)
    d = re.search(r'#define DRIVER_VERSION "(v[\d.]+)".*\((\d{4})/(\d{2})/(\d{2})\)', src)
    if not m or not d:
        sys.exit("ram17[] or DRIVER_VERSION not found: not a Realtek r8152.c with RTL8159 support")

    ram = bytes(int(b, 16) for b in re.findall(r"0x[0-9a-fA-F]+", m.group(1)))
    code_ver = int(m.group(2), 16)
    date = "".join(d.group(2, 3, 4))
    info = f"tgphy_ramcode_v{code_ver:x}_usb_{date}".encode()
    version = f"rtl8159-1 v{code_ver:x} {d.group(2)}/{d.group(3)}/{d.group(4)}".encode()

    block = struct.pack("<IIHHHH", RTL_FW_PHY_SPEED_UP, FW_OFFSET + len(ram), FW_OFFSET, code_ver, FW_REG, 0)
    block = block + info.ljust(FW_OFFSET - len(block), b"\0") + ram
    body = version.ljust(32, b"\0") + block
    body += b"\0" * (-(32 + len(body)) % 8)
    body += struct.pack("<II", RTL_FW_END, 8)

    with open(out, "wb") as f:
        f.write(hashlib.sha256(body).digest() + body)
    print(f"{out}: Realtek {d.group(1)}, PHY code_ver 0x{code_ver:04x}, {len(ram)} bytes of microcode")


if __name__ == "__main__":
    main()
