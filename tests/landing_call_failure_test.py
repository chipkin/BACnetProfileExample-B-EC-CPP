#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-EC Wire Test - Failure Modes: a call the group cannot serve, and a car that is faulted.

    python3 tests/landing_call_failure_test.py [--exe build/BACnetExampleBEC] [--port 48035]

  A. A floor this group does not serve. The car serves universal floors 1-8. A landing call
     for floor 9, for floor 0, or a destination call from 2 to 9 is refused with an Error;
     Landing_Calls stays empty, Landing_Call_Control keeps its last accepted value, and the car
     does not move.

  B. A faulted car. Cl. 12.59.32 Fault_Signals: "DOOR_CLOSING_FAULT  A door is failing to
     close"; cl. 12.59: "For reliability-evaluation, the FAULT_LISTED fault algorithm can be
     applied"; cl. 13.2.5.3: "For all transitions to, or from, the FAULT state, the
     corresponding event notification shall use the Event Type CHANGE_OF_RELIABILITY."
       1. A landing call brings the car to floor 3; something blocks the doorway (Simulation).
          The door cannot close: Fault_Signals = { DOOR_CLOSING_FAULT }, Reliability
          FAULTS_LISTED, Event_State FAULT, and the operator workstation (a confirmed
          recipient, test-only BEC_TEST_EVENT_RECIPIENT_PORT) gets a NORMAL -> FAULT
          notification.
       2. A landing call for floor 7, UP, is written: accepted - the passenger's call registers
          in Landing_Calls - but NOT assigned: Mauve's Assigned_Landing_Calls stays empty, and the
          car stays at floor 3 for several floor-travel times.
       3. The doorway clears: the door closes, the fault clears with a FAULT -> NORMAL
          notification, the call is assigned to the car, the car goes to 7, and the call clears.
"""
import sys
import time

import ec_setup as setup  # first: it puts the vendored wiretest/ on sys.path
from ec_setup import DIRECTION_STOPPED, DIRECTION_UP, DOOR_OPENED, refused
import wiretest
from wiretest import alarm, record

FAULT_PRIORITY = 50          # main.cpp NC_PRIORITY_TO_FAULT
# A confirmed notification the workstation missed is sent again APDU_Timeout (10 s) later
# (main.cpp serves Number_Of_APDU_Retries 3), so wait long enough for one retransmission.
NOTIFICATION_WAIT = 12


def fault_state(workstation, args):
    return (setup.lift_values(workstation, args.port, setup.PROPERTY_FAULT_SIGNALS),
            setup.lift_value(workstation, args.port, setup.PROPERTY_RELIABILITY),
            setup.lift_value(workstation, args.port, setup.PROPERTY_EVENT_STATE))


def main():
    args = setup.parser(__doc__).parse_args()
    workstation = wiretest.Workstation()
    example = setup.start_controller(args, recipient_port=workstation.port)
    hands = None
    try:
        hands = setup.control(args)

        # --- A. Floors the group does not serve ------------------------------------------------
        accepted = setup.write_landing_call(workstation, args.port, 2, direction=DIRECTION_UP)
        record("Control: a call for floor 2, UP is accepted", setup.acked(accepted), accepted.describe())
        wiretest.wait_until(lambda: setup.landing_calls(workstation, args.port) == [] and
                            (setup.car_snapshot(workstation, args.port) or (0,))[0] == 2, 8, 0.1)
        start = setup.car_snapshot(workstation, args.port)
        record("Control: the car served it - floor 2, Landing_Calls empty",
               start is not None and start[0] == 2 and setup.landing_calls(workstation, args.port) == [],
               f"read {start}")
        for name, floor, direction, destination in (("floor 9, UP", 9, DIRECTION_UP, None),
                                                     ("floor 0, UP", 0, DIRECTION_UP, None),
                                                     ("floor 2, destination 9", 2, None, 9)):
            answer = setup.write_landing_call(workstation, args.port, floor, direction=direction, destination=destination)
            record(f"Landing_Call_Control = {name} (not served by this group) is refused with an Error",
                   answer.answered and answer.frame.pdu_type == wiretest.PDU_ERROR, answer.describe())
        record("Refused calls are not active: Landing_Calls is empty", setup.landing_calls(workstation, args.port) == [])
        record("Landing_Call_Control still reads the last accepted call (floor 2, UP)",
               setup.landing_call_control(workstation, args.port) == {"floor": 2, "direction": DIRECTION_UP},
               f"read {setup.landing_call_control(workstation, args.port)}")
        time.sleep(4 * setup.TRAVEL_MS / 1000)
        still = setup.car_snapshot(workstation, args.port)
        record("The car did not move for a refused call", still is not None and still[:2] == (2, DIRECTION_STOPPED),
               f"read {still}")

        # --- B1. The car faults at floor 3 --------------------------------------------------------
        setup.write_landing_call(workstation, args.port, 3, direction=DIRECTION_UP)
        at_three = wiretest.wait_until(lambda: setup.car_snapshot(workstation, args.port) == (3, DIRECTION_STOPPED,
                                                                                              DOOR_OPENED), 8, 0.05)
        record("The car answers a call at floor 3: STOPPED there, door OPENED", at_three,
               f"read {setup.car_snapshot(workstation, args.port)}")
        mark = workstation.mark()
        hands.send("obstruct on")
        faulted = wiretest.wait_until(lambda: fault_state(workstation, args) == (
            [setup.LIFT_FAULT_DOOR_CLOSING_FAULT], setup.RELIABILITY_FAULTS_LISTED, alarm.EVENT_STATE_FAULT),
            3 * (setup.DWELL_MS + 2 * setup.DOOR_MS) / 1000 + 3, 0.1)
        record("Doorway blocked: Fault_Signals = { DOOR_CLOSING_FAULT }, Reliability FAULTS_LISTED, Event_State FAULT",
               faulted, f"read {fault_state(workstation, args)}")
        notification = workstation.wait_for_notification(
            setup.from_lift(alarm.EVENT_STATE_FAULT, setup.EVENT_TYPE_CHANGE_OF_RELIABILITY), NOTIFICATION_WAIT, mark)
        record("ConfirmedEventNotification from Lift 1: NORMAL -> FAULT, CHANGE_OF_RELIABILITY, priority 50",
               notification is not None and notification.confirmed and notification.priority == FAULT_PRIORITY,
               notification.describe() if notification else
               f"got {[received.describe() for received in workstation.notifications_since(mark)]}")

        # --- B2. A call while faulted: registered, not assigned, not served ---------------------
        answer = setup.write_landing_call(workstation, args.port, 7, direction=DIRECTION_UP)
        record("Faulted car: a call for floor 7, UP is still accepted (the passenger pressed the button)",
               setup.acked(answer), answer.describe())
        calls = setup.landing_calls(workstation, args.port)
        record("... it is active in Landing_Calls", calls == [{"floor": 7, "direction": DIRECTION_UP}], f"read {calls}")
        assigned = setup.assigned_landing_calls(workstation, args.port)
        record("... but NOT assigned: Mauve's Assigned_Landing_Calls is empty", assigned == [], f"read {assigned}")
        time.sleep(4 * setup.TRAVEL_MS / 1000)
        snapshot = setup.car_snapshot(workstation, args.port)
        record("Faulted: after 4 floor-travel times the car is still at floor 3, STOPPED",
               snapshot is not None and snapshot[:2] == (3, DIRECTION_STOPPED), f"read {snapshot}")
        record("Faulted: the call is still waiting in Landing_Calls",
               setup.landing_calls(workstation, args.port) == [{"floor": 7, "direction": DIRECTION_UP}])

        # --- B3. The doorway clears -----------------------------------------------------------------------
        mark = workstation.mark()
        hands.send("obstruct off")
        cleared = wiretest.wait_until(lambda: fault_state(workstation, args) == (
            [], setup.RELIABILITY_NO_FAULT_DETECTED, alarm.EVENT_STATE_NORMAL),
            (setup.DWELL_MS + 2 * setup.DOOR_MS) / 1000 + 3, 0.1)
        record("Doorway clear: Fault_Signals empty, Reliability NO_FAULT_DETECTED, Event_State NORMAL", cleared,
               f"read {fault_state(workstation, args)}")
        notification = workstation.wait_for_notification(
            setup.from_lift(alarm.EVENT_STATE_NORMAL, setup.EVENT_TYPE_CHANGE_OF_RELIABILITY), NOTIFICATION_WAIT, mark)
        record("ConfirmedEventNotification from Lift 1: FAULT -> NORMAL, CHANGE_OF_RELIABILITY",
               notification is not None and notification.from_state == alarm.EVENT_STATE_FAULT,
               notification.describe() if notification else
               f"got {[received.describe() for received in workstation.notifications_since(mark)]}")
        assigned = wiretest.wait_until(lambda: setup.assigned_landing_calls(workstation, args.port) == [
            {"floor": 7, "direction": DIRECTION_UP}] or setup.landing_calls(workstation, args.port) == [], 2, 0.05)
        record("Back in service the call is assigned to the car (or already served)", assigned)
        served = wiretest.wait_until(lambda: setup.landing_calls(workstation, args.port) == [],
                                     3 * 4 * setup.TRAVEL_MS / 1000 + 5, 0.1)
        snapshot = setup.car_snapshot(workstation, args.port)
        record("The car goes to floor 7 and the call clears", served and snapshot is not None and snapshot[0] == 7,
               f"Landing_Calls {setup.landing_calls(workstation, args.port)}, car {snapshot}")
    finally:
        if hands is not None:
            hands.close()
        workstation.close()
        example.stop()
        if not all(wiretest.results.RESULTS):
            example.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
