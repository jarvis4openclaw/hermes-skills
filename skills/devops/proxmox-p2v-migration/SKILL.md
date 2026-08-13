---
category: devops
name: proxmox-p2v-migration
description: >
  Migrate a physical Windows machine (P2V) to a Proxmox VE VM. Covers
  Disk2VHD imaging, VHDX→qcow2 conversion, VM config creation, VirtIO
  driver injection, first-boot recovery, and transfer strategies for
  large disks.
version: 1.1.0
trigger: >
  User wants to convert a physical Windows PC/server to a Proxmox VM,
  mentions P2V, asks about migrating a Windows machine to Proxmox,
  or wants to retire a physical machine while keeping its OS.
metadata:
  hermes:
    trigger_conditions:
      - "convert a physical Windows machine to a Proxmox VM"
      - "P2V migration"
      - "migrate physical PC to virtual machine"
      - "Disk2VHD imaging"
      - "VHDX to qcow2 conversion"
      - "retire physical machine keep OS as VM"
      - "move Windows server to Proxmox"
      - "physical to virtual on Proxmox"
      - "VirtIO driver injection Windows VM"
      - "first boot Windows VM after P2V"
      - "qm create VM from converted disk"
      - "pmxcfs ghost file VM config"
      - "Windows BSOD after P2V conversion"
---

# Proxmox P2V Migration (Windows Physical → Virtual)

## When to Use

- Converting a physical Windows desktop or server into a Proxmox VM (P2V)
- Retiring physical hardware while keeping its OS, installed apps, and data intact
- Preserving a legacy Windows environment that must keep running after hardware decommissioning
- Creating a disposable clone of a physical machine for testing or disaster-recovery drills
- Standardizing a fleet of physical Windows boxes into VM templates

## Not For

- Converting Linux physical machines → use `proxmox` skill's migration guidance or a fresh VM + rsync instead
- Virtual-to-virtual (V2V) between Proxmox hosts → `qm vzdump`/backup restore is simpler
- Bare-metal image restores with PXE/Clonezilla → not a VM workflow
- Migrating to Hyper-V, ESXi, or KVM/libvirt → the qcow2 conversion differs per hypervisor
- Physical machines with hardware-dependent apps that will not run virtualized → assess first, then choose a reinstall path

## Overview

Convert a physical Windows machine into a Proxmox VM using Microsoft's Disk2VHD tool + `qemu-img` conversion.

## Prerequisites

- **Source**: Windows PC with Disk2VHD (Sysinternals) — [download](https://learn.microsoft.com/en-us/sysinternals/downloads/disk2vhd)
- **Target**: Proxmox VE host with enough free storage
- **Network**: Both machines on the same LAN preferred (for direct transfer)
- **ISO**: [VirtIO drivers ISO](https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/latest-virtio/virtio-win.iso) — upload to Proxmox before first boot

## Step 1: Image the Physical Machine (on Windows)

1. Download and run **Disk2VHD as Administrator**
2. Select volumes to capture (C: is essential; include data volumes as needed)
3. For **spanned/RAID volumes**: ensure all constituent disks are connected
4. Output destination: **external drive** or **network share** (NOT a disk being imaged)
5. ✅ Check **"Use Vhdx"** (modern format, handles >2TB)
6. Click **Create** — runs online via VSS (no reboot needed)

**Pitfall**: Disk2VHD captures the volume, not the partition table. If the source has a recovery partition or EFI system partition you want preserved, you may need an offline image (Hiren's Boot CD + `dd`). For most Windows desktops, volume-only capture is sufficient.

## Step 2: Transfer the VHDX to Proxmox

### Option A: Direct scp/rsync (fastest on LAN)
```bash
# On Proxmox, create a staging directory
mkdir -p /zfspool/data/p2v-tmp

# From Windows (PowerShell, with SSH setup):
scp "D:\image.vhdx" wahid@pve:/zfspool/data/p2v-tmp/

# Or rsync (resumable):
rsync -avh --progress /mnt/d/image.vhdx wahid@pve:/zfspool/data/p2v-tmp/
```

### Option B: External USB drive
- Write VHDX to USB drive from Windows
- Plug into Proxmox, mount, copy to staging dir

### Option C: SMB share
- Mount a Samba share from Proxmox to Windows and copy directly

**Large transfers**: 500GB over gigabit ≈ 1.5–2 hours. For very large transfers, use `rsync --partial` or split into chunks.

## Step 3: Convert VHDX → qcow2 (on Proxmox)

```bash
cd /zfspool/data/p2v-tmp
qemu-img convert -f vpc -O qcow2 image.vhdx image-disk.qcow2

# Verify
qemu-img info image-disk.qcow2
```

Conversion time: ~1–2 hours for 500GB depending on I/O speed.

**Surviving SSH disconnects with `screen`:** Since conversion takes hours, always run `qemu-img convert` inside a GNU `screen` session so it survives SSH disconnection:

```bash
# Start a named screen session
screen -S p2v-convert

# Run conversion (inside screen)
qemu-img convert -f vpc -O qcow2 image.vhdx output.qcow2

# Detach: Ctrl+A, then D
# Reattach: screen -r p2v-convert
# List sessions: screen -ls
```

Use `watch -n 10 'ls -lh output.qcow2'` in another terminal to monitor progress while it runs.

**Note**: qcow2 is thin-provisioned — the file size will be smaller than the VHDX's used space. Run `qemu-img info` to confirm the virtual size matches the original disk.

## Step 4: Pick a VM ID and Storage Location

### Storage options:

| Storage Type | Location | Pros | Cons |
|---|---|---|---|
| **A: File reference** (unregistered path) | Any writable dir, e.g. `/zfspool/data/p2v-tmp/` | Simplest, no config changes needed | No Proxmox UI integration — no snapshots/resize/backup from web UI. Manual lifecycle. |
| **B: Directory storage** (registered) | Add via Datacenter → Storage → Add → Directory | Fully managed, UI integration | One-time registration; mixes VM disks with personal data if using a shared dataset |
| **C: ZFS subvol** (recommended ★) | `zfs create zfspool/data/subvol-<VMID>-disk-0` then place qcow2 inside | Clean isolation, ZFS features per-disk (snapshots, quotas, compression), matches LXC CT pattern | Slightly more setup (must create subvol first) |

**Advanced Path C setup:** Create a dedicated ZFS subvol for the VM disk, analogous to how Proxmox CTs are provisioned:
```bash
# Create the subvol (filesystem, not volume)
zfs create zfspool/data/subvol-<VMID>-disk-0
zfs set quota=<size> zfspool/data/subvol-<VMID>-disk-0
mountpoint is /zfspool/data/subvol-<VMID>-disk-0

# Convert VHDX directly into it
qemu-img convert -f vpc -O qcow2 <vhd-path> /zfspool/data/subvol-<VMID>-disk-0/vm-<VMID>-disk-0.qcow2

# VM config references the file directly
scsi0: /zfspool/data/subvol-<VMID>-disk-0/vm-<VMID>-disk-0.qcow2,size=<size>
```
Benefits: isolated ZFS dataset, can set per-disk quotas/snapshots/compression, portable, and can later register the subvol as a storage pool.

If using an unregistered path (like a personal ZFS dataset), create the VM config manually or use `qm create` to register it.

## Step 5: Create the VM Config

### Via the Proxmox Web UI:
1. Create VM → skip disk
2. Attach the converted qcow2 as an **existing disk**
3. BIOS: **SeaBIOS** (matches legacy Windows boot)
4. Machine: **i440fx** (most compatible for P2V Windows)
5. SCSI: **VirtIO SCSI** controller
6. Attach VirtIO ISO to CD/DVD drive

### Manual config (`/etc/pve/qemu-server/<VMID>.conf` as root):
```ini
bios: seabios
cores: <match source CPU cores>
cpu: host
memory: <match source RAM in MB>
machine: i440fx
name: WIN-P2V
net0: virtio=<MAC>,bridge=vmbr0
ostype: win10
scsihw: virtio-scsi-single
scsi0: /path/to/image-disk.qcow2,size=<virtual-size>
ide2: local:iso/virtio-win.iso,media=cdrom
```

### **Recommended: Use `qm create` (bypasses pmxcfs issues)**
The `/etc/pve/` filesystem (pmxcfs) can enter a ghost state where it reports "file exists" for files that don't appear in `ls`. Instead of writing the config file directly, use Proxmox's `qm create` command which talks to the API and handles the cluster filesystem correctly:

```bash
sudo qm create <VMID> \
  --name <VM-NAME> \
  --bios seabios \
  --ostype win10 \
  --cores <cores> \
  --cpu host \
  --memory <ram-mb> \
  --scsihw virtio-scsi-single \
  --scsi0 /path/to/image-disk.qcow2,size=<virtual-size> \
  --ide2 local:iso/virtio-win.iso,media=cdrom \
  --net0 virtio,bridge=vmbr0 \
  --boot order=scsi0;ide2
```

**Note on `--machine`**: i440fx is the default for SeaBIOS, so you can omit `--machine` entirely. If you need to specify it explicitly, use `--machine type=i440fx` (not just `i440fx`).

### VM ID convention:
Check existing VMs (`ls /etc/pve/qemu-server/`) and pick a free ID out of their range.

## Step 6: First Boot — Windows P2V Recovery

1. **Start the VM** — Windows detects new "hardware" and will reconfigure
2. **Expect 1–2 reboots** — this is normal P2V behavior
3. **Install VirtIO drivers** when Windows loads:
   - Open Device Manager → find unknown devices
   - Update driver → Browse CD/DVD → `viostor\w10\amd64` (SCSI disk)
   - Repeat for network: `NetKVM\w10\amd64`
   - Optional: balloon driver, guest tools
4. **Windows activation** — likely required (hardware change triggers reactivation)

**Troubleshooting first boot:**
- **Blue screen (BSOD)**: Boot from VirtIO ISO and repair or try `machine: q35` instead of i440fx
- **No disk detected**: The SCSI driver isn't loaded — boot from VirtIO ISO, load driver from `viostor\w10\amd64` during disk selection
- **No network**: Install `NetKVM` drivers from the VirtIO ISO
- **Stuck at boot logo**: Increase boot timeout in Windows (bcdedit) or attach a VGA console

## Pitfalls

1. **Windows license reactivation** — P2V counts as new hardware, so Windows will demand reactivation on first boot. Have the product key ready; digital licenses tied to a Microsoft account can be transferred by signing in.
2. **Staging disk space under-estimated** — The staging area needs ~1.5× the VHDX size temporarily (VHDX + qcow2 coexist during conversion). Plan for it or the convert step dies mid-write with `no space left on device`; `df -h` the target before starting.
3. **VM ID conflicts** — Reusing a live VM ID silently corrupts the config. Always check `/etc/pve/qemu-server/` for existing IDs and pick a free one out of the range before `qm create`.
4. **Boot failure after conversion (BSOD or black screen)** — If SeaBIOS won't boot, switch the machine type to `q35` or add an EFI disk for OVMF (UEFI boot). Match the *source machine's* firmware type — a UEFI source virtualized with SeaBIOS will not boot.
5. **Installed apps expecting physical hardware** — Antivirus, licensing daemons, and GPU-accelerated apps may fail or refuse to start in a VM. Inventory software licenses and test the VM before decommissioning the source.
6. **Stale motherboard/chipset drivers** — Old chipset drivers left in place cause first-boot BSODs. Uninstall motherboard/chipset drivers from Windows *before* shutdown on the source machine.
7. **pmxcfs ghost files** — `/etc/pve/` is a FUSE cluster filesystem that can enter a ghost state where `nano/cat/tee` report "File exists" for files that don't appear in `ls`. Recovery: use `qm create` to register the VM via the Proxmox API instead of writing config files directly. If that also fails, restart the cluster service: `sudo systemctl restart pve-cluster` (safe on single-node setups).
8. **SSH disconnect kills a long conversion** — `qemu-img convert` on a 500 GB disk takes 1–2 hours; losing the SSH session aborts it. Always run the conversion inside `screen -S p2v-convert` and monitor with `watch -n 10 'ls -lh output.qcow2'` so it survives disconnects.
9. **Wrong disk format flag in `qemu-img convert`** — Disk2VHD writes VHDX by default, which is VPC format: `qemu-img convert -f vpc -O qcow2`. Using `-f vhdx` or omitting `-f` produces a corrupt or size-mismatched image. Verify with `qemu-img info` afterwards.
10. **No disk detected at first boot** — The VirtIO SCSI driver isn't loaded. Boot from the VirtIO ISO and load `viostor\w10\amd64` during disk selection, then install `NetKVM\w10\amd64` for networking.
11. **`--machine i440fx` rejected by `qm create`** — The value must be typed as `--machine type=i440fx`, not bare `i440fx`. Simpler: omit `--machine` entirely — i440fx is the default for SeaBIOS.
12. **Volume-only capture misses the partition table** — Disk2VHD captures volumes, not the partition table. If the source has a recovery partition or EFI system partition you must preserve, take an offline image (Hiren's Boot CD + `dd`) instead.

## Verification

```bash
# Check VM is running
qm status <VMID>

# Check console (headless)
qm terminal <VMID> --iface serial0

# Or use VNC via Proxmox web UI
```

## References

See `references/p2v-transfer-notes.md` for session-specific examples including large transfer strategies and storage layout decisions.
