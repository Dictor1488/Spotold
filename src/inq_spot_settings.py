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
    if 'enabled' in data:
        _config['enabled'] = bool(data['enabled'])
    # A single radio choice is always mutually exclusive.
    if 'styleChoice' in data:
        try:
            _config['style'] = 0 if int(data['styleChoice']) == 0 else 1
        except (TypeError, ValueError):
            LOG.warning('Invalid INQ SPOT styleChoice: %r', data['styleChoice'])
    if _refresh is not None:
        _refresh()


def _callback(linkage, values):
    if linkage != LINKAGE:
        return
    try:
        _apply(values)
    except Exception:
        LOG.exception('Failed to apply INQ SPOT settings')


def _template():
    from gui.modsSettingsApi import templates
    # Use the public helper from the actual installed ModsSettingsAPI instead
    # of guessing serialized component type strings.
    radio = templates.createRadioButtonGroup(
        u'Indicator style', 'styleChoice',
        templates.generateOptions([u'Eye', u'Dot']),
        0 if int(_config.get('style', 1)) == 0 else 1,
        tooltip=u'{HEADER}Indicator style{/HEADER}{BODY}Eye or Dot.{/BODY}'
    )
    return {
        'modDisplayName': u'INQ SPOT',
        # Do not pin settingsVersion: the menu must migrate template changes.
        'enabled': True,
        'column1': [
            templates.createCheckbox(
                u'Показувати індикатори засвіту', 'enabled',
                bool(_config.get('enabled', True)),
                tooltip=u'{HEADER}Індикатори{/HEADER}{BODY}Показувати значки засвіту.{/BODY}'
            ),
            radio
        ],
        'column2': []
    }


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
