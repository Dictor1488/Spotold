# INQ SPOT — AS3 player-panel beta for World of Tanks 2.4.1

This branch replaces the standalone Gameface overlay with an embedded **ActionScript 3 / Scaleform** component based on the working player-row resolution in `Dictor1488/HpE`. It uses **no OldSkool Python core** and preserves the enemy spotting state transitions from the recovered `mod_spottedStatus.py`.

## Files

- `src/mod_inq_spot.py`: spotting hooks, initial enemy state, killed vehicle handling and reset
- `src/inq_spot_as3.py`: standalone DAAPI bridge and battle-view registration following HpE
- `as3/src_flash/src/InqSpotPanel.as`: AS3 injector
- `as3/src_flash/src/com/dictor/spot/battle/SpotPanel.as`: positions each icon under its **actual player-panel row**, using `getHolderByVehicleID(vehicleID)`
- `as3/src_flash/src/com/dictor/hpe/injector/`: component registration classes reused from HpE
- `gui/spottedstatus/styles/`: eight original PNG indicators
- `build.py`: Python 2.7 compilation and stored-format WOTMOD packaging
- `.github/workflows/release.yml`: HPE-based Flex AS3 compilation and release automation. The workflow retrieves compiler SWCs from public HpE repo.

## Display behavior

Each icon follows the player-panel row rather than using a fixed 25-pixel grid. Python sends state 1 (never detected), 2 (detected), 3 (missing), 4 (dead). The ActionScript control uses PNGs missing/detected/undetected respectively and hides dead vehicles. Enemy-only rows are targeted.

## Test status

**Untested in the game client.** The changes are committed as a beta source port. CI needs to compile `inqSpotPanel.swf` using Adobe Flex and the HpE SWCs, then create `INQ_SPOT_<version>.wotmod`. After installing the built package in `mods/2.4.1.0/`, test panel modes and replay spotting transitions and provide `python.log` / `game.log` if necessary.

**Architecture tradeoff:** AS3 graphics necessarily use the game's Scaleform runtime. This does not depend on the original OldSkool modsCore, but it is not Gameface.
