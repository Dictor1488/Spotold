# -*- coding: utf-8 -*-
"""Independent spotting state model. Requires visibility events from game adapter."""
NEVER_SEEN = 0
VISIBLE = 1
LOST = 2

class SpotStatus(object):
    def __init__(self):
        self._states = {}

    def reset(self, vehicle_ids):
        self._states = dict((int(vid), NEVER_SEEN) for vid in vehicle_ids)

    def update(self, vehicle_id, is_visible):
        vid = int(vehicle_id)
        if vid not in self._states:
            return None
        before = self._states[vid]
        if is_visible:
            after = VISIBLE
        elif before == VISIBLE:
            after = LOST
        else:
            after = before
        self._states[vid] = after
        return after if after != before else None

    def destroy(self, vehicle_id):
        self._states.pop(int(vehicle_id), None)

    def get(self, vehicle_id):
        return self._states.get(int(vehicle_id))

    def snapshot(self):
        return self._states.copy()
