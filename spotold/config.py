# -*- coding: utf-8 -*-
"""Settings and exact visual mapping reconstructed from recovered source."""
DEFAULTS = {'enabled': True, 'style': 1, 'align': 1,
            'hidePrestige': False, 'offsetX': 0}

def normalize(values):
    result = DEFAULTS.copy()
    if not isinstance(values, dict):
        return result
    result['enabled'] = bool(values.get('enabled', True))
    result['style'] = 0 if values.get('style', 1) == 0 else 1
    result['align'] = 0 if values.get('align', 1) == 0 else 1
    result['hidePrestige'] = bool(values.get('hidePrestige', False))
    try:
        result['offsetX'] = max(-150, min(150, int(values.get('offsetX', 0))))
    except (TypeError, ValueError):
        pass
    return result

def geometry(settings):
    settings = normalize(settings)
    x = -109 if settings['align'] == 0 else (4 if settings['hidePrestige'] else 22)
    return {'width': 24, 'height': 24, 'x': x + settings['offsetX'], 'y': 0}

def icon_name(state, colorblind=False):
    from .status import NOT_DETECTED, DETECTED, MISSING, DEAD
    if state == NOT_DETECTED:
        return 'missing'
    if state == DETECTED:
        return 'detected'
    if state == MISSING:
        return 'colorblind' if colorblind else 'undetected'
    if state == DEAD:
        return ''
    return None

def icon_html(state, settings=None, colorblind=False):
    name = icon_name(state, colorblind)
    if not name:
        return ''
    return '<img src="img://gui/spottedstatus/styles/%s/%s.png" width="19" height="19">' % (normalize(settings)['style'], name)
