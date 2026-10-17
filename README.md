# INQ SPOT — Gameface prototype (WoT 2.4.1.0)

Status: **development / not a verified working in-game release**.

## Architecture
- `src/mod_inq_spot.py` — original spotting logic from recovered OldSkool 1.4.0 Python, event hooks, no OldSkool dependency.
- `src/inq_spot_gameface.py` — Wulf/Gameface ViewModel, ViewImpl, WindowImpl adapter.
- `resources/gui/gameface/mods/inq_spot/` — HTML/CSS/JavaScript.
- `resources/gui/gen_resources/inq_spot.json` — WoT 2.4.1 native layout resource registration.
- `gui/spottedstatus/styles/` — original eight PNGs already tracked in Git.
- `build.py` — compiles the two Python files using Python 2.7 and packages assets into `.wotmod`.

No SWF or Scaleform renderer is used. The minimap/battle hooks are still imported from legacy-named game Python packages because they supply spotting events, **not** for graphics rendering.

## Known incomplete parts
- **Row positioning:** Gameface JavaScript currently receives vehicleID/state/icon style but DOES NOT map vehicle IDs to actual players-panel row elements. The icons therefore have no correct computed position yet. Do not claim UI feature complete.
- Layout loading and `R.mods.me.inq.spot.InqSpotBattleView` resolution have not been validated inside the official 2.4.1 client.
- The current HTML JS references `../libs/model.js` as in the Weather sample; this library is not bundled and may need a local adapter or alternate ViewModel binding.
- 2.4.1 production release must wait for an actual in-game battle test and game logs.

## Build
On Windows with Python 2.7 installed:
`python build.py --python27 C:\\Python27\\python.exe`

The GitHub Actions workflow builds on a v* tag and marks any release as prerelease. **Do not tag a release as stable yet.**

## WoT package loader fix (2026-10-17)

Previous build used ZIP_DEFLATED. Original WoT 2.4.x .wotmods use ZIP_STORED. The builder now writes uncompressed ZIP entries and checks that meta.xml is the first entry, the archive only has meta.xml/res/* paths, and all entries are stored. This addresses a likely cause of the game's `Mod package ... not loaded` message; it is not a substitute for testing the rebuilt package. Do not reinstall the old 0.3.0-beta.1 build without regenerating it from the updated code.
