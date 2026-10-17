# -*- coding: utf-8 -*-
"""INQ SPOT AS3 panel bridge based on HpE's verified registration pattern."""
import logging
import Event
from frameworks.wulf import WindowLayer
from gui.Scaleform.framework import ComponentSettings, ScopeTemplates, ViewSettings
from gui.Scaleform.framework.entities.BaseDAAPIComponent import BaseDAAPIComponent
from gui.Scaleform.framework.entities.View import View
from gui.Scaleform.framework.managers.loaders import SFViewLoadParams
from gui.Scaleform.genConsts.BATTLE_VIEW_ALIASES import BATTLE_VIEW_ALIASES
from gui.shared import EVENT_BUS_SCOPE, events, g_eventBus
from gui.shared.personality import ServicesLocator
from helpers import dependency
from skeletons.gui.impl import IGuiLoader

LOG = logging.getLogger('INQ_SPOT.as3')
ALIAS = 'inq_spot_player_panel_view'
COMPONENT = 'inqSpotPanel'
SWF = 'inqSpotPanel.swf'

class SpotMeta(BaseDAAPIComponent):
    def _populate(self):
        super(SpotMeta, self)._populate()
        g_bridge.component = self
        g_bridge.requested = True
        LOG.info('INQ SPOT AS3 component populated')
        if g_bridge.onReady is not None:
            g_bridge.onReady()

    def _dispose(self):
        if g_bridge.component is self:
            g_bridge.component = None
        g_bridge.requested = False
        super(SpotMeta, self)._dispose()

    def flashLogS(self, *values):
        LOG.warning('Flash: %r', values)

    def as_setStateS(self, vehicleID, state):
        if self._isDAAPIInited():
            self.flashObject.as_setState(int(vehicleID), int(state))

    def as_setSettingsS(self, style, align, offset, colorblind):
        if self._isDAAPIInited():
            self.flashObject.as_setSettings(int(style), int(align), int(offset), bool(colorblind))

    def as_setVisibilityS(self, visible):
        if self._isDAAPIInited():
            self.flashObject.as_setVisibility(bool(visible))

    def as_refreshAllS(self):
        if self._isDAAPIInited():
            self.flashObject.as_refreshAll()

    def as_clearS(self):
        if self._isDAAPIInited():
            self.flashObject.as_clear()

class Bridge(object):
    def __init__(self):
        self.component = None
        self.requested = False
        self.onReady = None
        self.registered = False

    def onComponentRegistered(self, event):
        if getattr(event, 'alias', None) != BATTLE_VIEW_ALIASES.PLAYERS_PANEL:
            return
        if self.requested:
            return
        app = ServicesLocator.appLoader.getDefBattleApp()
        if app is None:
            return
        try:
            self.requested = True
            app.loadView(SFViewLoadParams(ALIAS, ALIAS), {})
            LOG.info('INQ SPOT AS3 view requested')
        except Exception:
            self.requested = False
            LOG.exception('Cannot load INQ SPOT AS3 view')

    def send(self, name, *args):
        if self.component is None:
            return False
        try:
            getattr(self.component, name)(*args)
            return True
        except Exception:
            LOG.exception('Flash bridge call failed: %s', name)
            return False

g_bridge = Bridge()

def initialize():
    factory = dependency.instance(IGuiLoader).entitiesFactory
    if factory.getSettings(ALIAS) is None:
        factory.addSettings(ViewSettings(ALIAS, View, SWF,
            WindowLayer.WINDOW, None, ScopeTemplates.GLOBAL_SCOPE))
    if factory.getSettings(COMPONENT) is None:
        factory.addSettings(ComponentSettings(COMPONENT, SpotMeta,
            ScopeTemplates.DEFAULT_SCOPE))
    if not g_bridge.registered:
        g_eventBus.addListener(events.ComponentEvent.COMPONENT_REGISTERED,
            g_bridge.onComponentRegistered, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_bridge.registered = True
    LOG.info('INQ SPOT AS3 bridge initialized')

def finalize():
    if g_bridge.registered:
        g_eventBus.removeListener(events.ComponentEvent.COMPONENT_REGISTERED,
            g_bridge.onComponentRegistered, scope=EVENT_BUS_SCOPE.GLOBAL)
        g_bridge.registered = False
    g_bridge.component = None
    g_bridge.requested = False
