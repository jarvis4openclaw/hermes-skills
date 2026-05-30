---
name: windows-ssh
description: Manage Windows hosts over OpenSSH — reliable commands, known failure modes, and .NET workarounds for non-interactive SSH sessions. Use when running remote commands on Windows via SSH.
triggers:
  - windows ssh
  - remote windows
  - powershell over ssh
  - windows disk space
  - windows event log
  - ARCTIC
---

# Windows SSH Management

## Known Hosts
- **ARCTIC** — Boss's main Windows PC — `sshuser@192.168.100.18` — key: `/home/wahid/.ssh/id_ed25519`

## SSH Command Template
```bash
ssh -o StrictHostKeyChecking=no -i /home/wahid/.ssh/id_ed25519 sshuser@192.168.100.18 "powershell -NoProfile -Command \"<COMMAND>\""
```

---

## Critical Limitations of Windows OpenSSH Sessions

Windows SSH is NOT a full POSIX environment. It runs in a restricted, non-interactive, non-elevated logon session with:
- No full user profile loading
- No elevation
- No Explorer shell
- Limited WMI/CIM access
- Inconsistent home directory resolution

---

## Commands That FAIL in SSH Sessions

| Command | Failure | Reason |
|--------|---------|--------|
| `(Get-PSDrive C).Free` | Returns 0 | Provider not initialized |
| `Get-CimInstance Win32_*` | Access Denied | Requires admin + interactive logon |
| `Get-WmiObject Win32_*` | Access Denied | Same as above |
| `Get-Volume` | Access Denied | Requires elevation |
| `Get-Partition` | Access Denied | Requires elevation |
| `Get-ComputerInfo` | Partial/empty | Requires full profile |
| `Get-ChildItem Env:` | Missing entries | Profile not loaded |

---

## Reliable .NET Replacements

### Disk Free Space (C: drive)
```powershell
([System.IO.DriveInfo]::GetDrives() | Where-Object { $_.Name -eq 'C:\' }).AvailableFreeSpace / 1GB
```

### All Drives
```powershell
[System.IO.DriveInfo]::GetDrives() | ForEach-Object { "$($_.Name) Free: $([math]::Round($_.AvailableFreeSpace/1GB,2)) GB Total: $([math]::Round($_.TotalSize/1GB,2)) GB" }
```

### CPU Usage
```powershell
(Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples.CookedValue
```

### Memory Available (MB)
```powershell
(Get-Counter '\Memory\Available MBytes').CounterSamples.CookedValue
```

### Event Log (last 10 System errors)
```powershell
Get-EventLog -LogName System -EntryType Error -Newest 10 | Select-Object TimeGenerated, Source, Message | Format-List
```

### Running Processes (top 10 by CPU)
```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet | Format-Table
```

### Uptime
```powershell
(Get-Date) - (gcim Win32_OperatingSystem).LastBootUpTime
```
Note: `gcim` (Get-CimInstance) may fail for non-admin users — use this alternative:
```powershell
(Get-Date) - [System.DateTime]::FromFileTime((Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters').BootId)
```

---

## ARCTIC (Boss's Main Windows PC)
- **Host:** ARCTIC
- **IP:** 192.168.100.18
- **User:** sshuser
- **Key:** /home/wahid/.ssh/id_ed25519
- **Note:** sshuser is a non-admin local account (required for key auth to work)

---

## Known Issues & Workarounds

### 1. Administrator Accounts Cannot Use SSH Keys
**Cause:** Windows UAC token filtering — admin users don't get a full token over SSH, so `authorized_keys` is ignored.
**Workaround:** Always use a dedicated non-admin local user (e.g., `sshuser`).

### 2. Microsoft Account Users Cannot Use SSH Keys
**Cause:** OpenSSH cannot reliably resolve Microsoft Account (Outlook/Hotmail) identities.
**Workaround:** Create a local Windows user: `net user sshuser <password> /add`

### 3. `Get-PSDrive` Returns Zero
**Cause:** PowerShell drive providers are not fully initialized in SSH sessions.
**Workaround:** Use `[System.IO.DriveInfo]::GetDrives()` instead (see above).

### 4. WMI/CIM Returns Access Denied
**Cause:** WMI requires admin privileges and an interactive logon session.
**Workaround:** Use .NET APIs (`System.IO.DriveInfo`, `System.Diagnostics.Process`, `Get-Counter`).

### 5. `authorized_keys` Locked / Undeletable
**Cause:** File locked by Windows Defender, SYSTEM, or sshd.
**Fix:**
```powershell
Stop-Service sshd
Stop-Service ssh-agent
# Disable Defender real-time scanning temporarily
ren authorized_keys authorized_keys.old
# Recreate under correct user account
Start-Service sshd
```

### 6. Home Directory Not Resolved
**Cause:** OpenSSH can't find `C:\Users\<user>\.ssh\authorized_keys`.
**Fix:**
```powershell
Set-LocalUser -Name "sshuser" -HomeDirectory "C:\Users\sshuser"
```
Or in `C:\ProgramData\ssh\sshd_config`:
```
AuthorizedKeysFile C:/Users/%u/.ssh/authorized_keys
```

### 7. Default Shell is cmd.exe, Not PowerShell
**Cause:** Windows SSH defaults to `cmd.exe`.
**Fix (set PowerShell as default):**
```powershell
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force
```

### 8. Exit Code 0 on PowerShell Errors
**Cause:** Windows SSH can return exit code 0 even when PowerShell throws a terminating error.
**Workaround:** Always check stdout for error strings, not just exit codes.

---

## Setup (One-Time, Run as Administrator on Windows)

```powershell
# 1. Install OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# 2. Start and auto-start sshd
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

# 3. Open firewall
New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -LocalPort 22 -Protocol TCP -Direction Inbound -Action Allow

# 4. Create dedicated SSH user (non-admin)
net user sshuser <password> /add

# 5. Add authorized key
$sshDir = "C:\Users\sshuser\.ssh"
New-Item -ItemType Directory -Path $sshDir -Force
Add-Content -Path "$sshDir\authorized_keys" -Value "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIE6uY5VGOSB3IvsNY2R+1E34+/7LNtNE/KCFnQt1yEUC jarvis@clawd"
icacls $sshDir /inheritance:r /grant:r "sshuser:(R,W)"
icacls "$sshDir\authorized_keys" /inheritance:r /grant:r "sshuser:(R,W)"

# 6. Restart sshd
Restart-Service sshd
```

---

## Best Practices for Autonomous Agent Use
1. Never use WMI/CIM — use .NET APIs
2. Never add SSH user to Administrators group — breaks key auth
3. Always use a dedicated local user (not Microsoft Account)
4. Never modify `.ssh` from another user account — causes ACL corruption
5. Restart sshd after modifying `authorized_keys`
6. Check stdout for errors, not just exit codes
7. `sshd_config` is at `C:\ProgramData\ssh\sshd_config` (not `/etc/ssh/`)
