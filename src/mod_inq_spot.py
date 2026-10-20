# -*- coding: utf-8 -*-
"""INQ SPOT — AS3 battle-panel implementation for WoT 2.4.1."""
import logging
import BigWorld
import constants
from Avatar import PlayerAvatar
from gui.battle_control import avatar_getter
from gui.Scaleform.daapi.view.battle.shared.minimap.plugins import ArenaVehiclesPlugin
from gui.battle_control.controllers.battle_field_ctrl import BattleFieldCtrl
from gui.battle_control.arena_info.settings import VehicleSpottedStatus, INVALIDATE_OP
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore
from account_helpers.settings_core.settings_constants import GRAPHICS
from gui.mods.inq_spot_as3 import g_bridge, initialize as init_panel, finalize as fini_panel

LOG = logging.getLogger('INQ_SPOT')
CONFIG = {'enabled': True, 'style': 1, 'align': 1, 'offsetX': 0,
          'hidePrestige': False}
_originals = []
_initialized = False

class Controller(object):
    def __init__(self):
        self.active = False
        self.arena = None
        self.states = {}
        self.colorblind = False

    def enemy(self, vid):
        player = BigWorld.player()
        arena = getattr(player, 'arena', None)
        if arena is None:
            return False
        info = arena.vehicles.get(vid)
        return info is not None and info.get('team') != player.team

    def special(self):
        arena = avatar_getter.getArena()
        if arena is None:
            return False
        modes = [constants.ARENA_GUI_TYPE.EPIC_BATTLE,
                 constants.ARENA_GUI_TYPE.EVENT_BATTLES]
        halloween = getattr(constants.ARENA_GUI_TYPE, 'HALLOWEEN', None)
        if halloween is not None:
            modes.append(halloween)
        return arena.guiType in modes

    def start(self):
        self.stop()
        if self.special():
            return
        self.active = True
        self.colorblind = bool(dependency.instance(ISettingsCore).getSetting(GRAPHICS.COLOR_BLIND))
        self.arena = avatar_getter.getArena()
        if self.arena:
            self.arena.onVehicleKilled += self.killed
        self.seed()

    def seed(self):
        player = BigWorld.player()
        arena = getattr(player, 'arena', None)
        if arena is None:
            return
        self.states = dict((vid, 1 if info.get('isAlive', True) else 4)
            for vid, info in arena.vehicles.iteritems() if info.get('team') != player.team)
        self.push_all()

    def push_all(self):
        if not self.active:
            return
        g_bridge.send('as_setSettingsS', CONFIG['style'], CONFIG['align'],
                      CONFIG['offsetX'], self.colorblind)
        for vid, state in self.states.iteritems():
            g_bridge.send('as_setStateS', vid, state)
        g_bridge.send('as_setVisibilityS', bool(CONFIG['enabled']))
        g_bridge.send('as_refreshAllS')

    def aoi(self, vid, visible):
        if not self.active or not self.enemy(vid) or self.states.get(vid) in (None, 4):
            return
        state = 2 if visible else 3
        if self.states.get(vid) != state:
            self.states[vid] = state
            g_bridge.send('as_setStateS', vid, state)

    def killed(self, victimID, killerID, equipmentID, reason, numVehiclesAffected):
        if self.active and self.enemy(victimID) and self.states.get(victimID) != 4:
            self.states[victimID] = 4
            g_bridge.send('as_setStateS', victimID, 4)

    def stop(self):
        if self.arena is not None:
            try:
                self.arena.onVehicleKilled -= self.killed
            except Exception:
                LOG.exception('Could not unsubscribe onVehicleKilled')
        self.arena = None
        self.active = False
        self.states = {}
        g_bridge.send('as_clearS')

g_controller = Controller()
g_bridge.onReady = g_controller.push_all

def _patch(obj, name, callback):
    old = getattr(obj, name)
    def wrapper(*args, **kwargs):
        return callback(old, *args, **kwargs)
    setattr(obj, name, wrapper)
    _originals.append((obj, name, old, wrapper))

def _start(old, avatar, *args, **kwargs):
    result = old(avatar, *args, **kwargs)
    try:
        g_controller.start()
    except Exception:
        LOG.exception('start failed')
    return result

def _stop(old, avatar, *args, **kwargs):
    g_controller.stop()
    return old(avatar, *args, **kwargs)

def _aoi(old, obj, entry, in_aoi):
    result = old(obj, entry, in_aoi)
    try:
        if g_controller.active:
            for vid, mm_entry in obj._entries.iteritems():
                if mm_entry == entry:
                    g_controller.aoi(vid, in_aoi)
                    break
    except Exception:
        LOG.exception('AOI callback failed')
    return result

def _spotted(old, obj, vid, status):
    if not g_controller.active:
        return old(obj, vid, status)
    if vid in obj._aliveAllies or vid in obj._BattleFieldCtrl__deadAllies:
        return
    dp = obj._BattleFieldCtrl__battleCtx.getArenaDP()
    flags, vo = dp.updateVehicleSpottedStatus(vid, VehicleSpottedStatus.DEFAULT)
    if flags != INVALIDATE_OP.NONE:
        obj.onSpottedStatusChanged([(flags, vo)], dp)

def init():
    global _initialized
    if _initialized:
        return
    init_panel()
    _patch(PlayerAvatar, '_PlayerAvatar__startGUI', _start)
    _patch(PlayerAvatar, '_PlayerAvatar__destroyGUI', _stop)
    _patch(ArenaVehiclesPlugin, '_setInAoI', _aoi)
    _patch(BattleFieldCtrl, '_BattleFieldCtrl__updateSpottedStatus', _spotted)
    from gui.mods import inq_spot_settings
    inq_spot_settings.install(CONFIG, g_controller.push_all)
    _initialized = True
    LOG.info('INQ SPOT AS3 registration complete')

def fini():
    global _initialized
    if not _initialized:
        return
    g_controller.stop()
    for obj, name, old, wrapped in reversed(_originals):
        if getattr(obj, name) is wrapped:
            setattr(obj, name, old)
    del _originals[:]
    from gui.mods import inq_spot_settings
    inq_spot_settings.uninstall()
    fini_panel()
    _initialized = False

init()
