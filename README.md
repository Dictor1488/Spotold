# INQ SPOT

Enemy spotting indicators for World of Tanks 2.4.1, rendered with ActionScript 3 / Scaleform.

Indicators are attached to the enemy player-panel row by `vehicleID`. The mod has three selectable styles: **Eye**, **Dot**, and **SPOT lamps** (original graphics from the SPOT Gameface mod).

## Indicator states

- `missing`: enemy not yet spotted
- `detected`: enemy currently spotted
- `undetected`: enemy previously spotted, currently hidden
- `colorblind`: alternate hidden-state image when colorblind mode is enabled
- Destroyed enemy: indicator hidden

The first two styles use PNGs in `gui/spottedstatus/styles/{0,1}/`. The third style is generated at package time from `lamp_assets.py` into `gui/spottedstatus/styles/2/`.

## Settings

Aslain's menu / Izeberg ModsSettingsAPI supports an enabled checkbox and the style choices **Eye (0)**, **Dot (1)**, **SPOT lamps (2)**. The default is Dot. The choice updates during a battle.

## Source and build

- `src/mod_inq_spot.py`: battle events and spotting-state controller (Python 2.7)
- `src/inq_spot_as3.py`: Scaleform bridge (Python 2.7)
- `src/inq_spot_settings.py`: optional menu integration (Python 2.7)
- `as3/src_flash/src/`: AS3 panel, row attachment, and injector
- `as3/libs/`: AS3 compilation dependencies
- `gui/spottedstatus/styles/`: Eye and Dot images
- `lamp_assets.py`: original SPOT lamp images encoded for build packaging
- `build.py` / `build.json`: create the .wotmod
- `.github/workflows/release.yml`: Windows/Flex build and GitHub release

Build locally after compiling `as3/bin/inqSpotPanel.swf`:

```sh
python build.py --python27 /path/to/python2.7
```

Or run **Actions → Build and Release INQ SPOT AS3** with a version number.

In-game alignment and the newly added lamps need a fresh battle test. Previous log checks do not verify the third style.
