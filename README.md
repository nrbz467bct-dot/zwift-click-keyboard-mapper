# Zwift Click v2 → Keyboard Mapper (Windows)

Use your **Zwift Click v2** as a keyboard on Windows — bind any Click button to any key. Works with Zwift, MyWhoosh, indieVelo, emulators, or any app that takes keyboard input. Yes, you can play Pokémon on your trainer.

No companion app needed — connects directly to the Click over Bluetooth LE.

## Features

- All 10 buttons bindable (D-pad, A/B/Y/Z, plus/minus) via a simple `config.json`
- Real press-and-hold behaviour (key goes down when you press, up when you release) — works in games and emulators that poll key state
- Multiple simultaneous buttons (diagonals, combos)
- Hardware-level scan code injection (`pydirectinput`) — works where soft keypresses don't
- Auto-reconnect if the Click drops out
- Unknown buttons are auto-detected and printed so you can bind them

## Requirements

- Windows 10/11 with Bluetooth LE
- Python 3.10+ (tick **"Add Python to PATH"** during install!)
- A Zwift Click v2

## Setup

1. Install Python from https://www.python.org/downloads/
2. Open Command Prompt and run:
   ```
   pip install bleak pydirectinput
   ```
3. Download this repo (green **Code** button → Download ZIP) and extract it anywhere.

## Usage

1. Make sure the Click is **not** connected to Zwift / Companion / your phone — it can only talk to one thing at a time.
2. Press a Click button to wake it (blue blinking LED).
3. Right-click `start.bat` → **Run as administrator** (admin is needed for key injection into most apps).
4. Wait for "Connected". Done.

## Configuring bindings

Edit `config.json` in Notepad:

```json
"bindings": {
  "up": "up",
  "down": "down",
  "left": "left",
  "right": "right",
  "a": "x",
  "b": "z",
  "y": "v",
  "z": "c",
  "plus": "q",
  "minus": "w"
}
```

Left side = Click button, right side = keyboard key to send. Key names: letters, numbers, `up/down/left/right`, `space`, `enter`, `esc`, `f1`–`f12`, etc. Save and restart the script.

## Troubleshooting

- **"python not found"** — reinstall Python and tick "Add Python to PATH", or change `python` to `py` in start.bat
- **Device not found** — wake the Click (press a button); make sure nothing else is connected to it
- **Terminal shows presses but the app ignores them** — run as administrator; click the app window so it has focus; check the app's own key bindings match your config
- **`unbound button: btnX_Y`** — that button isn't in your config yet; add it using that exact name
- **LED flashing orange** — flat CR2032 battery

## Credits & disclaimer

Built on the BLE protocol reverse-engineering work in [andriuz29/Zwift-Click-V2-Universal-PC-Controller](https://github.com/andriuz29/Zwift-Click-V2-Universal-PC-Controller). Thanks!

**This is an unofficial community tool**, not affiliated with or endorsed by Zwift. The protocol is reverse-engineered — a Zwift firmware update could break it at any time. Use at your own risk.

## License

MIT — do whatever you want with it, no warranty.
