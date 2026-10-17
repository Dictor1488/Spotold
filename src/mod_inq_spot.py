# -*- coding: utf-8 -*-
"""INQ SPOT — standalone beta for WoT 2.4.1."""
import logging
import BigWorld
import constants
from Avatar import PlayerAvatar
from gui.battle_control import avatar_getter
from gui.Scaleform.daapi.view.battle.shared.minimap.plugins import ArenaVehiclesPlugin
from gui.Scaleform.daapi.view.battle.shared.stats_exchange.vehicle import VehicleInfoComponent
from gui.battle_control.controllers.battle_field_ctrl import BattleFieldCtrl
from gui.battle_control.arena_info.settings import VehicleSpottedStatus, INVALIDATE_OP
from helpers import dependency
from skeletons.account_helpers.settings_core import ISettingsCore
from account_helpers.settings_core.settings_constants import GRAPHICS
from gui.mods.inq_spot_gameface import create_overlay, update_overlay, close_overlay

LOG = logging.getLogger('INQ_SPOT')
LOG.setLevel(logging.DEBUG)
LOG.warning('[DIAG] module imported; Gameface diagnostic build')
CONFIG = {'enabled': True, 'style': 1, 'align': 1, 'offsetX': 0, 'hidePrestige': False}
STATES = (None, 'missing', 'detected', 'undetected', '')
_PANEL = None
_registered = False
_originals = []

def _safe(fn, *args):
    try:
        return fn(*args)
    except Exception:
        LOG.exception('INQ SPOT operation failed')
        return None

def _icon(state, colorblind):
    if state == 4:
        return ''
    name = 'colorblind' if state == 3 and colorblind else STATES[state]
    return '<img src="img://gui/spottedstatus/styles/%s/%s.png" width="19" height="19">' % (CONFIG['style'], name)

def _geometry():
    x = -109 if CONFIG['align'] == 0 else (4 if CONFIG['hidePrestige'] else 22)
    try:
        x += max(-150, min(150, int(CONFIG.get('offsetX', 0))))
    except (TypeError, ValueError):
        pass
    cell = {'width': 24, 'height': 24, 'x': x, 'y': 0}
    return {'isHtml': True, 'left': dict(cell), 'right': dict(cell)}

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
        kinds = constants.ARENA_GUI_TYPE
        modes = [kinds.EPIC_BATTLE, kinds.EVENT_BATTLES]
        halloween = getattr(kinds, 'HALLOWEEN', None)
        if halloween is not None:
            modes.append(halloween)
        return arena.guiType in modes

    def start(self):
        LOG.warning('[DIAG] battle start; current_active=%s', self.active)
        self.stop()
        if not CONFIG['enabled'] or self.special():
            return
        self.active = True
        LOG.warning('[DIAG] battle eligible, preparing arena and Gameface')
        self.colorblind = bool(dependency.instance(ISettingsCore).getSetting(GRAPHICS.COLOR_BLIND))
        self.arena = avatar_getter.getArena()
        if self.arena:
            self.arena.onVehicleKilled += self.killed
        self.ui_ready()

    def stop(self):
        self.active = False
        if self.arena is not None:
            try:
                self.arena.onVehicleKilled -= self.killed
            except Exception:
                LOG.exception('Failed to unsubscribe')
            self.arena = None
        LOG.warning('[DIAG] stop battle; cached=%s', len(self.states))
        self.states.clear()
        _safe(close_overlay)

    def ui_ready(self):
        if not self.active:
            return
        player = BigWorld.player()
        arena = getattr(player, 'arena', None)
        if arena is None:
            return
        self.states.clear()
        for vid, info in arena.vehicles.iteritems():
            if info.get('team') != player.team:
                self.states[vid] = 1 if info.get('isAlive', True) else 4
        LOG.warning('[DIAG] arena roster initialized: enemies=%d', len(self.states))
        result = _safe(create_overlay, _geometry())
        LOG.warning('[DIAG] create_overlay result=%r', result)
        for vid in self.states:
            self.render(vid)

    def render(self, vid):
        if not self.active or not self.enemy(vid):
            return
        state = self.states.get(vid)
        if state is not None:
            LOG.debug('[DIAG] render vehicleID=%s state=%s', vid, state)
            _safe(update_overlay, vid, state, CONFIG['style'], self.colorblind)

    def aoi(self, vid, visible):
        if not self.active or not self.enemy(vid) or self.states.get(vid) in (None, 4):
            return
        state = 2 if visible else 3
        if self.states.get(vid) != state:
            LOG.warning('[DIAG] AOI vehicleID=%s spotted=%s state=%s->%s', vid, visible, self.states.get(vid), state)
            self.states[vid] = state
            self.render(vid)

    def killed(self, victimID, killerID, equipmentID, reason, numVehiclesAffected):
        if self.active and self.enemy(victimID) and self.states.get(victimID) != 4:
            LOG.warning('[DIAG] destroyed vehicleID=%s', victimID)
            self.states[victimID] = 4
            self.render(victimID)

_controller = Controller()

def _patch(obj, name, handler):
    base = getattr(obj, name)
    def wrapped(*args, **kwargs):
        return handler(base, *args, **kwargs)
    setattr(obj, name, wrapped)
    LOG.warning('[DIAG] hook installed %s.%s', getattr(obj, '__name__', str(obj)), name)
    _originals.append((obj, name, base, wrapped))

def _start(base, avatar, *args, **kwargs):
    result = base(avatar, *args, **kwargs)
    _safe(_controller.start)
    return result

def _destroy(base, avatar, *args, **kwargs):
    _safe(_controller.stop)
    return base(avatar, *args, **kwargs)

def _aoi(base, obj, entry, isInAoI):
    result = base(obj, entry, isInAoI)
    if _controller.active:
        for vid, mm_entry in obj._entries.iteritems():
            if mm_entry == entry:
                _safe(_controller.aoi, vid, isInAoI)
                break
    return result

def _battle_spotted(base, obj, vehicleID, vehicleSpottedStatus):
    if not _controller.active:
        return base(obj, vehicleID, vehicleSpottedStatus)
    if vehicleID in obj._aliveAllies or vehicleID in obj._BattleFieldCtrl__deadAllies:
        return
    ctx = obj._BattleFieldCtrl__battleCtx
    dp = ctx.getArenaDP()
    flags, vo = dp.updateVehicleSpottedStatus(vehicleID, VehicleSpottedStatus.DEFAULT)
    if flags != INVALIDATE_OP.NONE:
        obj.onSpottedStatusChanged([(flags, vo)], dp)

def _vehicle_info(base, obj, info, overrides):
    result = base(obj, info, overrides)
    if CONFIG['hidePrestige'] and _controller.active:
        for key in ('prestigeLevel', 'prestigeMarkId'):
            if key in obj._data:
                obj._data[key] = 0
    return result

def init():
    global _registered
    if _registered:
        return
    _patch(PlayerAvatar, '_PlayerAvatar__startGUI', _start)
    _patch(PlayerAvatar, '_PlayerAvatar__destroyGUI', _destroy)
    _patch(ArenaVehiclesPlugin, '_setInAoI', _aoi)
    _patch(BattleFieldCtrl, '_BattleFieldCtrl__updateSpottedStatus', _battle_spotted)
    _patch(VehicleInfoComponent, 'addVehicleInfo', _vehicle_info)
    _registered = True
    LOG.warning('[DIAG] all game hooks registered')
    LOG.info('INQ SPOT Gameface controller initialized')

def fini():
    global _registered
    if not _registered:
        return
    _safe(_controller.stop)
    for obj, name, original, wrapped in reversed(_originals):
        if getattr(obj, name, None) is wrapped:
            setattr(obj, name, original)
    del _originals[:]
    _registered = False

init()
