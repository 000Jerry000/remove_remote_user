# RDP User Security Watchdog

A lightweight Python security watchdog for Windows that periodically checks the **Remote Desktop Users** local group and removes unauthorized accounts.

The default check interval is **1 minutes**.

> **Important:** This tool is intended as a defensive measure. If an unknown account is repeatedly recreated, the underlying malware or persistence mechanism should be investigated and removed. This script should not be considered a replacement for antivirus or a full system cleanup.

---

## Features

* Checks the Windows `Remote Desktop Users` group.
* Runs automatically every 1 minutes.
* Removes accounts that are not in the configured allowlist.
* Keeps specified legitimate users untouched.
* Records activity in a log file.
* Runs continuously in the background while the Python process is running.
* Requires Windows Administrator privileges.

---

## Requirements

### Operating System

* Windows 10
* Windows 11

### Software

* Python 3.9 or later

Python must be available from the command line:

```bat
python --version
```

Example:

```text
Python 3.12.5
```

---

## Project Structure

```text
rdp-guard/
│
├── rdp_guard.py
├── rdp_guard.log
└── README.md
```

`rdp_guard.log` will be created automatically when the program starts.

---

## Configuration

Open:

```text
rdp_guard.py
```

Find:

```python
ALLOWED_USERS = {
    "Administrator",
    # "YourWindowsUsername",
}
```

Add the Windows accounts that are allowed to use Remote Desktop.

For example:

```python
ALLOWED_USERS = {
    "Administrator",
    "Masao",
}
```

Only these accounts will be allowed to remain in the `Remote Desktop Users` group.

### Allow no Remote Desktop users

If Remote Desktop is not required on the computer:

```python
ALLOWED_USERS = set()
```

This causes every member of `Remote Desktop Users` to be removed.

---

## Check Interval

The default interval is:

```python
CHECK_INTERVAL = 1 * 60
```

This means:

```text
1 minutes × 60 seconds = 900 seconds
```

To check every 5 minutes:

```python
CHECK_INTERVAL = 5 * 60
```

To check every 30 minutes:

```python
CHECK_INTERVAL = 30 * 60
```

---

# Installation

## 1. Install Python

Install Python 3 from the official Python website.

During installation, make sure:

```text
Add Python to PATH
```

is enabled.

After installation, verify:

```bat
python --version
```

---

## 2. Create the project folder

For example:

```text
C:\RDPGuard
```

Place the following file inside:

```text
C:\RDPGuard\rdp_guard.py
```

---

## 3. Configure allowed users

Edit:

```text
C:\RDPGuard\rdp_guard.py
```

For example:

```python
ALLOWED_USERS = {
    "Masao",
}
```

Replace `Masao` with the actual Windows username that should be allowed.

---

# Find Your Windows Username

Open Command Prompt:

```bat
whoami
```

Example:

```text
DESKTOP-ABC123\Masao
```

The username is:

```text
Masao
```

You can also run:

```bat
echo %USERNAME%
```

---

# Check Existing Remote Desktop Users

Before running the watchdog, check the current members manually.

Open **Command Prompt as Administrator** and run:

```bat
net localgroup "Remote Desktop Users"
```

Example:

```text
Alias name     Remote Desktop Users

Members

-------------------------------------------------------------------------------
Masao
UnknownUser
The command completed successfully.
```

If `UnknownUser` is not legitimate, the watchdog will remove it when it runs.

---

# Running the Program

## Important

The program must run with **Administrator privileges**.

Open:

```text
Command Prompt
```

using:

```text
Run as administrator
```

Then:

```bat
cd C:\RDPGuard
```

Run:

```bat
python rdp_guard.py
```

You should see:

```text
============================================================
RDP USER SECURITY WATCHDOG
============================================================
Checking every 1 minutes.
Allowed users: Masao
```

The first security check happens immediately.

After that, the program waits 1 minutes and checks again.

---

# How It Works

The watchdog follows this cycle:

```text
              Start
                │
                ▼
       Check Administrator
          privileges
                │
                ▼
      Read Remote Desktop
          Users group
                │
                ▼
       Compare with allowlist
                │
          ┌─────┴─────┐
          │           │
       Allowed    Unauthorized
          │           │
          │           ▼
          │      Remove account
          │           │
          └─────┬─────┘
                │
                ▼
          Write log
                │
                ▼
          Wait 1 minutes
                │
                └──────────► Repeat
```

---

# Log File

The program creates:

```text
rdp_guard.log
```

Example:

```text
2026-08-10 22:00:01 | INFO | RDP Guard started.
2026-08-10 22:00:01 | INFO | Current Remote Desktop Users: ['Masao', 'UnknownUser']
2026-08-10 22:00:01 | INFO | Allowed RDP user: Masao
2026-08-10 22:00:01 | WARNING | Unauthorized Remote Desktop user detected: UnknownUser
2026-08-10 22:00:01 | WARNING | Removed unauthorized RDP user: UnknownUser
```

The log is useful for determining whether an unknown account continues to appear.

---

# Testing

You can test the watchdog with a test account.

First create a temporary local account:

```bat
net user TestRDPGuard Password123! /add
```

Add it to Remote Desktop Users:

```bat
net localgroup "Remote Desktop Users" TestRDPGuard /add
```

Verify:

```bat
net localgroup "Remote Desktop Users"
```

You should see:

```text
TestRDPGuard
```

Now run:

```bat
python rdp_guard.py
```

If `TestRDPGuard` is not in `ALLOWED_USERS`, it should be removed.

Verify again:

```bat
net localgroup "Remote Desktop Users"
```

You should no longer see:

```text
TestRDPGuard
```

After testing, remove the test account completely:

```bat
net user TestRDPGuard /delete
```

---

# Running Automatically

The Python program only runs while its process is running.

For continuous protection, you can configure it to start automatically with Windows using **Task Scheduler**.

## Recommended Task Scheduler settings

Open:

```text
Task Scheduler
```

Create a new task.

### General

Set:

```text
Name:
RDP Security Watchdog
```

Enable:

```text
Run whether user is logged on or not
```

and:

```text
Run with highest privileges
```

Select:

```text
Configure for:
Windows 10 / Windows 11
```

---

## Trigger

Create a trigger:

```text
At startup
```

This starts the watchdog when Windows starts.

---

## Action

Program:

```text
C:\Path\To\Python\python.exe
```

Arguments:

```text
C:\RDPGuard\rdp_guard.py
```

Start in:

```text
C:\RDPGuard
```

Adjust the Python path according to your installation.

You can find the Python executable with:

```bat
where python
```

Example:

```text
C:\Users\Masao\AppData\Local\Programs\Python\Python312\python.exe
```

---

# Security Considerations

This program only monitors membership of:

```text
Remote Desktop Users
```

It does **not** detect every type of malware.

If an attacker or malware has Administrator/SYSTEM privileges, it may be able to:

* recreate the account
* create another administrator account
* modify the Windows registry
* enable Remote Desktop
* create scheduled tasks
* install a Windows service
* modify firewall rules
* terminate this watchdog
* modify or delete the log
* establish another remote-access mechanism

Therefore, if an unauthorized account keeps coming back, investigate the underlying system rather than simply increasing the watchdog frequency.

---

# Recommended Incident Response

If you believe the PC is currently compromised:

## 1. Disconnect from the Internet

Temporarily disconnect:

```text
Ethernet
```

or:

```text
Wi-Fi
```

This can prevent an attacker from continuing remote access while you investigate.

---

## 2. Check local accounts

```bat
net user
```

Look for accounts you do not recognize.

---

## 3. Check Administrators

```bat
net localgroup administrators
```

Look for unexpected accounts.

---

## 4. Check Remote Desktop Users

```bat
net localgroup "Remote Desktop Users"
```

Look for unexpected accounts.

---

## 5. Check Remote Desktop configuration

You can inspect the current RDP configuration with:

```bat
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections
```

Generally:

```text
1 = RDP disabled
0 = RDP enabled
```

If you don't need Remote Desktop, disabling it is preferable.

---

## 6. Run a full malware scan

Use a reputable, fully updated security product and perform a **full system scan**.

For a suspected active compromise, consider using an **offline scan** as well.

---

# Limitations

This program is intentionally simple.

It monitors:

```text
Remote Desktop Users
```

It does not provide:

```text
❌ Full malware detection
❌ Antivirus functionality
❌ Network intrusion detection
❌ Credential protection
❌ Rootkit detection
❌ Complete persistence detection
❌ Guaranteed protection against Administrator-level malware
```

It should therefore be treated as an additional defensive layer rather than a complete security solution.

---

# Troubleshooting

## "This program must be run as Administrator."

Close the terminal and open:

```text
Command Prompt → Run as administrator
```

Then run:

```bat
python rdp_guard.py
```

---

## Python is not recognized

If you see:

```text
'python' is not recognized as an internal or external command
```

run:

```bat
where python
```

If Python is installed but not in PATH, use the full path:

```bat
"C:\Path\To\Python\python.exe" C:\RDPGuard\rdp_guard.py
```

---

## The account comes back after removal

This is the most important situation.

If:

```text
UnknownUser
```

is removed and later appears again, **do not assume the watchdog has failed**.

It may indicate that another process is recreating the account.

Check:

```bat
net user
```

```bat
net localgroup administrators
```

```bat
schtasks /query /fo LIST /v
```

```bat
sc query
```

and perform a full malware/security investigation.

---

# License

This project is intended for personal defensive security and system administration purposes.

Use it only on computers that you own or are authorized to administer.
