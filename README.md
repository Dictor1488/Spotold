# INQ SPOT

Independent enemy spotting status mod targeting **World of Tanks 2.4.1.0**.

**Current state: beta source port. Not an in-game-verified stable release.**

## Repository

- `src/mod_inq_spot.py`: standalone battle event hooks and candidate panel renderer bridge (no OldSkool Python imports)
- `build.json`: ID `me.inq.spot`, display name `INQ SPOT`, version `0.3.0-beta.1`
- `build.py`: compile Python **2.7** bytecode, generate distributable `.wotmod`
- `.github/workflows/release.yml`: CI artifacts, tag-driven **prerelease** uploads

## Resources

All eight PNG indicators are already committed in `gui/spottedstatus/styles/{0,1}/`. The legacy SWF panel injector is not yet present in GitHub; `build.py` expects `assets/flash/playersPanelAPI_modsCore.swf`. Download `INQ_SPOT_source_0.3.0-beta.1.zip` from the originating ChatGPT conversation for the complete local build project. CI still requires the missing SWF file before building a complete .wotmod.

## Build from complete source archive

`python build.py --python27 C:\\Python27\\python.exe`

Build output: `dist/INQ_SPOT_0.3.0-beta.1.wotmod`. Install in `mods/2.4.1.0/`.

## Release policy

Create a `v0.3.0-beta.1` tag **only after** the SWF is in GitHub and the 2.4.1 GUI lifecycle is validated. The workflow automatically publishes a GitHub prerelease from that tag.

**Known risk:** the bundled renderer uses a legacy SWF. A successful archive/syntax test does not prove it will initialize correctly in the 2.4.1 client. Verify in battle using `python.log`.
