"""
Zwift Click v2 -> Keyboard Mapper
Connects directly to a Zwift Click v2 over Bluetooth LE and turns button
presses into keyboard keystrokes. Edit config.json to change key bindings.

Run:  python zwift_click_mapper.py
Stop: Ctrl+C in the terminal window
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import platform

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("Missing library. Run:  pip install bleak")
    sys.exit(1)

# --- key injection backend: pydirectinput on Windows, pynput elsewhere ---
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import pydirectinput
    except ImportError:
        print("Missing library. Run:  pip install pydirectinput")
        sys.exit(1)
    pydirectinput.PAUSE = 0  # remove built-in delay for low latency

    def key_down_raw(key):
        pydirectinput.keyDown(key)

    def key_up_raw(key):
        pydirectinput.keyUp(key)
else:
    try:
        from pynput.keyboard import Controller, Key
    except ImportError:
        print("Missing library. Run:  pip install pynput")
        sys.exit(1)
    _kb = Controller()

    def _to_key(name):
        name = name.lower()
        if len(name) == 1:
            return name
        try:
            return Key[name.replace(" ", "_")]
        except KeyError:
            print(f"Unknown key name in config: '{name}'")
            return None

    def key_down_raw(key):
        k = _to_key(key)
        if k is not None:
            _kb.press(k)

    def key_up_raw(key):
        k = _to_key(key)
        if k is not None:
            _kb.release(k)

# ---------------------------------------------------------------- config ---
CONFIG_PATH = Path(__file__).parent / "config.json"

DEFAULTS = {
    "device_name_filter": "Zwift Click",
    "bindings": {
        "plus": "k",
        "minus": "i",
        "up": "u",
        "down": "down",
        "left": "left",
        "right": "right",
    },
    "hold_to_repeat": ["plus", "minus"],
    "repeat_initial_delay_ms": 350,
    "repeat_interval_ms": 150,
    "debounce_ms": 60,
}


def load_config():
    cfg = dict(DEFAULTS)
    if CONFIG_PATH.exists():
        try:
            user = json.loads(CONFIG_PATH.read_text())
            for k, v in user.items():
                if k == "bindings":
                    cfg["bindings"] = {**DEFAULTS["bindings"], **v}
                else:
                    cfg[k] = v
        except json.JSONDecodeError as e:
            print(f"config.json has an error ({e}). Using defaults.")
    else:
        CONFIG_PATH.write_text(json.dumps(DEFAULTS, indent=2))
        print(f"Created default config at {CONFIG_PATH}")
    return cfg


# ------------------------------------------------------------- protocol ---
NOTIFY_CHAR = "00000002-19ca-4651-86e5-fa29dcdd09d1"
WRITE_CHAR = "00000003-19ca-4651-86e5-fa29dcdd09d1"
HANDSHAKE = ["526964654f6e0203", "000800", "000810"]
KEEPALIVE = "000810"

# Each button is one bit in a 4-byte mask (bit cleared = pressed).
# Known bits get friendly names; unknown ones show as btn<byte>_<bit>
# in the terminal — add them to config.json bindings with that name.
BIT_NAMES = {
    (0, 0): "left",
    (0, 1): "up",
    (0, 2): "right",
    (0, 3): "down",
    (0, 4): "a",
    (0, 5): "b",
    (0, 6): "y",
    (1, 0): "z",
    (1, 1): "minus",
    (1, 5): "plus",
}


def decode_buttons(hx):
    """Return set of pressed button names from a 2308...0F state packet."""
    mask = bytes.fromhex(hx[4:12])
    pressed = set()
    for i, byte in enumerate(mask):
        for bit in range(8):
            if not byte & (1 << bit):
                pressed.add(BIT_NAMES.get((i, bit), f"btn{i}_{bit}"))
    return pressed


class ClickMapper:
    def __init__(self, cfg):
        self.cfg = cfg
        self.bindings = cfg["bindings"]
        self.repeat_buttons = set(cfg.get("hold_to_repeat", []))
        self.debounce = cfg.get("debounce_ms", 60) / 1000
        self.initial_delay = cfg.get("repeat_initial_delay_ms", 350) / 1000
        self.interval = cfg.get("repeat_interval_ms", 150) / 1000
        self.last_press = {}
        self.pressed = set()

    def key_down(self, button):
        key = self.bindings.get(button)
        if not key:
            return
        now = time.time()
        if now - self.last_press.get(button, 0) < self.debounce:
            return
        self.last_press[button] = now
        key_down_raw(key)
        print(f"  {button:<6} -> {key} DOWN")

    def key_up(self, button):
        key = self.bindings.get(button)
        if not key:
            return
        key_up_raw(key)
        print(f"  {button:<6} -> {key} UP")

    def handle(self, _sender, data: bytearray):
        hx = data.hex().upper()
        if not hx.startswith("2308") or len(hx) != 14:
            return
        now_pressed = decode_buttons(hx)
        for button in now_pressed - self.pressed:
            if button not in self.bindings:
                print(f"  unbound button: {button}  (add it to config.json)")
            self.key_down(button)
        for button in self.pressed - now_pressed:
            self.key_up(button)
        self.pressed = now_pressed


async def connect_once(cfg, mapper):
    print("Searching for Zwift Click... (press a button to wake it)")
    device = await BleakScanner.find_device_by_filter(
        lambda d, ad: d.name and cfg["device_name_filter"] in d.name,
        timeout=15.0,
    )
    if not device:
        return False

    print(f"Found: {device.name} [{device.address}] — connecting...")
    async with BleakClient(device.address) as client:
        await client.start_notify(NOTIFY_CHAR, mapper.handle)
        for msg in HANDSHAKE:
            await client.write_gatt_char(
                WRITE_CHAR, bytearray.fromhex(msg), response=False
            )
            await asyncio.sleep(0.1)

        print("\n=== Connected. Bindings ===")
        for btn, key in cfg["bindings"].items():
            tag = " (hold repeats)" if btn in mapper.repeat_buttons else ""
            print(f"  {btn:<6} -> {key}{tag}")
        print("Ctrl+C to quit.\n")

        while client.is_connected:
            await client.write_gatt_char(
                WRITE_CHAR, bytearray.fromhex(KEEPALIVE), response=False
            )
            await asyncio.sleep(5)
    return True


async def main():
    cfg = load_config()
    mapper = ClickMapper(cfg)
    while True:
        try:
            found = await connect_once(cfg, mapper)
            if not found:
                print("Not found. Retrying in 5s... (is the Click awake/blinking blue?)")
                await asyncio.sleep(5)
            else:
                print("Disconnected. Reconnecting...")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Connection error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye.")
