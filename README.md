# INQ SPOT 1.0.0

Standalone enemy spotting indicators for **World of Tanks 2.4.1**, using ActionScript 3 / Scaleform. Indicators attach to the actual enemy row through `getHolderByVehicleID(vehicleID)`, as in HpE. No OldSkool core is required.

## Spotting indicators

- `missing.png`: never spotted
- `detected.png`: currently visible
- `undetected.png`: previously spotted, now lost (or `colorblind.png` when colorblind mode is on)
- Destroyed enemies: icon hidden.

Eight original PNGs are retained in `gui/spottedstatus/styles/0` and `1`.

## Source structure

- `src/mod_inq_spot.py` — battle hooks and spotting state controller (Python 2.7)
- `src/inq_spot_as3.py` — DAAPI/AS3 communication and registration (Python 2.7)
- `as3/src_flash/src/InqSpotPanel.as` — injector
- `as3/src_flash/src/com/dictor/spot/battle/SpotPanel.as` — AS3 row attachment and icon presentation
- `as3/src_flash/src/com/dictor/hpe/injector/` — battle injection primitives adapted from HpE
- `as3/libs/` — required local SWC libraries
- `build.py` — packages compiled SWF, Python bytecode and PNGs as uncompressed `.wotmod`
- `.github/workflows/release.yml` — Windows/Flex CI and GitHub Release publishing

## Mod settings

When Aslain's menu or Izeberg's ModsSettingsAPI is installed, INQ SPOT appears in the mods settings screen with:
- **Показувати індикатори засвіту** — enable/disable icons;
- **Вигляд індикаторів** — dropdown: Око (style 0) or Кружки (style 1).

When Aslain's Gameface Mod Menu is installed, the settings panel also shows the original PNG previews for both styles (never spotted, spotted, lost) side by side, using its supported image controls. Older ModsSettingsAPI variants retain the text-only style chooser.\n\nThe selected style is saved through ModsSettingsAPI and applied to existing indicators during battle. Without ModsSettingsAPI, the default remains circles (style 1).

## Release

Manually run **Actions → Build and Release INQ SPOT AS3**, choose version `1.0.0`. Flex SWF compilation is mandatory for each build; Python 2.7 is required. The workflow publishes `dist/INQ_SPOT_1.0.0.wotmod` to Releases.

## Verification

The latest provided game log confirmed the 0.4.0-beta.1 WOTMOD loaded, the AS3 bridge and view initialized, 15 enemy states were sent, and spotting transitions arrived without INQ SPOT errors. This supports releasing a clean version, although rendering alignment in all player-panel modes has not been independently confirmed. For in-game problems, send `game.log`.
