---
title: "Cloud WiFi Camera"
layout: "project"
icon: "camera"
description: "Turning a V380E-class cloud camera into a working local-only 720p RTSP/ONVIF camera with OpenIPC on its own flash."
status: "Working"
stage: "Local-only RTSP/ONVIF"
hardware: "Anyka AK3918EN080 (V200)"
hardware_detail: "64 MiB RAM · 8 MiB MX25L6433F NOR · SC1245 sensor"
firmware: "OpenIPC AK3918EV200 · Linux 4.4.302"
network: "Wi-Fi · LAN only, no default route"
streaming: "H.264 1280×720 · RTSP/ONVIF"
storage: "NOR rootfs + jffs2 overlay"
recovery: "Saved U-Boot SD p4/p3 boots; stock rescue on p1/p2"
date: 2026-11-22
weight: 10
---

The camera is a cheap, cloud-first Wi-Fi model from the V380 family. It has no
Ethernet socket, and its normal life is a vendor app, a vendor account and a
cloud service. This project keeps the hardware and replaces that life with
something local: an authenticated RTSP stream on the LAN, ONVIF for an NVR, and
no dependency on the vendor cloud.

The camera now works end to end. OpenIPC boots unattended from the camera's own
NOR flash, joins the LAN over Wi-Fi, and serves 720p H.264. The work was done on
20–22 November 2026.

## What works

Verified on 22 November 2026:

- **Boot:** OpenIPC 4.4.302 boots from NOR in about 17 seconds, with a
  persistent jffs2 overlay. Settings survive a reboot.
- **Network:** the RTL8188FU Wi-Fi adapter associates and gets a DHCP lease.
  The configuration is LAN-only, with no IPv4 default route and IPv6 disabled.
- **Video:** the SC1245 sensor is detected and the encoder produces H.264 at
  1280×720, 25 fps, about 1600 kbit/s.
- **Streaming:** authenticated RTSP on TCP 554, with ONVIF on port 80. RTP over
  TCP and UDP both work.
- **Clients:** ffprobe and Blue Iris both pull the main stream. ONVIF
  `GetStreamUri` returns the working RTSP path.
- **Management:** the OpenIPC web UI and SSH are available on the LAN.
- **Recovery:** the stock SD rescue on p1/p2 was left in place, and saved U-Boot
  entries boot the OpenIPC SD roots on p3/p4.

## The hardware

The main processor is an **Anyka AK3918EN080** (V200, CDSJ02A20), confirmed from
the physical marking. The stock boot log reports 64 MiB of DRAM and an 8 MiB NOR
flash; the flash was read off-board as an **MX25L6433F**. The sensor reports ID
`0x1245`, which points at an **SC1245**, and the stock root filesystem contains
an `8188fu.ko` driver for a **Realtek RTL8188FU** USB Wi-Fi adapter.

The sensor and Wi-Fi entries came from the stock software and boot log before
the replacement. Both are now driven by the OpenIPC kernel and confirmed
in the live system. The board also has UART pads marked TX1/RX1; the console runs
at 115200 8N1.

{{< gallery >}}
{{< photo src="img/projects/cloud-wifi-camera/board-front.jpg" alt="The camera board with the lens, IR-cut filter assembly and Wi-Fi module fitted." caption="Lens, IR-cut filter assembly and the RTL8188FU Wi-Fi module." >}}
{{< photo src="img/projects/cloud-wifi-camera/board-front-top.jpg" alt="Top view of the board showing the IR-cut filter assembly and its wiring." caption="The IR-cut filter assembly and its wiring." >}}
{{< photo src="img/projects/cloud-wifi-camera/board-back.jpg" alt="Back of the camera board showing the microSD slot, micro-USB port, reset button and board marking." caption="MicroSD slot, micro-USB power, reset button and board marking." >}}
{{< photo src="img/projects/cloud-wifi-camera/board-in-hand.jpg" alt="The camera board held in one hand, showing its size." caption="The board held for scale." >}}
{{< /gallery >}}

## What the stock firmware does

Stock is Linux 3.4.35 on an Anyka board with a SquashFS root, a JFFS2
configuration partition and a vendor U-Boot that reads its own partition table.
The flash was read twice and the two 8 MiB images matched. The filesystems and
the JFFS2 configuration were reconstructed offline, and a full backup plus a
stock-kernel/SD recovery route were kept before anything was changed.

Static analysis of `mvrtsp`, `recorder` and `libmvs_core.so` found:

- The RTSP server is gated by `rtsp=0` in the recovered `factory_const.ini`. With
  that value it exits before opening RTSP or ONVIF; the ONVIF fork is inside the
  same gate. When enabled, this build listens on TCP 554, with ONVIF on TCP 8899
  and UDP 3702.
- The RTSP handlers in this build have no authentication path. ONVIF is likely
  unauthenticated too, but that was not proven.
- RTSP depends on the recorder and event hub. The server cannot simply be
  stubbed out without also removing the media queues the stream needs.
- `-nonet` is not a local-only switch. It skips Wi-Fi/network initialisation,
  not the cloud, OTA or server start-up.
- The recovered `nvipcstart.sh` contains an `LD_PRELOAD` OTA redirect and an FTP
  download-and-execute command, and boot also starts a DDNS helper. Those
  commands were never executed and no vendor endpoint was contacted. Their
  presence is why patching the stock system looked less attractive than a clean
  replacement: removing one path would not establish a no-cloud system.

These are static findings from the stock firmware, not a validated no-cloud
image.

## A clean replacement

The replacement is an OpenIPC build for the AK3918EV200, which OpenIPC
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

The first attempt kept the vendor bootloader, both partition tables, MAC and ENV
records untouched. A replacement kernel was built with device-tree changes only,
and full-node copies of the two kernel slots were written with a static
`flashcp` from a stock-kernel SD rescue shell. Every write was read back and
hashed, and a rollback path was prepared first.

The first three kernel builds all stopped at `Waiting for root device
/dev/mmcblk0p2`. The kernel reached the MMC controller, but the card never
answered. The cause was not the MMC driver: the new boot path skipped the board
pinmux that the stock bootloader applies. Restoring the stock SYSCTRL
values made the card enumerate and mount the root filesystem:

```sh
mw.l 0x08000074 0x0A000186 1
mw.l 0x08000078 0 1
mw.l 0x0800007c 0x06BAF5A5 1
mw.l 0x080000dc 0x00303F03 1
mw.l 0x08000080 0x1C0 1
mw.l 0x080000e0 0 1
```

These values document the fix; they are not a procedure to copy onto another
board. They were then saved in U-Boot's environment, with the
original ENV block backed up first, so the camera cold-boots the 4.4.302 kernel
without manual commands. The stock SD rescue remained on p1/p2, byte-identical
to its backups, and an OpenIPC root was staged on p3 and later p4.

## From SD root to flash

The first OpenIPC root ran from SD p4 with a tmpfs overlay. Wi-Fi, the sensor,
720p encoding and RTSP all worked there, but settings vanished on reboot and SD
boot took four to five minutes. The root now lives on NOR:

- a squashfs root in `mtd2`
- a small jffs2 `rootfs_data` partition in `mtd3` for persistent settings
- the kernel in `mtd1`
- the vendor bootloader, partition tables, stock kernel, MAC and ENV records
  left in `mtd0`

The rootfs was written with `flashcp`, read back and hashed, and the stale vendor
bytes in `rootfs_data` were erased and initialised as jffs2. The first flash-root
boot mounted the squashfs correctly but then appeared to hang at `Starting
mdev...`. That line was stale console scrollback from the previous boot. The real
stall was `S31hostname` calling `fw_printenv`, which spun forever in userspace
because `/etc/fw_env.config` was missing. Adding the config fixed it;
`fw_printenv` now returns defaults with a bad-CRC warning. Boot time
dropped to about 17 seconds.

## Flash layout

```text
mtd0  0x000000  0x1b9000  preserved    U-Boot, tables, stock KERNEL, MAC, ENV
mtd1  0x1b9000  0x1ad000  kernel       OpenIPC uImage (video variant)
mtd2  0x366000  0x459000  rootfs       OpenIPC squashfs
mtd3  0x7bf000  0x041000  rootfs_data  jffs2 overlay (~260 KB)
```

The kernel command line is:

```text
mtdparts=spi0.0:0x1b9000(preserved),0x1ad000(kernel),0x459000(rootfs),0x41000(rootfs_data)
```

The rootfs image is exactly `0x459000` bytes, so the partition has no slack. The
memory split is 40 MiB for Linux and 24 MiB reserved for video
(`mem=40M memsize=64M rmem=24M`). The saved U-Boot environment boots this layout
by default; `boot_p4` and `boot_p3` remain as SD recovery entries.

## Streaming and validation

The live stream is H.264 at 1280×720, 25 fps and about 1600 kbit/s. It is served
on RTSP port 554 and requires authentication; RTSP uses the same account as the
web UI and SSH. The main path is `/main`, with `/stream=0`, `/video0` and `/ch0`
as aliases. RTP over TCP works better over Wi-Fi; UDP also works.

ONVIF is on port 80 at `/onvif/device_service`, using HTTP Basic authentication.
WSSE PasswordDigest also works once `onvif.password` is set, because majestic
needs a cleartext copy of the password for digest (it is stored in the camera
configuration with mode 0600). `GetStreamUri` returns the working `/stream=0`
path.

Blue Iris was used to validate the stream. Two client-side problems came up: an
unset ONVIF password, and Blue Iris never sending an RTSP `Authorization` header
at all. Upgrading Blue Iris fixed the second; a camera-side capture showed the
missing header. VLC on Arch needs the separate `vlc-plugin-live555` package;
`ffplay` and `mpv` work without it.

## Local-only behaviour

The camera's own network configuration is LAN-only. The Wi-Fi setup brings up
the link and DHCP but installs no IPv4 default route, and IPv6 is disabled. The
running system is OpenIPC: the vendor cloud client, OTA redirect and DDNS helper
from the stock firmware are not present in the boot path.

This is a practical result, not a formal traffic audit. The no-default-route and
IPv6-off configuration was verified on the SD-root system before the move to
NOR, but a full capture across boot, idle, streaming and reconnect was not
repeated afterwards. In practice the camera has no route and no vendor cloud
software, though not every packet has been accounted for.

## Limitations

- **Night mode is not working.** The IR-cut mapping is known (opening/night coil
  GPIO 42, closing/day coil GPIO 41, IR illuminator GPIO 6), and the SoC pads
  toggle correctly, but neither coil direction moved the filter or changed the
  image, and the IR lamp did not light. The likely causes are the lens module's
  IR-cut/IR connector, an unpopulated or damaged H-bridge, or a lens without a
  switched filter.
- **There is no real substream.** `video1` is disabled, so `/sub` is another
  alias of the 720p main stream. A 640×360, 10 fps, ~400 kbit/s second encoder
  would improve NVR use.
- **ONVIF discovery is not reliable with Blue Iris.** The device service and
  stream URI work when the camera is added manually; Blue Iris's WS-Security
  discovery did not. The ONVIF profile also advertises 6 fps while the real
  stream is 25 fps, so manual RTSP is more accurate.
- **Audio and JPEG snapshots are disabled.** The camera sends no audio.
- **The identity EEPROM is missing.** The desoldered chip was an FT24C02A, a
  256-byte I2C identity EEPROM, not firmware. OpenIPC does not use it and the
  camera runs without it. Reinstalling it only matters if the board may return
  to stock or be sold.
- **Recovery is not consumer-grade.** `boot_normal` no longer reaches a working
  stock root because the OpenIPC kernel occupies the old A/B slots. Recovery
  means interrupting U-Boot and booting the saved SD p4 or p3 entry, or the
  stock p1/p2 rescue. Recovery also requires a whole-NOR dump, and `fw_setenv`
  should not be run from userspace.
- **This is not a release image.** There is no reproducible build manifest, no
  whole-chip install, no formal review of OpenIPC's optional integrations, and
  no formal overnight, multi-client, AP-restart or thermal test.
