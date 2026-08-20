---
name: linux-lfs-build-troubleshooting
description: Debug Linux From Scratch (LFS) builds, overlay filesystem issues, and GRUB bootloader installation. Covers locating actual build artifacts, analyzing overlayfs upper/lower layers, verifying target disk contents, and fixing misplaced builds before bootloader installation.
category: devops
version: 1.1.0
tags:
  - lfs
  - linux-from-scratch
  - overlayfs
  - grub
  - bootloader
  - disk-partitioning
  - persistent-live-usb
metadata:
  hermes:
    trigger_conditions:
      - "LFS build on wrong device"
      - "overlay filesystem confusing"
      - "files appear then disappear on live USB"
      - "GRUB won't boot after LFS"
      - "kernel panic can't mount root"
      - "build artifacts not on target disk"
      - "casper-rw persistence partition"
      - "where did my LFS build go"
      - "grub-install planning or verification"
      - "boot failure after Linux From Scratch"
      - "upperdir vs combined view"
      - "copy LFS build to internal drive"
      - "EFI System Partition boot issue"
---

# Linux From Scratch Build Troubleshooting

## When to Use

- User is building LFS and needs to locate where build files actually live
- LFS build appears to be on wrong device (USB persistence vs target disk)
- Overlay filesystem confusion (combined view vs upperdir only)
- GRUB installation planning/verification
- Boot failure diagnosis after LFS build
- Kernel panic with "can't mount root" after booting the new build
- Persistence partition (`casper-rw`) inspection or repair

## Not For

- **Building LFS from scratch / chapter-by-chapter walkthrough** → use the official LFS book, not this skill
- **Non-overlay filesystem build environments** (plain chroot on a real partition) → standard `chroot` + `grub-install` flow applies; the overlayfs/upperdir diagnosis is irrelevant
- **GRUB on a running production system** → use the distro's native bootloader management instead
- **General disk space recovery** → use the `disk-space-recovery` skill
- **Docker/container overlayfs troubleshooting** → that's container storage driver debugging, not live-USB persistence

## Core Concepts

### Overlay Filesystem in Persistent Live USB
When booting Ubuntu live USB with `persistent` kernel parameter:
- Root filesystem is an **overlayfs** combining:
  - **Lowerdirs** (read-only): squashfs images from live USB (`/minimal.standard*.squashfs`)
  - **Upperdir** (read-write): persistent partition on USB (`/dev/sdb2` labeled `casper-rw`)
- The mount point `/mnt/lfs` shows the **combined view** (lower + upper)
- The raw persistent data lives at `/mnt/help/upper/mnt/lfs/` (mount sdb2 directly at `/mnt/help`)

### Key Diagnostic Commands

```bash
# Find actual block device for a mount point
cat /proc/mounts | grep /mnt/lfs
findmnt -T /mnt/lfs
df -h /mnt/lfs

# Inspect overlay upperdir (where YOUR writes actually go)
mount /dev/sdb2 /mnt/help  # direct mount of persistence partition
ls /mnt/help/upper/mnt/lfs/  # only files you created/modified

# Compare combined vs upperdir
ls /mnt/lfs/proc | wc -l       # 357 (live kernel procfs)
ls /mnt/help/upper/mnt/lfs/proc | wc -l  # 0 (never written to disk)
```

### Verifying Target Disk Contents
```bash
# Check if target disk (e.g., /dev/sda2) has actual LFS content
mkdir -p /tmp/sda2_peek
mount -o ro /dev/sda2 /tmp/sda2_peek
du -sh /tmp/sda2_peek/        # Should be GBs, not KB
ls /tmp/sda2_peek/boot/       # Kernel, initramfs, GRUB config
cat /tmp/sda2_peek/etc/fstab  # Must point to correct root device
umount /tmp/sda2_peek
```

## Common Failure: Build on Wrong Device

**Symptoms:**
- `/mnt/lfs` shows full build (7GB+)
- Target disk (`/dev/sda2`) shows near-empty (164K skeleton)
- `/etc/fstab` correctly references `/dev/sda2` but data isn't there

**Root Cause:** Built inside chroot while `/mnt/lfs` was backed by USB persistence (`/dev/sdb2`), not the target internal drive.

**Fix:**
```bash
# 1. Mount target disk read-write
mount /dev/sda2 /mnt/sda2

# 2. Copy entire build from upperdir to target
cp -av /mnt/help/upper/mnt/lfs/* /mnt/sda2/

# 3. Mount EFI partition if needed
mount /dev/sda4 /mnt/sda2/boot/efi  # verify this is ESP first!

# 4. Chroot and install GRUB
chroot /mnt/sda2
grub-install --target=x86_64-efi --efi-directory=/boot/efi
update-grub
```

## GRUB Installation Checklist

Before running `grub-install`:
- [ ] Target root partition (`/dev/sda2`) has full LFS content (kernel, binaries, etc.)
- [ ] `/etc/fstab` on target references correct root UUID
- [ ] EFI System Partition identified (`blkid | grep vfat`, typically `/dev/sda4`)
- [ ] ESP mounted at `/boot/efi` inside chroot
- [ ] Kernel files present in `/boot` (`vmlinuz-*`, `System.map-*`, `config-*`)
- [ ] GRUB config directory exists (`/boot/grub/`)

## Pitfalls

1. **Building on USB persistence** — The build survives reboots but lands on the wrong disk. Symptom: `/mnt/lfs` shows 7GB+ while `/dev/sda2` shows a 164K skeleton. Fix: copy the upperdir to the target disk *before* running `grub-install`.
2. **Empty `/boot` on the target** — GRUB installs cleanly but the kernel is missing at boot. Always verify `ls /mnt/sda2/boot/` shows `vmlinuz-*` before bootloader work.
3. **Wrong EFI partition** — GRUB installs but firmware can't find it. Find the real ESP with `blkid | grep vfat` and mount it at `/boot/efi` inside the chroot; never assume `/dev/sda4`.
4. **fstab mismatch** — Kernel panic "can't mount root" after reboot. Verify `/etc/fstab` root UUID matches `blkid /dev/sda2` before closing the chroot.
5. **Overlay confusion** — Files appear and disappear between views. Use `/mnt/help/upper/...` for ground truth and `/mnt/lfs` for work; never copy from the combined view when you want the persistent layer.
6. **Persistent partition not mounted at `/mnt/help`** — The skill's ground-truth commands assume the persistence partition (`/dev/sdb2`, label `casper-rw`) is mounted read-write. If it's not, `ls /mnt/help/upper/...` silently shows nothing — mount it first and confirm the label with `blkid`.
7. **`du` on the wrong mount** — `du -sh /mnt/lfs` reports the combined view; a "full build" there doesn't prove anything about the target disk. Always measure the target and the upperdir separately.

## References
- `references/overlayfs-persistent-usb.md` — How Ubuntu live USB persistence works with overlayfs
- `references/grub-install-checklist.md` — Step-by-step GRUB installation verification
- `references/lfs-device-verification.md` — Commands to verify build location and target disk readiness