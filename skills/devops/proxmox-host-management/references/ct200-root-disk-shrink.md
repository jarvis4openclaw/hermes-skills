# CT 200 Root Disk Shrink — 2026-05-21

## Situation
- CT 200 (signal-scheduler, 192.168.100.47) root disk was over capacity
- Proxmox config said `rootfs: local-lvm:vm-200-disk-0,size=4G` (stale)
- Actual LVM volume: 24G, filesystem: 24G, used: 8.4G
- Target: 20G (shrink operation)

## Commands Run
```
pct stop 200
e2fsck -fy /dev/pve/vm-200-disk-0
resize2fs /dev/pve/vm-200-disk-0 20G
lvreduce -L 20G /dev/pve/vm-200-disk-0
pct set 200 -rootfs local-lvm:vm-200-disk-0,size=20G
pct start 200
```

## Result
- Filesystem: 20G, 8.5G used, 11G free (46%)
- Config metadata now in sync with actual volume
- All three layers (LVM, ext4, Proxmox config) agree at 20G
- Total downtime: ~30 seconds

## Lessons
- Config metadata was 4G while volume was 24G — always verify with `lvs` and `df`, don't trust config alone
- `lvreduce` detected filesystem was already shrunk and skipped its own fs resize — safe
- Thin pool data% was 71.71%, so freeing 4G back to the pool was beneficial
