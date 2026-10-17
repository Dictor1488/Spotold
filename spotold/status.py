# -*- coding: utf-8 -*-
"""Original OldSkool 1.4.0 spotting state transitions; no core dependency."""
NOT_DETECTED = 1
DETECTED = 2
MISSING = 3
DEAD = 4

class SpotStatus(object):
    def __init__(self):
        self._states = {}

    def reset(self, enemy_vehicles):
        if hasattr(enemy_vehicles, 'items'):
            self._states = dict((int(vid), NOT_DETECTED if alive else DEAD)
                                for vid, alive in enemy_vehicles.items())
        else:
            self._states = dict((int(vid), NOT_DETECTED) for vid in enemy_vehicles)

    def update(self, vehicle_id, is_in_aoi):
        vid = int(vehicle_id)
        before = self._states.get(vid)
        if before is None or before == DEAD:
            return None
        after = DETECTED if is_in_aoi else MISSING
        if before == after:
            return None
        self._states[vid] = after
        return after

    def kill(self, vehicle_id):
        vid = int(vehicle_id)
        if self._states.get(vid) == DEAD:
            return None
        self._states[vid] = DEAD
        return DEAD

    def get(self, vehicle_id):
        return self._states.get(int(vehicle_id))

    def snapshot(self):
        return self._states.copy()
