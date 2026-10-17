# -*- coding: utf-8 -*-
from __future__ import division

import json
import logging
import os

import BigWorld
import GUI
import ResMgr

from frameworks.wulf import PositionAnchor, ViewFlags, ViewModel, ViewSettings, WindowFlags, WindowLayer
from gui.battle_control.arena_info import vos_collections
from gui.battle_control.arena_info.settings import VehicleSpottedStatus
from gui.battle_control.controllers import battle_field_ctrl
from gui.battle_control.controllers.battle_field_ctrl import IBattleFieldListener
from gui.Scaleform.daapi.view.battle.shared.minimap.plugins import ArenaVehiclesPlugin
from gui.impl.pub import ViewImpl, WindowImpl
from helpers import dependency
from skeletons.gui.battle_session import IBattleSessionProvider

try:
    from gui.impl.gen import R
    _GAMEFACE_OK = True
except Exception:
    R = None
    _GAMEFACE_OK = False

_LOG = logging.getLogger('[me_inq_spotted]')
RES_MAP_ITEM_ID = 'mods/dictor/spot/SpottedPanel/layoutID'
CONFIG_PATH = os.path.join('mods', 'configs', 'me_inq_spotted', 'config.json')

STATE_NEVER = 0
STATE_SPOTTED = 1
STATE_NOT_SPOTTED = 2
STATE_KILLED = 3
STATE_NAMES = ('neverSpotted', 'spotted', 'notSpotted', 'killed')
ORIGINAL_PANEL_TOP = 60

DEFAULT_CONFIG = {
    'enabled': True,
    'removeBaseIndicator': True,
    'style': 1,
    'colorblind': False,
    'debug': False,
    'position': {
        'y': 3,
        'rightByMode': {'0': 38, '1': 46, '2': 91, '3': 116, '4': 231},
        'rowHeight': 25,
        'width': 20,
        'height': 380,
    },
}


def _load_json(path):
    try:
        section = ResMgr.openSection(path)
        if section is not None and section.asString:
            value = json.loads(section.asString)
            return value if isinstance(value, dict) else {}
    except Exception:
        pass
    return {}


def _load_config():
    loaded = _load_json(CONFIG_PATH)
    config = dict(DEFAULT_CONFIG)
    config['position'] = dict(DEFAULT_CONFIG['position'])
    config['position']['rightByMode'] = dict(DEFAULT_CONFIG['position']['rightByMode'])
    if isinstance(loaded, dict):
        for key in ('enabled', 'removeBaseIndicator', 'debug', 'style', 'colorblind'):
            if key in loaded:
                config[key] = loaded[key]
        position = loaded.get('position')
        if isinstance(position, dict):
            for key in ('y', 'rowHeight', 'width', 'height'):
                if key in position:
                    config['position'][key] = position[key]
            if isinstance(position.get('rightByMode'), dict):
                config['position']['rightByMode'].update(position['rightByMode'])
    return config


def _screen_size():
    try:
        return GUI.screenResolution()
    except Exception:
        return (1920, 1080)


def _vehicle_id(value):
    try:
        return int(getattr(value, 'vehicleID', value))
    except Exception:
        return None


def _status_to_state(status, previous):
    if status == VehicleSpottedStatus.SPOTTED:
        return STATE_SPOTTED
    if status == VehicleSpottedStatus.UNSPOTTED:
        return STATE_NOT_SPOTTED
    if status == VehicleSpottedStatus.DEFAULT and previous == STATE_NEVER:
        return STATE_NEVER
    return previous


class SpottedModel(ViewModel):
    def __init__(self):
        self._payload = '{}'
        super(SpottedModel, self).__init__(properties=1, commands=1)

    def _initialize(self):
        super(SpottedModel, self)._initialize()
        self._addStringProperty('payload', self._payload)
        self.onReady = self._addCommand('onReady')

    def setPayload(self, value):
        self._setString(0, value)


class SpottedView(ViewImpl):
    viewLayoutID = R.mods.dictor.spot.SpottedPanel if _GAMEFACE_OK else None

    def __init__(self):
        self._model = SpottedModel()
        settings = ViewSettings(SpottedView.viewLayoutID(), flags=ViewFlags.VIEW, model=self._model)
        super(SpottedView, self).__init__(settings)
        self._last_payload = None

    def _getEvents(self):
        return ((self._model.onReady, self._on_ready),)

    def _on_ready(self, *args):
        _runtime.view = self
        _runtime.push()
        _runtime.apply_position()

    def push(self, payload):
        raw = json.dumps(payload, separators=(',', ':'))
        if raw == self._last_payload:
            return
        try:
            with self._model.transaction() as model:
                model.setPayload(raw)
            self._last_payload = raw
        except Exception:
            _LOG.exception('GameFace payload update failed')

    def _finalize(self):
        if _runtime.view is self:
            _runtime.view = None
        super(SpottedView, self)._finalize()


class SpottedWindow(WindowImpl):
    def __init__(self, parent):
        super(SpottedWindow, self).__init__(
            WindowFlags.WINDOW,
            content=SpottedView(),
            parent=parent,
            layer=WindowLayer.WINDOW,
            name='me_inq_spotted',
        )

    def _onReady(self):
        try:
            self.show(focus=False)
        except Exception:
            pass
        _runtime.apply_position()


class Runtime(object):
    guiSessionProvider = dependency.descriptor(IBattleSessionProvider)

    def __init__(self):
        self.config = _load_config()
        self.window = None
        self.view = None
        self.feedback = None
        self.battle_field = None
        self.states = {}
        self.enemy_order = []
        self.ui_order = []
        self.mode = 1
        self._attached = False
        self._using_native_spotted = False
        self._load_retry = None

    def debug(self, message, *args):
        if self.config.get('debug', False):
            try:
                _LOG.info(message, *args)
            except Exception:
                pass

    def _main_window(self):
        try:
            from skeletons.gui.impl import IGuiLoader
            return dependency.instance(IGuiLoader).windowsManager.getMainWindow()
        except Exception:
            return None

    def load(self):
        self._load_retry = None
        if self.window is not None or not _GAMEFACE_OK:
            return
        parent = self._main_window()
        if parent is None:
            self._load_retry = BigWorld.callback(0.1, self.load)
            return
        try:
            self.window = SpottedWindow(parent)
            self.window.load()
            self.view = self.window.content
            self.seed()
            self.attach()
            self.push()
            self.apply_position()
            _LOG.info('SPOT panel loaded; enemies=%d nativeSpotted=%s', len(self.enemy_order), self._using_native_spotted)
        except Exception:
            self.window = None
            self.view = None
            _LOG.exception('Failed to load SPOT panel')

    def destroy(self):
        if self._load_retry is not None:
            try:
                BigWorld.cancelCallback(self._load_retry)
            except Exception:
                pass
            self._load_retry = None
        self.detach()
        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:
                pass
        self.window = None
        self.view = None
        self.states = {}
        self.enemy_order = []
        self.ui_order = []

    def _native_enemy_order(self, arena_dp):
        try:
            collection = vos_collections.EnemyItemsCollection(sortKey=vos_collections.VehicleInfoSortKey)
            return [int(vehicle_id) for vehicle_id in collection.ids(arena_dp)]
        except Exception:
            return []

    def _read_state(self, arena_dp, vehicle_id, previous=STATE_NEVER):
        try:
            info = arena_dp.getVehicleInfo(vehicle_id)
            if info.isObserver() or not arena_dp.isEnemyTeam(info.team):
                return None
            if not info.isAlive():
                return STATE_KILLED
            stats = arena_dp.getVehicleStats(vehicle_id)
            return _status_to_state(getattr(stats, 'spottedStatus', VehicleSpottedStatus.DEFAULT), previous)
        except Exception:
            return None

    def seed(self):
        self.states = {}
        try:
            arena_dp = self.guiSessionProvider.getArenaDP()
            for info in arena_dp.getVehiclesInfoIterator():
                try:
                    if info.isObserver() or not arena_dp.isEnemyTeam(info.team):
                        continue
                    vehicle_id = int(info.vehicleID)
                    state = self._read_state(arena_dp, vehicle_id, STATE_NEVER)
                    if state is not None:
                        self.states[vehicle_id] = state
                except Exception:
                    pass

            order = [v for v in self.ui_order if v in self.states]
            if not order:
                order = [v for v in self._native_enemy_order(arena_dp) if v in self.states]
            if not order:
                order = list(self.states.keys())
            self.enemy_order = order
        except Exception:
            _LOG.exception('Failed to seed spotted states')

    def sync_order_from_ui(self, data):
        if not isinstance(data, dict):
            return
        raw = data.get('rightItemsIDs')
        if raw is None:
            return
        order = []
        try:
            for value in raw:
                vehicle_id = _vehicle_id(value)
                if vehicle_id is not None and vehicle_id not in order:
                    order.append(vehicle_id)
        except Exception:
            return
        if not order:
            return

        self.ui_order = order
        if self.states:
            try:
                arena_dp = self.guiSessionProvider.getArenaDP()
                for vehicle_id in order:
                    if vehicle_id not in self.states:
                        state = self._read_state(arena_dp, vehicle_id, STATE_NEVER)
                        if state is not None:
                            self.states[vehicle_id] = state
                    elif self.states.get(vehicle_id) != STATE_KILLED:
                        state = self._read_state(arena_dp, vehicle_id, self.states[vehicle_id])
                        if state is not None:
                            self.states[vehicle_id] = state
            except Exception:
                pass
            actual = [v for v in order if v in self.states]
            if actual:
                self.enemy_order = actual
                self.push()
        self.debug('rightItemsIDs=%s', order)

    def refresh_order(self):
        if self.ui_order:
            actual = [v for v in self.ui_order if v in self.states]
            if actual and actual != self.enemy_order:
                self.enemy_order = actual
                self.push()
            return
        try:
            arena_dp = self.guiSessionProvider.getArenaDP()
            order = [v for v in self._native_enemy_order(arena_dp) if v in self.states]
            if order and order != self.enemy_order:
                self.enemy_order = order
                self.push()
        except Exception:
            pass

    def attach(self):
        if self._attached:
            return
        attached = False
        self._using_native_spotted = False
        try:
            dynamic = getattr(self.guiSessionProvider, 'dynamic', None)
            self.battle_field = getattr(dynamic, 'battleField', None) if dynamic is not None else None
            if self.battle_field is not None and hasattr(self.battle_field, 'onSpottedStatusChanged'):
                self.battle_field.onSpottedStatusChanged += self._on_spotted_status_changed
                self._using_native_spotted = True
                attached = True
        except Exception:
            self.battle_field = None
            self._using_native_spotted = False

        if not self._using_native_spotted:
            try:
                self.feedback = self.guiSessionProvider.shared.feedback
                if self.feedback is not None:
                    if hasattr(self.feedback, 'onMinimapVehicleAdded'):
                        self.feedback.onMinimapVehicleAdded += self._on_added
                        attached = True
                    if hasattr(self.feedback, 'onMinimapVehicleRemoved'):
                        self.feedback.onMinimapVehicleRemoved += self._on_removed
                        attached = True
            except Exception:
                self.feedback = None
        else:
            self.feedback = None
        self._attached = attached

    def detach(self):
        if self.battle_field is not None and self._using_native_spotted:
            try:
                self.battle_field.onSpottedStatusChanged -= self._on_spotted_status_changed
            except Exception:
                pass
        self.battle_field = None
        if self.feedback is not None:
            try:
                self.feedback.onMinimapVehicleAdded -= self._on_added
            except Exception:
                pass
            try:
                self.feedback.onMinimapVehicleRemoved -= self._on_removed
            except Exception:
                pass
        self.feedback = None
        self._using_native_spotted = False
        self._attached = False

    def _is_enemy(self, vehicle_id):
        try:
            return int(vehicle_id) in self.states
        except Exception:
            return False

    def _set_state(self, vehicle_id, state):
        try:
            vehicle_id = int(vehicle_id)
        except Exception:
            return False
        if vehicle_id not in self.states or self.states.get(vehicle_id) == STATE_KILLED:
            return False
        if self.states.get(vehicle_id) == state:
            return False
        self.states[vehicle_id] = state
        self.debug('vehicle=%d state=%s', vehicle_id, STATE_NAMES[state])
        return True

    def _on_spotted_status_changed(self, updated, arena_dp):
        changed = False
        try:
            for entry in updated:
                vo = entry[1] if isinstance(entry, (tuple, list)) and len(entry) > 1 else entry
                vehicle_id = _vehicle_id(vo)
                if vehicle_id not in self.states or self.states.get(vehicle_id) == STATE_KILLED:
                    continue
                state = self._read_state(arena_dp, vehicle_id, self.states[vehicle_id])
                if state is not None and self._set_state(vehicle_id, state):
                    changed = True
        except Exception:
            _LOG.exception('Spotted-status event processing failed')
        if changed:
            self.push()

    def _on_added(self, vehicle_proxy, vehicle_info, gui_props):
        try:
            if self._set_state(vehicle_info.vehicleID, STATE_SPOTTED):
                self.push()
        except Exception:
            pass

    def _on_removed(self, vehicle_id):
        try:
            if self._set_state(vehicle_id, STATE_NOT_SPOTTED):
                self.push()
        except Exception:
            pass

    def mark_dead(self, dead_enemies):
        changed = False
        try:
            for value in dead_enemies:
                vehicle_id = _vehicle_id(value)
                if vehicle_id in self.states and self.states.get(vehicle_id) != STATE_KILLED:
                    self.states[vehicle_id] = STATE_KILLED
                    changed = True
        except Exception:
            _LOG.exception('Dead-vehicle processing failed')
        if changed:
            self.push()

    def set_mode(self, mode):
        try:
            self.mode = int(mode)
        except Exception:
            return
        self.apply_position()
        self.refresh_order()

    def apply_position(self):
        if self.window is None:
            return
        position = self.config.get('position', {})
        right = position.get('rightByMode', {}).get(str(self.mode), 38)
        screen_w, _ = _screen_size()
        x = max(0, int(screen_w) - int(right) - int(position.get('width', 20)))
        y = ORIGINAL_PANEL_TOP + int(position.get('y', 3))
        try:
            self.window.move(x, y, xAnchor=PositionAnchor.LEFT, yAnchor=PositionAnchor.TOP)
        except Exception:
            try:
                self.window.move(x, y)
            except Exception:
                pass

    def push(self):
        if self.view is None:
            return
        rows = [STATE_NAMES[self.states.get(vehicle_id, STATE_NEVER)] for vehicle_id in self.enemy_order]
        self.view.push({'visible': bool(self.config.get('enabled', True)), 'rows': rows, 'mode': int(self.mode), 'style': int(self.config.get('style', 1)), 'colorblind': bool(self.config.get('colorblind', False))})


_runtime = Runtime()
_listener = None
_orig_set_components = None
_orig_set_in_aoi = None
_orig_stop_control = None
_orig_stats_get = None
_panel_hooks = []
_stats_ui_hooks = []
_installed = False


class SpottedBattleListener(IBattleFieldListener):
    def __init__(self):
        _runtime.load()

    def updateVehicleHealth(self, vehicleID, newHealth, maxHealth):
        if newHealth <= 0 and _runtime._is_enemy(vehicleID):
            _runtime.mark_dead((vehicleID,))

    def updateTeamHealth(self, alliesHP, enemiesHP, totalAlliesHP, totalEnemiesHP):
        _runtime.load()

    def updateDeadVehicles(self, aliveAllies, deadAllies, aliveEnemies, deadEnemies):
        _runtime.mark_dead(deadEnemies)


def _get_listener():
    global _listener
    if _listener is None:
        _listener = SpottedBattleListener()
    return _listener


def _patched_set_components(self, *components):
    listener = _get_listener()
    if listener not in components:
        components = components + (listener,)
    return _orig_set_components(self, *components)


def _patched_stop_control(self):
    global _listener
    try:
        _runtime.destroy()
        _listener = None
    except Exception:
        _LOG.exception('Battle cleanup failed')
    return _orig_stop_control(self)


def _hook_panel_modes():
    try:
        from gui.Scaleform.daapi.view.battle.classic.players_panel import PlayersPanel
        for name in ('setInitialMode', 'setLargeMode', 'tryToSetPanelModeByMouse', '_handleNextMode'):
            old = getattr(PlayersPanel, name, None)
            if old is None:
                continue

            def make_wrapper(old_fn):
                def wrapper(self, *args, **kwargs):
                    result = old_fn(self, *args, **kwargs)
                    try:
                        mode = getattr(self, '_mode', 1)
                        BigWorld.callback(0.0, lambda: _runtime.set_mode(mode))
                    except Exception:
                        pass
                    return result
                return wrapper

            new = make_wrapper(old)
            setattr(PlayersPanel, name, new)
            _panel_hooks.append((PlayersPanel, name, old, new))
    except Exception:
        _LOG.exception('Players-panel mode hooks unavailable')


def _restore_panel_hooks():
    for cls, name, old, new in _panel_hooks:
        try:
            if getattr(cls, name, None) is new:
                setattr(cls, name, old)
        except Exception:
            pass
    del _panel_hooks[:]


def _hook_stats_ui_order():
    try:
        from gui.Scaleform.daapi.view.meta.BattleStatisticDataControllerMeta import BattleStatisticDataControllerMeta
        names = ('as_setVehiclesDataS', 'as_addVehiclesInfoS', 'as_updateVehiclesInfoS',
                 'as_updateVehicleStatusS', 'as_setFragsS', 'as_updateVehiclesStatsS')
        for name in names:
            old = getattr(BattleStatisticDataControllerMeta, name, None)
            if old is None:
                continue

            def make_wrapper(old_fn):
                def wrapper(self, data, *args, **kwargs):
                    try:
                        _runtime.sync_order_from_ui(data)
                    except Exception:
                        pass
                    return old_fn(self, data, *args, **kwargs)
                return wrapper

            new = make_wrapper(old)
            setattr(BattleStatisticDataControllerMeta, name, new)
            _stats_ui_hooks.append((BattleStatisticDataControllerMeta, name, old, new))
        _LOG.info('Players-panel rightItemsIDs hooks installed')
    except Exception:
        _LOG.exception('Failed to hook players-panel sort IDs')


def _restore_stats_ui_order():
    for cls, name, old, new in _stats_ui_hooks:
        try:
            if getattr(cls, name, None) is new:
                setattr(cls, name, old)
        except Exception:
            pass
    del _stats_ui_hooks[:]


def _hook_base_spotted_indicator():
    global _orig_stats_get
    if not _runtime.config.get('removeBaseIndicator', True):
        return
    try:
        from gui.Scaleform.daapi.view.battle.classic.stats_exchange import DynamicVehicleStatsComponent
        _orig_stats_get = DynamicVehicleStatsComponent.get

        def hidden_spotted_get(self, forced=False):
            data = _orig_stats_get(self, forced)
            if isinstance(data, dict) and 'spottedStatus' in data:
                data['spottedStatus'] = VehicleSpottedStatus.DEFAULT
            return data

        DynamicVehicleStatsComponent.get = hidden_spotted_get
        hidden_spotted_get._me_inq_spotted = True
        _LOG.info('Base WG spotted indicator suppressed in UI exchange')
    except Exception:
        _orig_stats_get = None
        _LOG.exception('Failed to suppress base WG spotted indicator')


def _restore_base_spotted_indicator():
    global _orig_stats_get
    if _orig_stats_get is None:
        return
    try:
        from gui.Scaleform.daapi.view.battle.classic.stats_exchange import DynamicVehicleStatsComponent
        current = getattr(DynamicVehicleStatsComponent, 'get', None)
        if getattr(current, '_me_inq_spotted', False):
            DynamicVehicleStatsComponent.get = _orig_stats_get
    except Exception:
        pass
    _orig_stats_get = None



def _patched_set_in_aoi(self, entry, is_in_aoi):
    result = _orig_set_in_aoi(self, entry, is_in_aoi)
    try:
        if _runtime.window is not None:
            for vehicle_id, mm_entry in self._entries.iteritems():
                if mm_entry == entry:
                    next_state = STATE_SPOTTED if is_in_aoi else STATE_NOT_SPOTTED
                    if _runtime._set_state(vehicle_id, next_state):
                        _runtime.push()
                    break
    except Exception:
        _LOG.exception('AOI update failed')
    return result

def initialize():
    global _orig_set_components, _orig_stop_control, _orig_set_in_aoi, _installed
    if _installed:
        return
    _orig_set_in_aoi = ArenaVehiclesPlugin._setInAoI
    ArenaVehiclesPlugin._setInAoI = _patched_set_in_aoi
    _orig_set_components = battle_field_ctrl.BattleFieldCtrl.setViewComponents
    _orig_stop_control = battle_field_ctrl.BattleFieldCtrl.stopControl
    battle_field_ctrl.BattleFieldCtrl.setViewComponents = _patched_set_components
    battle_field_ctrl.BattleFieldCtrl.stopControl = _patched_stop_control
    _hook_panel_modes()
    _hook_stats_ui_order()
    _hook_base_spotted_indicator()
    _installed = True
    _LOG.info('INQ SPOT merged: Gameface adapter + original AOI spotting hooks; Gameface=%s', _GAMEFACE_OK)


def finalize():
    global _installed, _listener
    if not _installed:
        return
    try:
        _runtime.destroy()
    except Exception:
        pass
    if _orig_set_in_aoi is not None and ArenaVehiclesPlugin._setInAoI is _patched_set_in_aoi:
        ArenaVehiclesPlugin._setInAoI = _orig_set_in_aoi
    _restore_base_spotted_indicator()
    _restore_stats_ui_order()
    _restore_panel_hooks()
    try:
        if battle_field_ctrl.BattleFieldCtrl.setViewComponents is _patched_set_components:
            battle_field_ctrl.BattleFieldCtrl.setViewComponents = _orig_set_components
        if battle_field_ctrl.BattleFieldCtrl.stopControl is _patched_stop_control:
            battle_field_ctrl.BattleFieldCtrl.stopControl = _orig_stop_control
    except Exception:
        pass
    _listener = None
    _installed = False
    _LOG.info('me_inq_spotted finalized')


def init():
    initialize()


def fini():
    finalize()
