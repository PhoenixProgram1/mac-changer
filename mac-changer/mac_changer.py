import sys
import re
import random
import argparse
import subprocess
import winreg
from pathlib import Path

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    COLORAMA = True
except ImportError:
    COLORAMA = False


ADAPTER_KEY = r"SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}"


def c(text, color):
    if not COLORAMA:
        return text
    colors = {
        "green":  Fore.GREEN,
        "yellow": Fore.YELLOW,
        "red":    Fore.RED,
        "cyan":   Fore.CYAN,
        "white":  Fore.WHITE,
        "magenta": Fore.MAGENTA,
    }
    return f"{colors.get(color, '')}{text}{Style.RESET_ALL}"


def is_admin():
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_adapters():
    adapters = []
    try:
        reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, ADAPTER_KEY)
    except Exception:
        return adapters

    i = 0
    while True:
        try:
            subkey_name = winreg.EnumKey(reg, i)
            i += 1
            if not subkey_name.isdigit():
                continue
            subkey_path = f"{ADAPTER_KEY}\\{subkey_name}"
            subkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path)
            try:
                driver_desc, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                try:
                    net_cfg_id, _ = winreg.QueryValueEx(subkey, "NetCfgInstanceId")
                except:
                    net_cfg_id = None
                try:
                    current_mac, _ = winreg.QueryValueEx(subkey, "NetworkAddress")
                except:
                    current_mac = None
                adapters.append({
                    "index":      subkey_name,
                    "name":       driver_desc,
                    "cfg_id":     net_cfg_id,
                    "custom_mac": current_mac,
                })
            except:
                pass
            winreg.CloseKey(subkey)
        except OSError:
            break

    winreg.CloseKey(reg)
    return adapters


def get_current_mac(adapter_name):
    try:
        out = subprocess.check_output(
            ["getmac", "/v", "/fo", "csv"],
            stderr=subprocess.DEVNULL
        ).decode(errors="ignore")
        for line in out.splitlines():
            if adapter_name.lower() in line.lower():
                parts = line.split(",")
                if len(parts) >= 2:
                    mac = parts[1].strip().strip('"').replace("-", ":").upper()
                    if re.match(r"([0-9A-F]{2}:){5}[0-9A-F]{2}", mac):
                        return mac
    except:
        pass
    return "Unknown"


def random_mac():
    mac = [random.randint(0x00, 0xff) for _ in range(6)]
    mac[0] = (mac[0] & 0xfc) | 0x02
    return "".join(f"{b:02X}" for b in mac)


def set_mac(adapter_index, adapter_name, new_mac):
    subkey_path = f"{ADAPTER_KEY}\\{adapter_index}"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            subkey_path,
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "NetworkAddress", 0, winreg.REG_SZ, new_mac)
        winreg.CloseKey(key)
    except Exception as e:
        print(c(f"  [ERROR] Registry write failed: {e}", "red"))
        return False

    disable = subprocess.run(
        ["netsh", "interface", "set", "interface", adapter_name, "disable"],
        capture_output=True
    )
    enable = subprocess.run(
        ["netsh", "interface", "set", "interface", adapter_name, "enable"],
        capture_output=True
    )

    if disable.returncode != 0 or enable.returncode != 0:
        print(c(f"  [WARN] Adapter restart may have failed. Try disabling/enabling manually.", "yellow"))

    return True


def remove_mac(adapter_index, adapter_name):
    subkey_path = f"{ADAPTER_KEY}\\{adapter_index}"
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            subkey_path,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, "NetworkAddress")
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
    except Exception as e:
        print(c(f"  [ERROR] Registry write failed: {e}", "red"))
        return False

    subprocess.run(["netsh", "interface", "set", "interface", adapter_name, "disable"], capture_output=True)
    subprocess.run(["netsh", "interface", "set", "interface", adapter_name, "enable"], capture_output=True)
    return True


def cmd_list(args):
    adapters = get_adapters()
    if not adapters:
        print(c("No network adapters found.", "red"))
        return

    print()
    print(c(f"  {'#':<4} {'Adapter':<45} {'Current MAC'}", "cyan"))
    print(c("  " + "-" * 70, "white"))
    for i, a in enumerate(adapters):
        mac = get_current_mac(a["name"])
        tag = c(f"  ({a['custom_mac']})", "yellow") if a["custom_mac"] else ""
        print(f"  {c(str(i), 'magenta'):<4} {a['name']:<45} {mac}{tag}")
    print()


def cmd_change(args):
    adapters = get_adapters()
    if not adapters:
        print(c("No adapters found.", "red"))
        return

    try:
        idx = int(args.adapter)
        adapter = adapters[idx]
    except (ValueError, IndexError):
        print(c(f"Invalid adapter index. Run 'list' to see available adapters.", "red"))
        return

    if args.mac:
        new_mac = args.mac.upper().replace(":", "").replace("-", "")
        if not re.match(r"^[0-9A-F]{12}$", new_mac):
            print(c("Invalid MAC format. Use XX:XX:XX:XX:XX:XX", "red"))
            return
    else:
        new_mac = random_mac()

    formatted = ":".join(new_mac[i:i+2] for i in range(0, 12, 2))
    print(c(f"\n  Adapter : {adapter['name']}", "cyan"))
    print(c(f"  New MAC : {formatted}", "cyan"))
    print()

    if set_mac(adapter["index"], adapter["name"], new_mac):
        print(c(f"  [OK] MAC address changed to {formatted}", "green"))
    else:
        print(c("  [FAIL] Could not change MAC address.", "red"))
    print()


def cmd_restore(args):
    adapters = get_adapters()
    if not adapters:
        print(c("No adapters found.", "red"))
        return

    try:
        idx = int(args.adapter)
        adapter = adapters[idx]
    except (ValueError, IndexError):
        print(c("Invalid adapter index. Run 'list' to see available adapters.", "red"))
        return

    print(c(f"\n  Restoring original MAC for: {adapter['name']}", "cyan"))
    print()

    if remove_mac(adapter["index"], adapter["name"]):
        print(c("  [OK] MAC address restored to hardware default.", "green"))
    else:
        print(c("  [FAIL] Could not restore MAC address.", "red"))
    print()


def build_parser():
    p = argparse.ArgumentParser(
        prog="mac_changer",
        description="Change or restore MAC addresses on Windows network adapters."
    )
    sub = p.add_subparsers(dest="command")

    sub.add_parser("list", help="List all network adapters and their current MACs.")

    ch = sub.add_parser("change", help="Change the MAC address of an adapter.")
    ch.add_argument("adapter", help="Adapter index from the list command.")
    ch.add_argument("-m", "--mac", help="Specific MAC to set (XX:XX:XX:XX:XX:XX). Random if omitted.", default=None)

    rs = sub.add_parser("restore", help="Restore the original hardware MAC address.")
    rs.add_argument("adapter", help="Adapter index from the list command.")

    return p


def main():
    if not is_admin():
        print(c("\n  [ERROR] Run as Administrator.\n", "red"))
        sys.exit(1)

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        cmd_list(args)
    elif args.command == "change":
        cmd_change(args)
    elif args.command == "restore":
        cmd_restore(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
