---
title: "Cloud WiFi Camera"
layout: "project"
icon: "camera"
description: "Reverse engineering a V380E-class cloud camera and bringing up an OpenIPC kernel on it."
status: "In progress"
stage: "OpenIPC kernel boots; userspace next"
hardware: "Anyka AK3918EN080 (V200)"
hardware_detail: "64 MiB RAM · 8 MiB MX25L6433F NOR · SC1245 sensor"
firmware: "OpenIPC AK3918EV200 · Linux 4.4.302"
recovery: "Stock SD rescue retained on p1/p2"
date: 2026-11-21
weight: 10
---

The camera is a cheap, cloud-first Wi-Fi model from the V380 family. It has no
Ethernet socket, and its normal life is a vendor app, a vendor account and a
cloud service. The aim of this project is to keep the hardware but replace that
life with something local: an RTSP stream on the LAN, optionally ONVIF, and no
dependency on the vendor cloud.

The work recorded here was done on 20–21 November 2026. It is a bring-up log,
not a finished conversion.

## The hardware

The main processor is an **Anyka AK3918EN080** (V200, CDSJ02A20), confirmed from
the physical marking. The stock boot log reports 64 MiB of DRAM and an 8 MiB NOR
flash; the flash was read off-board as an **MX25L6433F**. The sensor reports ID
`0x1245`, which points at an **SC1245**, and the stock root filesystem contains
an `8188fu.ko` driver for a **Realtek RTL8188FU** USB Wi-Fi adapter.

The sensor and Wi-Fi entries are evidence from the stock software and boot log,
not proof that the replacement kernel has driven either device yet. The board
also has UART pads marked TX1/RX1; the console runs at 115200 8N1.

## What the stock firmware does

Stock is Linux 3.4.35 on an Anyka board with a SquashFS root, a JFFS2
configuration partition and a vendor U-Boot that reads its own partition table.
The flash was read twice and the two 8 MiB images matched. The filesystems and
the JFFS2 configuration were reconstructed offline, and a full backup plus a
stock-kernel/SD recovery route were kept before anything was changed.

Static analysis of `mvrtsp`, `recorder` and `libmvs_core.so` found:

- The RTSP server is gated by `rtsp=0` in the recovered `factory_const.ini`. With
  that value it exits before opening RTSP or ONVIF; the ONVIF fork is inside the
  same gate. When enabled, the reviewed build listens on TCP 554, with ONVIF on
  TCP 8899 and UDP 3702.
- The RTSP handlers in this build have no authentication path. The review
  considered ONVIF likely to be unauthenticated too, but did not prove it.
- RTSP depends on the recorder and event hub. The server cannot simply be
  stubbed out without also removing the media queues the stream needs.
- `-nonet` is not a local-only switch. It skips Wi-Fi/network initialisation,
  not the cloud, OTA or server start-up.
- The recovered `nvipcstart.sh` contains an `LD_PRELOAD` OTA redirect and an FTP
  download-and-execute command, and boot also starts a DDNS helper. Those
  commands were never executed and no vendor endpoint was contacted. Their
  presence is why patching the stock system looked less attractive than a clean
  replacement: removing one path would not establish a no-cloud system.

No dynamic traffic capture was done. These are static findings and file
observations, not a validated no-cloud image.

## A clean replacement

The chosen route is an OpenIPC replacement for the AK3918EV200, which OpenIPC
[lists as a supported target](https://openipc.org/cameras/vendors/anyka/socs/ak3918ev200).
The official `openipc.ak3918ev200-nor-lite.tgz` rolling asset was downloaded,
its SHA-256 checked, and its kernel and root filesystem inspected. That checks
the download, not compatibility with this board.

An in-place swap was blocked. The 1,756,563-byte OpenIPC kernel does not fit the
1,572,864-byte stock KERNEL slot, the 4,554,752-byte root filesystem does not fit
slot A, and the load address differs. The stock `readcfg` also overwrites kernel
parameters from the vendor table, so the layout and boot flow had to be adapted
rather than forced. The replacement uses Linux 4.4.302 with built-in
sensor/encoder drivers; the stock 3.4.35 modules cannot be carried across.

## Bringing up a new kernel

The first stage kept the vendor bootloader, both partition tables, MAC and ENV
records untouched. A replacement kernel was built with device-tree changes only,
and full-node copies of the two kernel slots were written with a static
`flashcp` from a stock-kernel SD rescue shell. Every write was read back and
hashed, and a rollback path was prepared first.

The first three candidate boots all stopped at `Waiting for root device
/dev/mmcblk0p2`. The kernel reached the MMC controller, but the card never
answered. The cause was not the MMC driver: the candidate boot path skipped the
board pinmux that the stock bootloader applies. Restoring the stock SYSCTRL
values made the card enumerate and mount the root filesystem:

```sh
mw.l 0x08000074 0x0A000186 1
mw.l 0x08000078 0 1
mw.l 0x0800007c 0x06BAF5A5 1
mw.l 0x080000dc 0x00303F03 1
mw.l 0x08000080 0x1C0 1
mw.l 0x080000e0 0 1
```

These values are recorded as evidence of the fix, not as a procedure to copy
onto another board. They were then saved in U-Boot's environment, with the
original ENV block backed up first, so the camera cold-boots the 4.4.302 kernel
without manual commands. The stock SD rescue is still on p1/p2, byte-identical
to its backups, and a customised OpenIPC root filesystem has been staged on a
new p3. Later kernel variants add USB/Wi-Fi and camera nodes; the notes describe
the USB-enabled variant as the one currently flashed, but the captured boot
evidence stops at the earlier SD-root milestone.

## Where this stopped

The verified milestone is a boot, not a working camera. The camera cold-boots
the OpenIPC 4.4.302 kernel from flash, enumerates the SD card and mounts the
stock rescue root from SD p2. The stock p1/p2 rescue partitions are intact, and
the OpenIPC root filesystem is ready on p3.

The OpenIPC userspace has not yet booted as the system. Wi-Fi association,
sensor capture, video encoding, RTSP/ONVIF and a no-cloud traffic test are all
still unverified on the replacement stack. There is no final flash layout,
release image or whole-chip install, and `boot_normal` no longer reaches a
working stock root because the trial kernel occupies the old A/B slots. Recovery
is still a deliberate U-Boot and SD operation, not a consumer upgrade.

> **Stopping point.** The last confirmed result is the SD-root kernel boot. The
> work stops before the OpenIPC root filesystem is booted and before any
> end-to-end camera function is validated.

## Next steps

The next step is to boot p3 as the OpenIPC root, then bring up local-only Wi-Fi
and the SC1245/video path, followed by RTSP and optional ONVIF. The acceptance
tests are already written down: an isolated LAN with no WAN, no unexpected
outbound traffic, working RTSP over TCP and UDP, and a checked rollback. Only
after those pass is it worth designing a persistent partition layout and a
release image.
