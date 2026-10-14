# MAC Changer

![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/platform-windows-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)
![Version](https://img.shields.io/badge/version-1.0.0-orange?style=flat-square)

A Windows CLI tool to change, randomize, or restore the MAC address of any network adapter. Works by writing directly to the Windows registry and restarting the adapter via netsh.

---

## Requirements

- Python 3.10+
- Windows (uses `winreg` and `netsh`)
- Administrator privileges
- `colorama`

---

## Installation

### Windows

Double-click `install.bat`. It will request admin automatically and install all dependencies.

### Manual

```bash
git clone https://github.com/your-username/mac-changer.git
cd mac-changer
pip install -r requirements.txt
```

---

## Usage

All commands must be run as Administrator.

### List all adapters

```powershell
python mac_changer.py list
```

Shows every network adapter on the system with its index and current MAC address. Adapters with a custom MAC set will show the spoofed value highlighted in yellow.

### Randomize a MAC address

```powershell
python mac_changer.py change 0
```

Generates a random locally administered MAC and applies it to the adapter at index 0.

### Set a specific MAC address

```powershell
python mac_changer.py change 0 -m AA:BB:CC:DD:EE:FF
```

Applies the exact MAC you provide to the adapter at index 0.

### Restore the original hardware MAC

```powershell
python mac_changer.py restore 0
```

Removes the registry override and falls back to the MAC burned into the hardware.

---

## Full Example Session

```powershell
python mac_changer.py list

  #    Adapter                                       Current MAC
  -----------------------------------------------------------------------
  0    Realtek PCIe 2.5GbE Family Controller         B8:27:EB:44:55:66
  1    MediaTek Wi-Fi 6 MT7902LEN Wireless LAN Card  A4:C3:F0:11:22:33

python mac_changer.py change 1

  Adapter : MediaTek Wi-Fi 6 MT7902LEN Wireless LAN Card
  New MAC : F6:C4:72:28:EB:1C

  [OK] MAC address changed to F6:C4:72:28:EB:1C

python mac_changer.py change 1 -m DE:AD:BE:EF:00:01

  Adapter : MediaTek Wi-Fi 6 MT7902LEN Wireless LAN Card
  New MAC : DE:AD:BE:EF:00:01

  [OK] MAC address changed to DE:AD:BE:EF:00:01

python mac_changer.py restore 1

  Restoring original MAC for: MediaTek Wi-Fi 6 MT7902LEN Wireless LAN Card

  [OK] MAC address restored to hardware default.
```

---

## How It Works

1. Reads the Windows registry under `HKLM\SYSTEM\CurrentControlSet\Control\Class\{4D36E972...}` to enumerate all network adapters.
2. Writes the new MAC address to the `NetworkAddress` value of the target adapter's registry key.
3. Disables and re-enables the adapter via `netsh` so the change takes effect immediately.
4. To restore, it deletes the `NetworkAddress` value entirely so Windows falls back to the hardware MAC.

---

## Notes

- If you see `[WARN] Adapter restart may have failed`, the MAC was still written to the registry. Manually disable and re-enable the adapter in Device Manager to apply it.
- Not all adapters support MAC spoofing via registry. If the change does not stick, the NIC driver may be ignoring the `NetworkAddress` override.
- Changes do not survive a full driver reinstall on some NICs.
- WAN Miniport adapters are virtual and cannot be meaningfully changed.

---

## License

MIT
