# Spotold

Independent enemy spotting indicator port targeting World of Tanks 2.4.1. No `oldskool` / `modscore` imports.

## Implemented
- State engine: never seen, spotted, spotted previously; reset on battle start.
- Config model: two visual styles (eyes/dots), left/right positioning, horizontal offset, colorblind indicators, optional prestige hiding.
- Unit tests: `python -m unittest discover -s tests` (3 passing).

## Pending (NOT READY FOR GAME INSTALLATION)
- Recover and validate original protected `mod_spottedStatus.pyc` behavior.
- Port actual 2.4.1 battle visibility events and native players-panel integration.
- Package the eight original PNG assets in a WOT-compatible distribution and verify gameplay.

Original mod reference: `spottedStatus_1.4.0.zip`; old panel API reference: `modscore(1).zip`.

The provided `deobfuscate(4).py` relies on Python 2.7, executes extracted bytecode and is not safe to run against untrusted artifacts outside isolation. It was inspected but **not executed**. The supplied `.skill` pipeline also refers to a separate missing `deobfuscate_protected.py` tool. No full decompilation or in-game compatibility is claimed.
