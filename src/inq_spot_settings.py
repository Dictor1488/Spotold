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

def _apply(data):
    if not isinstance(data, dict):
        return
    config = _config
    if 'enabled' in data:
        config['enabled'] = bool(data['enabled'])
    if 'circles' in data:
        config['style'] = 1 if bool(data['circles']) else 0
    # A battle can be running when the user applies settings in the garage
    # overlay or opens the menu mid-replay. The bridge ignores calls until
    # its AS3 component becomes ready, then onReady sends current config.
    if _refresh is not None:
        _refresh()

def _on_changed(linkage, values):
    if linkage != LINKAGE and linkage != (LINKAGE,):
        return
    try:
        _apply(values)
    except Exception:
        LOG.exception('Failed to apply INQ SPOT settings')

def _preview_images():
    """Build native Aslain image controls; never send them to legacy MSA."""
    try:
        from gui.aslainMenu import templates
        create_image = getattr(templates, 'createImage', None)
        if not callable(create_image):
            return None
        result = [[], []]
        for style in (0, 1):
            for file_name, label in (
                    ('missing', u'Не засвічений'),
                    ('detected', u'У засвіті'),
                    ('undetected', u'Зник із засвіту')):
                source = 'coui://gui/spottedstatus/styles/%d/%s.png' % (
                    style, file_name)
                result[style].append(create_image(
                    source, 28, 28, label=label, align='left'))
        return result
    except Exception:
        LOG.exception('Could not build AS3 icon previews for Mod Menu')
        return None


def _template():
    from gui.mods import mod_inq_spot
    config = mod_inq_spot.CONFIG
    previews = _preview_images()
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
                'type': 'Dropdown',
                'text': u'Вигляд індикаторів',
                'tooltip': u'{HEADER}Вигляд{/HEADER}{BODY}Око або кружки. Зміни застосовуються одразу.{/BODY}',
                'options': [{'label': u'Око'}, {'label': u'Кружки'}],
                'value': 1 if config.get('style', 1) == 1 else 0,
                'varName': 'styleChoice',
                'width': 220
            }
        ],
        'column2': []
    }
    if previews is not None:
        result['column1'].append({'type': 'Label', 'text': u'Око — приклади'})
        result['column1'].extend(previews[0])
        result['column2'].append({'type': 'Label', 'text': u'Кружки — приклади'})
        result['column2'].extend(previews[1])
    return result

def _normalize_and_apply(values):
    if not isinstance(values, dict):
        return
    data = dict(values)
    if 'styleChoice' in data:
        try:
            data['circles'] = int(data['styleChoice']) == 1
        except (TypeError, ValueError):
            data['circles'] = False
    _apply(data)

def _callback(linkage, values):
    if linkage != LINKAGE and linkage != (LINKAGE,):
        return
    try:
        _normalize_and_apply(values)
    except Exception:
        LOG.exception('Failed to apply INQ SPOT settings callback')

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
        _normalize_and_apply(saved)
        LOG.info('INQ SPOT template registered in ModsSettingsAPI')
    except Exception:
        LOG.exception('INQ SPOT ModsSettingsAPI registration failed')

def uninstall():
    # The API owns the registered menu template; it has no universal removal
    # method. Guard against duplicate registration within one client session.
    return
