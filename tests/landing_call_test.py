#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-EC Wire Test - the Profile Function: a landing call written over BACnet is served.

    python3 tests/landing_call_test.py [--exe build/BACnetExampleBEC] [--port 47833]

ANSI/ASHRAE 135-2024 L.13.2: "A B-EC device performs elevator control. It supports limited
modification of its elevator objects by another device." Cl. 12.58.10 Landing_Call_Control:
"A write to this property is equivalent to a passenger pressing a call button at a landing,
indicating either desired direction of travel or destination floor." Cl. 12.58.9
Landing_Calls: "Each element of this list shall represent a currently active call for the
group of lifts."

The Peer is a Python client playing a landing-call panel. It writes Landing_Call_Control
(a raw BACnetLandingCallStatus - wiretest.services.landing_call_status) and watches the car over BACnet: a
SubscribeCOVPropertyMultiple on the car, ReadPropertyMultiple snapshots, and reads of
Landing_Calls / Assigned_Landing_Calls / Registered_Car_Call. Nothing reaches into the
example except the Simulation's speed (the test-only control channel).

  1. Control: the car stands at floor 1, STOPPED, door CLOSED; no landing call is active;
     Landing_Call_Control reads floor 0, direction NONE; the car stays put.
  2. Someone at floor 6 presses DOWN: the write is accepted; Landing_Call_Control reads back
     6 / DOWN; Landing_Calls and the car's Assigned_Landing_Calls list 6 / DOWN.
  3. The car is sent: the COV subscriber hears Car_Position 2, 3, 4, 5, 6, one floor at a
     time, and the door SAFETY_LOCKED -> OPENING -> OPENED; every RPM snapshot of the moving
     car has the door SAFETY_LOCKED; the trip takes at least five floor-travel times.
  4. The call clears when - and only when - the car is at 6: Landing_Calls and
     Assigned_Landing_Calls go empty, and every read that still listed the call was taken
     before the car stood at 6.
  5. A destination call: someone at floor 3 asks for floor 8. The car goes down to 3, the
     landing call clears, Registered_Car_Call lists 8 (the passenger is in the car), and the
     car carries on up to 8, where the car call clears.
"""
import sys
import time

import ec_setup as setup  # first: it puts the vendored wiretest/ on sys.path
from ec_setup import (DIRECTION_DOWN, DIRECTION_STOPPED, DIRECTION_UP, DOOR_CLOSED, DOOR_OPENED, DOOR_OPENING,
                      DOOR_SAFETY_LOCKED, LIFT, acked)
from wiretest.services import LIFT_CAR_DIRECTION_NONE as DIRECTION_NONE
import wiretest
from wiretest import record

COV_PROCESS_IDENTIFIER = 11


class Subscriber:
    """The panel's COV subscription on the car, and the changes it has heard, in order."""

    def __init__(self):
        self.client = setup.client()

    def subscribe(self, port):
        return self.client.request(lambda invoke_id: wiretest.services.subscribe_cov_property_multiple_request(
            invoke_id, COV_PROCESS_IDENTIFIER, False, 600, [(*LIFT, list(setup.CAR_PROPERTIES))]), port)

    def listen(self, seconds):
        """The (property, value) changes every notification since the last listen() carried."""
        self.client.frames = []
        self.client.collect(seconds)
        changes = []
        for frame in self.client.frames:
            if frame.ok and wiretest.services.is_cov_notification_multiple(frame):
                for monitored, property_identifier, _, octets in wiretest.services.CovNotificationMultiple(frame).values:
                    if monitored == LIFT:
                        changes.append((property_identifier, wiretest.decode_application(octets)))
        return changes

    def close(self):
        self.client.close()


def values(changes, property_identifier):
    collapsed = []
    for identifier, value in changes:
        if identifier == property_identifier and (not collapsed or collapsed[-1] != value):
            collapsed.append(value)
    return collapsed


def follow_call(panel, args, floor, seconds):
    """Poll the car and Landing_Calls until the call at `floor` has cleared; returns
    (snapshots of the moving car, the car snapshot taken just BEFORE each read that still
    listed the call, the car snapshot when it was first seen cleared)."""
    moving, listed_while, cleared_at = [], [], None
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        snapshot = setup.car_snapshot(panel, args.port)
        calls = setup.landing_calls(panel, args.port)
        if snapshot is not None and snapshot[1] != DIRECTION_STOPPED:
            moving.append(snapshot)
        if isinstance(calls, list) and any(call["floor"] == floor for call in calls):
            listed_while.append(snapshot)
        elif isinstance(calls, list):
            cleared_at = setup.car_snapshot(panel, args.port)
            break
        time.sleep(0.05)
    return moving, listed_while, cleared_at


def main():
    args = setup.parser(__doc__).parse_args()
    example = setup.start_controller(args)
    panel = setup.client()        # retries a lost request, visibly
    subscriber = Subscriber()
    hands = None
    try:
        hands = setup.control(args)

        # --- 1. Control ---------------------------------------------------------------------
        first = setup.car_snapshot(panel, args.port)
        record("Control: the car stands at floor 1, STOPPED, door CLOSED", first == (1, DIRECTION_STOPPED, DOOR_CLOSED),
               f"read (position, direction, door) {first}")
        record("Control: no landing call is active (Landing_Calls empty)", setup.landing_calls(panel, args.port) == [])
        control_value = setup.landing_call_control(panel, args.port)
        record("Control: Landing_Call_Control reads floor 0, direction NONE (no call written yet)",
               control_value == {"floor": 0, "direction": DIRECTION_NONE}, f"read {control_value}")
        answer = subscriber.subscribe(args.port)
        record("SubscribeCOVPropertyMultiple on the car is accepted", acked(answer), answer.describe())
        time.sleep(4 * setup.TRAVEL_MS / 1000)
        heard = subscriber.listen(0.2)
        record("Control: with no call the car stays at floor 1 (COV: only the subscription's first notification)",
               values(heard, setup.PROPERTY_CAR_POSITION) == [1] and
               setup.car_snapshot(panel, args.port) == first, f"heard {heard}")

        # --- 2. A call at floor 6, DOWN ----------------------------------------------------------
        pressed = time.monotonic()
        answer = setup.write_landing_call(panel, args.port, 6, direction=DIRECTION_DOWN)
        record("WriteProperty Landing_Call_Control = floor 6, DOWN is accepted", acked(answer), answer.describe())
        control_value = setup.landing_call_control(panel, args.port)
        record("Landing_Call_Control reads back floor 6, DOWN", control_value == {"floor": 6, "direction": DIRECTION_DOWN},
               f"read {control_value}")
        calls = setup.landing_calls(panel, args.port)
        assigned = setup.assigned_landing_calls(panel, args.port)
        record("The call is active: Landing_Calls lists floor 6, DOWN",
               calls == [{"floor": 6, "direction": DIRECTION_DOWN}], f"read {calls}")
        record("... and assigned to the car: Mauve's Assigned_Landing_Calls lists floor 6, DOWN",
               assigned == [{"floor": 6, "direction": DIRECTION_DOWN}], f"read {assigned}")

        # --- 3 and 4. The car goes; the call clears at 6 ------------------------------------------
        moving, listed_while, cleared_at = follow_call(panel, args, 6, 3 * 5 * setup.TRAVEL_MS / 1000 + 5)
        took = time.monotonic() - pressed
        record("The call cleared with the car at floor 6, STOPPED, door opening or open",
               cleared_at is not None and cleared_at[:2] == (6, DIRECTION_STOPPED) and
               cleared_at[2] in (DOOR_OPENING, DOOR_OPENED), f"car when Landing_Calls emptied: {cleared_at}")
        record("While the call was listed the car was never yet standing at 6",
               bool(listed_while) and all(snapshot is None or snapshot[:2] != (6, DIRECTION_STOPPED)
                                          for snapshot in listed_while),
               f"{len(listed_while)} read(s) listed it; last car snapshot then {listed_while[-1] if listed_while else None}")
        record("Every RPM snapshot of the moving car is UP with the door SAFETY_LOCKED",
               bool(moving) and all(snapshot[1] == DIRECTION_UP and snapshot[2] == DOOR_SAFETY_LOCKED for snapshot in moving),
               f"{len(moving)} moving snapshot(s): {sorted(set(moving))}")
        record(f"The trip took at least 5 floor-travel times ({5 * setup.TRAVEL_MS} ms) - the car's set speed",
               took >= 5 * setup.TRAVEL_MS / 1000, f"took {took * 1000:.0f} ms")
        record("Assigned_Landing_Calls is empty again", setup.assigned_landing_calls(panel, args.port) == [])
        heard = subscriber.listen(0.3)
        record("COV: Car_Position 2, 3, 4, 5, 6 - one floor at a time",
               values(heard, setup.PROPERTY_CAR_POSITION) == [2, 3, 4, 5, 6],
               f"heard {values(heard, setup.PROPERTY_CAR_POSITION)}")
        record("COV: the door SAFETY_LOCKED for the trip, then OPENING -> OPENED at 6",
               values(heard, setup.PROPERTY_CAR_DOOR_STATUS)[:3] == [DOOR_SAFETY_LOCKED, DOOR_OPENING, DOOR_OPENED],
               f"heard {values(heard, setup.PROPERTY_CAR_DOOR_STATUS)}")

        # --- 5. A destination call: from 3 to 8 ---------------------------------------------------------
        answer = setup.write_landing_call(panel, args.port, 3, destination=8)
        record("WriteProperty Landing_Call_Control = floor 3, destination 8 is accepted", acked(answer), answer.describe())
        calls = setup.landing_calls(panel, args.port)
        record("Landing_Calls lists floor 3, destination 8", calls == [{"floor": 3, "destination": 8}], f"read {calls}")
        assigned = setup.assigned_landing_calls(panel, args.port)
        record("Assigned_Landing_Calls lists floor 3 with the direction the passenger will travel, UP",
               assigned == [{"floor": 3, "direction": DIRECTION_UP}], f"read {assigned}")
        moving, listed_while, cleared_at = follow_call(panel, args, 3, 3 * 3 * setup.TRAVEL_MS / 1000 + 6)
        record("The car went DOWN to 3 (door SAFETY_LOCKED on the way) and the landing call cleared there",
               cleared_at is not None and cleared_at[0] == 3 and bool(moving) and
               all(snapshot[1] == DIRECTION_DOWN and snapshot[2] == DOOR_SAFETY_LOCKED for snapshot in moving),
               f"cleared with the car at {cleared_at}; moving {sorted(set(moving))}")
        car_calls = setup.registered_car_calls(panel, args.port)
        record("The passenger is in the car: Registered_Car_Call lists 8", car_calls == [8], f"read {car_calls}")
        arrived = wiretest.wait_until(lambda: (setup.car_snapshot(panel, args.port) or (None, None))[:2] == (
            8, DIRECTION_STOPPED), 3 * 5 * setup.TRAVEL_MS / 1000 + 5, 0.1)
        record("The car carries on to floor 8 and stops", arrived, f"read {setup.car_snapshot(panel, args.port)}")
        record("At 8 the car call is cleared", setup.registered_car_calls(panel, args.port) == [],
               f"read {setup.registered_car_calls(panel, args.port)}")
        heard = subscriber.listen(0.3)
        record("COV: Car_Position 5, 4, 3 down, then 4 ... 8 up",
               values(heard, setup.PROPERTY_CAR_POSITION) == [5, 4, 3, 4, 5, 6, 7, 8],
               f"heard {values(heard, setup.PROPERTY_CAR_POSITION)}")
    finally:
        if hands is not None:
            hands.close()
        panel.close()
        subscriber.close()
        example.stop()
        if not all(wiretest.results.RESULTS):
            example.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
