# -*- coding: utf-8 -*-

import BigWorld
import logging

_LOG = logging.getLogger('[me_inq_spotted_panelmode]')
_orig_set_panel_mode = None
_installed = False


def _get_runtime():
    try:
        from gui.mods import mod_inq_spot
        return getattr(mod_me_inq_spotted, '_runtime', None)
    except Exception:
        return None


def _apply_mode(mode):
    runtime = _get_runtime()
    if runtime is None:
        return
    try:
        runtime.set_mode(int(mode))
    except Exception:
        _LOG.exception('Failed to sync SPOT with players-panel mode')


def _install():
    global _orig_set_panel_mode, _installed
    if _installed:
        return
    try:
        from gui.Scaleform.daapi.view.meta.PlayersPanelMeta import PlayersPanelMeta
        _orig_set_panel_mode = PlayersPanelMeta.as_setPanelModeS

        def _patched_set_panel_mode(self, value):
            result = _orig_set_panel_mode(self, value)
            try:
                # This is the final DAAPI call used by WoT for every classic
                # players-panel mode change, so it is the authoritative mode.
                BigWorld.callback(0.0, lambda: _apply_mode(value))
            except Exception:
                _apply_mode(value)
            return result

        PlayersPanelMeta.as_setPanelModeS = _patched_set_panel_mode
        _patched_set_panel_mode._me_inq_spotted_panelmode = True
        _installed = True
        _LOG.info('Players-panel exact mode hook installed')
    except Exception:
        _LOG.exception('Failed to install players-panel exact mode hook')


def _restore():
    global _orig_set_panel_mode, _installed
    if not _installed or _orig_set_panel_mode is None:
        return
    try:
        from gui.Scaleform.daapi.view.meta.PlayersPanelMeta import PlayersPanelMeta
        current = getattr(PlayersPanelMeta, 'as_setPanelModeS', None)
        if getattr(current, '_me_inq_spotted_panelmode', False):
            PlayersPanelMeta.as_setPanelModeS = _orig_set_panel_mode
    except Exception:
        pass
    _orig_set_panel_mode = None
    _installed = False


def init():
    _install()


def fini():
    _restore()
