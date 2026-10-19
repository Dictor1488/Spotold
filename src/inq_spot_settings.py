# -*- coding: utf-8 -*-
"""INQ SPOT: ModsSettingsAPI integration. Style 0 = eye, 1 = circles."""
import logging
LOG = logging.getLogger('INQ_SPOT.settings')
LINKAGE = 'me.inq.spot'

try:
    from gui.modsSettingsApi import g_modsSettingsApi
except ImportError:
    g_modsSettingsApi = None

_installed = False

def _apply(data):
    if not isinstance(data, dict):
        return
    from gui.mods import mod_inq_spot
    config = mod_inq_spot.CONFIG
    if 'enabled' in data:
        config['enabled'] = bool(data['enabled'])
    if 'circles' in data:
        config['style'] = 1 if bool(data['circles']) else 0
    if mod_inq_spot.g_controller.active:
        mod_inq_spot.g_controller.push_all()

def _changed(linkage, values):
    if linkage != LINKAGE:
        return
    try:
        _apply(values)
    except Exception:
        LOG.exception('Failed to apply INQ SPOT settings')

def install():
    global _installed
    if _installed or g_modsSettingsApi is None:
        return
    try:
        from gui.mods import mod_inq_spot
        template = {
            'modDisplayName': u'INQ SPOT',
            'enabled': True,
            'column1': [
                {'type': 'CheckBox', 'text': u'Показувати індикатори засвіту',
                 'value': bool(mod_inq_spot.CONFIG['enabled']), 'varName': 'enabled'},
                {'type': 'CheckBox', 'text': u'Кружки замість ока',
                 'value': mod_inq_spot.CONFIG['style'] == 1, 'varName': 'circles'}
            ],
            'column2': [
                {'type': 'Label', 'text': u'Вимкнено: око (styles/0). Увімкнено: кружки (styles/1).'}
            ]
        }
        saved = g_modsSettingsApi.setModTemplate(LINKAGE, template, _changed)
        _installed = True
        if saved:
            _apply(saved)
        LOG.info('INQ SPOT settings registered')
    except Exception:
        LOG.exception('INQ SPOT ModsSettingsAPI registration failed')

def uninstall():
    global _installed
    _installed = False
