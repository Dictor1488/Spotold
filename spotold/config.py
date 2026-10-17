# -*- coding: utf-8 -*-
"""Standalone settings for the original two indicator styles."""
DEFAULTS = {
    'enabled': True,
    'indicatorStyle': 0,
    'align': 'left',
    'offsetX': 0,
    'colorblind': False,
    'hidePrestige': False,
}

def normalize(values):
    result = DEFAULTS.copy()
    if not isinstance(values, dict):
        return result
    result['enabled'] = bool(values.get('enabled', result['enabled']))
    result['indicatorStyle'] = 1 if values.get('indicatorStyle') == 1 else 0
    result['align'] = 'right' if values.get('align') == 'right' else 'left'
    try:
        result['offsetX'] = max(-250, min(250, int(values.get('offsetX', 0))))
    except (TypeError, ValueError):
        pass
    result['colorblind'] = bool(values.get('colorblind', False))
    result['hidePrestige'] = bool(values.get('hidePrestige', False))
    return result

def icon_name(state, colorblind=False):
    from .status import NEVER_SEEN, VISIBLE, LOST
    if state == NEVER_SEEN:
        return 'undetected.png'
    if state == VISIBLE:
        return 'colorblind.png' if colorblind else 'detected.png'
    if state == LOST:
        return 'missing.png'
    return None
