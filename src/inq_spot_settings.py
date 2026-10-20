# -*- coding: utf-8 -*-
"""Optional ModsSettingsAPI bridge for INQ SPOT (Python 2.7).

Works with Aslain's Gameface menu (preferred) and Izeberg's original API.
AS3 is initialized independently and receives updated values on UI ready.
"""
import logging

LOG = logging.getLogger('INQ_SPOT.settings')
LINKAGE = 'me.inq.spot'
_registered = False
_api = None
_config = {'enabled': True, 'style': 1}
_refresh = None

def _find_api():
    # Aslain's Gameface menu implements the Izeberg template vocabulary.
    try:
        from gui.aslainMenu import g_modsSettingsApi
        if g_modsSettingsApi is not None:
            return g_modsSettingsApi
    except ImportError:
        pass
    try:
        from gui.modsSettingsApi import g_modsSettingsApi
        return g_modsSettingsApi
    except ImportError:
        return None

_syncing = False

def _apply(data):
    if not isinstance(data, dict):
        return
    if 'enabled' in data:
        _config['enabled'] = bool(data['enabled'])
    old_style = int(_config.get('style', 1))
    has_eye = 'styleEye' in data
    has_circles = 'styleCircles' in data
    if has_eye or has_circles:
        eye = bool(data.get('styleEye', old_style == 0))
        circles = bool(data.get('styleCircles', old_style == 1))
        # Prefer the newly checked option when both values arrive.
        if eye != circles:
            _config['style'] = 0 if eye else 1
        elif eye and circles:
            _config['style'] = 0 if old_style == 1 else 1
        else:
            _config['style'] = old_style
    elif 'styleChoice' in data:
        try:
            _config['style'] = 0 if int(data['styleChoice']) == 0 else 1
        except (TypeError, ValueError):
            pass
    if _refresh is not None:
        _refresh()


def _callback(linkage, values):
    global _syncing
    if linkage != LINKAGE and linkage != (LINKAGE,):
        return
    if _syncing:
        return
    try:
        _apply(values)
        if _api is not None and ('styleEye' in values or 'styleCircles' in values):
            _syncing = True
            try:
                _api.updateModSettings(LINKAGE, newSettings={
                    'styleEye': _config['style'] == 0,
                    'styleCircles': _config['style'] == 1
                })
            finally:
                _syncing = False
    except Exception:
        LOG.exception('Failed to apply INQ SPOT settings')


def _template():
    config = _config
    result = {
        'modDisplayName': u'INQ SPOT',
        'settingsVersion': 1,
        'enabled': True,
        'column1': [
            {
                'type': 'CheckBox',
                'text': u'Показувати індикатори засвіту',
                'tooltip': u'{HEADER}Індикатори{/HEADER}{BODY}Увімкнути або приховати значки засвіту.{/BODY}',
                'value': bool(config.get('enabled', True)),
                'varName': 'enabled'
            },
            {
                'type': 'CheckBox',
                'text': u'Eye',
                'tooltip': u'{HEADER}Eye{/HEADER}{BODY}<img src="img://gui/spottedstatus/styles/0/detected.png" width="48" height="48"/> Значки у вигляді ока.{/BODY}',
                'tooltipIcon': 'img://gui/spottedstatus/styles/0/detected.png',
                'value': int(config.get('style', 1)) == 0,
                'varName': 'styleEye'
            },
            {
                'type': 'CheckBox',
                'text': u'Dot',
                'tooltip': u'{HEADER}Dot{/HEADER}{BODY}<img src="img://gui/spottedstatus/styles/1/detected.png" width="48" height="48"/> Круглі індикатори.{/BODY}',
                'tooltipIcon': 'img://gui/spottedstatus/styles/1/detected.png',
                'value': int(config.get('style', 1)) == 1,
                'varName': 'styleCircles'
            }
        ],
        'column2': []
    }
    return result

def install(config=None, refresh=None):
    global _registered, _api, _config, _refresh
    if config is not None:
        _config = config
    if refresh is not None:
        _refresh = refresh
    if _registered:
        return
    api = _find_api()
    if api is None:
        LOG.info('ModsSettingsAPI not installed, using default INQ SPOT settings')
        return
    try:
        # The same setModTemplate signature is implemented by both Izeberg
        # and Aslain. It registers the callback and returns stored settings.
        saved = api.setModTemplate(LINKAGE, _template(), _callback)
        _api = api
        _registered = True
        _apply(saved)
        LOG.info('INQ SPOT template registered in ModsSettingsAPI')
    except Exception:
        LOG.exception('INQ SPOT ModsSettingsAPI registration failed')

def uninstall():
    # The API owns the registered menu template; it has no universal removal
    # method. Guard against duplicate registration within one client session.
    return
