---
name: windows-ssh
description: Manage Windows hosts over OpenSSH — reliable commands, known failure modes, and .NET workarounds for non-interactive SSH sessions. Use when running remote commands on Windows via SSH.
version: 1.1.0
triggers:
  - windows ssh
  - remote windows
  - powershell over ssh
  - windows disk space
  - windows event log
  - ARCTIC
metadata:
  hermes:
    trigger_conditions:
      - "windows ssh"
      - "remote windows command"
      - "powershell over ssh"
      - "check windows disk space"
      - "windows event log"
      - "ARCTIC PC"
      - "connect to windows machine"
      - "ssh into windows"
      - "windows server remote"
      - "windows uptime check"
      - "windows process list"
      - "windows memory usage"
      - "windows cpu usage"
---

# Windows SSH Management

## When to Use

- Running remote commands on Windows machines over SSH
- Checking disk space, CPU, memory, or uptime on a Windows host
- Retrieving event logs from Windows servers
- Managing processes on remote Windows machines
- Setting up OpenSSH on a Windows host for the first time
- Debugging SSH key authentication failures on Windows
- Working with ARCTIC (Boss's main Windows PC at 192.168.100.18)
- Replacing WMI/CIM calls that fail in non-interactive SSH sessions

## Not For

- **Linux/macOS remote management** → use standard SSH; these Windows-specific workarounds don't apply
- **Interactive PowerShell sessions** → use `ssh -t` for PTY; this skill covers non-interactive command execution only
- **Windows Remote Desktop (RDP)** → use `xfreerdp` or `mstsc` instead
- **WinRM/PSRemoting** → use `pywinrm` or `Invoke-Command` instead; this skill covers SSH only
- **Windows service management requiring elevation** → SSH user is non-admin; use `sc` with admin credentials or RDP
- **File transfer to/from Windows** → use `scp` or `rsync` directly; these don't need the .NET workarounds

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

## Pitfalls

1. **Administrator accounts cannot use SSH keys** — Windows UAC token filtering strips the admin token over SSH, so `authorized_keys` is ignored even if the file exists and has correct permissions. Always use a dedicated non-admin local user (e.g., `sshuser`). Verify with `whoami /groups | findstr "Mandatory Label"` — it should show "Medium Mandatory Level," not "High."

2. **Microsoft Account users cannot use SSH keys** — OpenSSH cannot reliably resolve Microsoft Account (Outlook/Hotmail) identities because the home directory path includes the email domain. Create a local Windows user: `net user sshuser <password> /add`. Local accounts use `C:\Users\sshuser` which OpenSSH can resolve.

3. **`Get-PSDrive C` returns 0 free space** — PowerShell drive providers are not fully initialized in non-interactive SSH sessions. Always use `[System.IO.DriveInfo]::GetDrives()` instead of `Get-PSDrive` for disk queries. The .NET API doesn't depend on PowerShell providers.

4. **WMI/CIM returns Access Denied** — WMI requires admin privileges and an interactive logon session. Use .NET APIs: `System.IO.DriveInfo` for disks, `System.Diagnostics.Process` for process info, and `Get-Counter` for performance counters. These work without elevation.

5. **`authorized_keys` file locked or undeletable** — Windows Defender, SYSTEM, or sshd may hold file handles. Stop sshd and ssh-agent: `Stop-Service sshd; Stop-Service ssh-agent`. Disable Defender real-time scanning temporarily, then rename the file: `ren authorized_keys authorized_keys.old`. Recreate under the correct user, then restart sshd.

6. **Home directory not resolved by OpenSSH** — OpenSSH can't find `C:\Users\<user>\.ssh\authorized_keys` if the home directory isn't set correctly. Fix: `Set-LocalUser -Name "sshuser" -HomeDirectory "C:\Users\sshuser"`. Alternatively, add `AuthorizedKeysFile C:/Users/%u/.ssh/authorized_keys` to `C:\ProgramData\ssh\sshd_config`.

7. **Default shell is cmd.exe, not PowerShell** — Windows SSH defaults to `cmd.exe`, which doesn't support PowerShell syntax. Set PowerShell as default: `New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -PropertyType String -Force`. Restart sshd after.

8. **Exit code 0 even when PowerShell command fails** — Windows SSH can return exit code 0 even when PowerShell throws a terminating error. Always check stdout for error strings like "Cannot", "Access Denied", "Exception", or "Error" rather than relying on exit codes. Pipe stderr explicitly: `powershell -Command "..." 2>&1`.

9. **PowerShell `-Command` with nested quotes breaks** — PowerShell's quote escaping is different from bash. Use backslash-escaped double quotes inside the PowerShell command: `ssh user@host "powershell -Command \"Get-Process | Select-Object -First 5\""`. For complex commands, base64-encode: `powershell -EncodedCommand $(echo '<command>' | iconv -t UTF-16LE | base64 -w0)`.

10. **`sshd_config` location is different from Linux** — Windows OpenSSH stores config at `C:\ProgramData\ssh\sshd_config` (not `/etc/ssh/sshd_config`). Modifying the wrong file has no effect. After changes, restart sshd: `Restart-Service sshd`.

11. **ACL corruption when modifying `.ssh` from another user account** — Windows ACLs on `C:\Users\sshuser\.ssh` are user-specific. Modifying `authorized_keys` from a different account (even as Administrator) can corrupt the ACL and lock out the SSH user. Always use `icacls` to reset permissions after any file change: `icacls "C:\Users\sshuser\.ssh\authorized_keys" /inheritance:r /grant:r "sshuser:(R,W)"`.

12. **`Get-Counter` fails with "The specified object was not found"** — Performance counters may not be registered in a minimal Windows install. Rebuild counter registry: `lodctr /R` (requires admin). If still failing, check if the counter exists: `Get-Counter -ListSet * | Where-Object { $_.CounterSetName -match "Memory|Processor" }`.