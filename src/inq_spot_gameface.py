# -*- coding: utf-8 -*-
"""INQ SPOT native Gameface overlay. Requires registered layout resource in WoT 2.4.1."""
import json
import logging
LOG = logging.getLogger('INQ_SPOT.gameface')
LOG.setLevel(logging.DEBUG)
LOG.warning('[DIAG] Gameface module imported')
_window = None
_view = None
_pending = {}
_geometry = {}

from frameworks.wulf import ViewModel, ViewSettings, ViewFlags, WindowFlags, WindowLayer
from gui.impl.pub import ViewImpl, WindowImpl

# Native 2.4.1 resources are generated through gui/gen_resources / R.mods.
# Fail gracefully when the layout has not been registered.
def _layout_id():
    try:
        from gui.impl.gen import R
        result = R.mods.me.inq.spot.InqSpotBattleView()
        LOG.warning('[DIAG] layout resolved id=%r', result)
        return result
    except Exception:
        LOG.exception('INQ SPOT Gameface layout is not registered')
        return None

class SpotModel(ViewModel):
    def __init__(self):
        super(SpotModel, self).__init__(properties=1, commands=0)

    def _initialize(self):
        super(SpotModel, self)._initialize()
        self._addStringProperty('payload', '{}')

    def setPayload(self, value):
        self._setString(0, value)

class SpotView(ViewImpl):
    def __init__(self, layout):
        super(SpotView, self).__init__(
            ViewSettings(layoutID=layout, flags=ViewFlags.VIEW, model=SpotModel()))

    @property
    def viewModel(self):
        return super(SpotView, self).getViewModel()

    def _onLoading(self, *args, **kwargs):
        super(SpotView, self)._onLoading(*args, **kwargs)
        LOG.warning('[DIAG] SpotView _onLoading')
        _refresh()

class SpotWindow(WindowImpl):
    def __init__(self, view):
        super(SpotWindow, self).__init__(
            WindowFlags.WINDOW | WindowFlags.WINDOW_FULLSCREEN,
            content=view, layer=WindowLayer.WINDOW)

    def _onReady(self):
        LOG.warning('[DIAG] SpotWindow _onReady')
        self.show(focus=False)
        _refresh()

def _refresh():
    if _view is None:
        return
    try:
        data = {'geometry': _geometry, 'vehicles': _pending}
        LOG.debug('[DIAG] ViewModel refresh vehicles=%d bytes=%d', len(_pending), len(json.dumps(data)))
        with _view.viewModel.transaction() as vm:
            vm.setPayload(json.dumps(data, separators=(',', ':')))
    except Exception:
        LOG.exception('Gameface payload refresh failed')

def create_overlay(geometry):
    global _window, _view, _geometry
    LOG.warning('[DIAG] create_overlay geometry=%r', geometry)
    _geometry = dict(geometry)
    if _window is None:
        layout = _layout_id()
        if layout is None:
            LOG.error('[DIAG] no layout ID, Gameface window cannot open')
            return False
        try:
            _view = SpotView(layout)
            _window = SpotWindow(_view)
            _window.load()
            LOG.warning('[DIAG] window.load() returned')
        except Exception:
            LOG.exception('Could not load INQ SPOT Gameface overlay')
            _window = None
            _view = None
            return False
    _refresh()
    return True

def update_overlay(vehicle_id, state, style, colorblind):
    if state not in (1, 2, 3, 4):
        return
    LOG.debug('[DIAG] update_overlay id=%s state=%s', vehicle_id, state)
    _pending[str(vehicle_id)] = {'state': state, 'style': style, 'colorblind': bool(colorblind)}
    _refresh()

def close_overlay():
    global _window, _view, _geometry
    LOG.warning('[DIAG] close_overlay pending=%d', len(_pending))
    old = _window
    _window = None
    _view = None
    _geometry = {}
    _pending.clear()
    if old is not None:
        try:
            old.destroy()
        except Exception:
            LOG.exception('Gameface teardown failed')
