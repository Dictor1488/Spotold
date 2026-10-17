# -*- coding: utf-8 -*-

import logging

_LOG = logging.getLogger('[me_inq_spotted_visibility]')
_orig_toggle_full_stats = None
_installed = False


def _get_runtime():
    try:
        from gui.mods import mod_inq_spot
        return getattr(mod_me_inq_spotted, '_runtime', None)
    except Exception:
        return None


def _set_spot_visible(visible):
    runtime = _get_runtime()
    if runtime is None or runtime.window is None:
        return
    try:
        if visible:
            runtime.window.show(focus=False)
            runtime.apply_position()
            runtime.push()
        else:
            runtime.window.hide()
    except Exception:
        _LOG.exception('Failed to change SPOT visibility')


def _install():
    global _orig_toggle_full_stats, _installed
    if _installed:
        return
    try:
        from gui.Scaleform.daapi.view.battle.classic.page import ClassicPage
        _orig_toggle_full_stats = ClassicPage._toggleFullStats

        def _patched_toggle_full_stats(self, isShown, permanent=None, tabAlias=None):
            # Hide our separate GameFace overlay before WoT opens the full
            # battle statistics/team-roster screen, and restore it only after
            # that screen is closed. ClassicPage itself hides the stock HUD
            # through this exact method, so we follow the same lifecycle.
            if isShown:
                _set_spot_visible(False)
            result = _orig_toggle_full_stats(self, isShown, permanent, tabAlias)
            if not isShown:
                _set_spot_visible(True)
            return result

        ClassicPage._toggleFullStats = _patched_toggle_full_stats
        _patched_toggle_full_stats._me_inq_spotted_visibility = True
        _installed = True
        _LOG.info('Full-stats visibility hook installed')
    except Exception:
        _LOG.exception('Failed to install full-stats visibility hook')


def _restore():
    global _orig_toggle_full_stats, _installed
    if not _installed or _orig_toggle_full_stats is None:
        return
    try:
        from gui.Scaleform.daapi.view.battle.classic.page import ClassicPage
        current = getattr(ClassicPage, '_toggleFullStats', None)
        if getattr(current, '_me_inq_spotted_visibility', False):
            ClassicPage._toggleFullStats = _orig_toggle_full_stats
    except Exception:
        pass
    _orig_toggle_full_stats = None
    _installed = False


def init():
    _install()


def fini():
    _restore()
