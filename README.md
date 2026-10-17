# Spotold — WoT 2.4.1 standalone port

Recovered original OldSkool Spotted Status 1.4.0 behavior and built an independent implementation.

## Implemented in the repository
- Original four status transitions (1 never seen, 2 visible, 3 vanished, 4 dead).
- Exact original icons and label geometry (see `spotold/status.py`, `spotold/config.py`).
- Tests for state changes and geometry.

## Standalone candidate package
A separate candidate WOTMOD was assembled and statically verified in the associated ChatGPT conversation: `Spotold_standalone_2.4.1_candidate.zip`. It includes a standalone `mod_spotold.py`, the original 8 PNG icons and a self-contained copy of the panel injector SWF. It does not import `gui.oldskool` or `modscore`. The standalone runtime source and binary are **not yet checked into this repository**.

## Verification pending
The original panel injector SWF was extracted from the 2.4.0.0 modscore resource package. 2.4.1 actual panel registration and runtime behavior have **not been tested in a game client**. A successful syntax/archive check does not establish in-game compatibility. In particular the new 2.4.1 view registration API may require a change.

Do not publish as a production-ready 2.4.1 release without battle testing and checking `python.log`.
