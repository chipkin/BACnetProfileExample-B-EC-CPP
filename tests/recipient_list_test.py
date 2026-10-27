#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-EC Wire Test - Crimson's Recipient_List is writable, and alarms go where it is written.

    python3 tests/recipient_list_test.py [--exe build/BACnetExampleBEC] [--port 47833]

ANSI/ASHRAE 135-2024 cl. 12.21 (Notification Class, Recipient_List). The example seeds one
entry, the default cl. 12.21 gives a read-only list: local broadcast (network 0, empty MAC),
all days, 00:00:00.00-23:59:59.99, Process Identifier 0, unconfirmed, all transitions. The
list is writable, so a management station can add itself. This test starts the example
WITHOUT the test-only recipient (BEC_TEST_EVENT_RECIPIENT_PORT): the workstation receives
alarms only because it wrote itself into the list.

  1. Control: Recipient_List reads the seeded default entry, and nothing else.
  2. WriteProperty Recipient_List = the default entry + the workstation (127.0.0.1:<its port>,
     Process Identifier 2, confirmed): SimpleACK, and it reads back exactly as written.
  3. The passenger alarm: a ConfirmedEventNotification NORMAL -> OFFNORMAL reaches the
     workstation, and the example also sends the alarm to the local-broadcast entry (its own
     TX log line: no other socket can share the example's port).
  4. Released: a to-normal ConfirmedEventNotification reaches the workstation.
  5. Failure Mode: a Recipient_List write that is not a list of BACnetDestination is refused,
     and the list is unchanged.
"""
import sys

import ec_setup as setup
import wiretest
from wiretest import alarm, record

CRIMSON = (15, 1)                     # Notification Class 1
PROPERTY_RECIPIENT_LIST = 102
DEFAULT_ENTRY = alarm.destination(b"", 0, False)          # cl. 12.21's local-broadcast entry
WORKSTATION_PROCESS_IDENTIFIER = setup.TEST_RECIPIENT_PROCESS_IDENTIFIER
BROADCAST_EVENT_TX = "(broadcast) (Network Port 1) - Unconfirmed: UnconfirmedEventNotification"
NOTIFICATION_WAIT = 12                # one APDU_Timeout retransmission (see passenger_alarm_test.py)


def recipient_list(client, port):
    answer = client.read_property(port, *CRIMSON, PROPERTY_RECIPIENT_LIST, timeout=2.0)
    if answer.answered and answer.frame.pdu_type == wiretest.PDU_COMPLEX_ACK:
        return answer.value_octets, answer
    return None, answer


def main():
    args = setup.parser(__doc__).parse_args()
    workstation = setup.workstation()
    example = setup.start_controller(args)          # no test-only recipient
    hands = None
    try:
        hands = setup.control(args)

        # --- 1. Control -----------------------------------------------------------------------
        octets, answer = recipient_list(workstation, args.port)
        record("Control: Recipient_List is the seeded cl. 12.21 default entry only",
               octets == DEFAULT_ENTRY, octets.hex() if octets is not None else answer.describe())

        # --- 2. The workstation writes itself in ----------------------------------------------
        mac = bytes([127, 0, 0, 1, workstation.port >> 8, workstation.port & 0xFF])
        written = DEFAULT_ENTRY + alarm.destination(mac, WORKSTATION_PROCESS_IDENTIFIER, True)
        answer = setup.write(workstation, args.port, CRIMSON, PROPERTY_RECIPIENT_LIST, written)
        record("WriteProperty Recipient_List (default entry + this workstation, confirmed) is accepted",
               answer.answered and answer.frame.pdu_type == wiretest.PDU_SIMPLE_ACK, answer.describe())
        octets, answer = recipient_list(workstation, args.port)
        record("Recipient_List reads back exactly as written", octets == written,
               octets.hex() if octets is not None else answer.describe())

        # --- 3. The alarm reaches the written recipients ----------------------------------------
        broadcasts_before = example.output().count(BROADCAST_EVENT_TX)
        mark = workstation.mark()
        hands.send("alarm on")
        notification = workstation.wait_for_notification(
            setup.from_lift(alarm.EVENT_STATE_OFFNORMAL, setup.EVENT_TYPE_CHANGE_OF_STATE), NOTIFICATION_WAIT, mark)
        record("Alarm: a ConfirmedEventNotification NORMAL -> OFFNORMAL reaches the written workstation, "
               "Process Identifier 2",
               notification is not None and notification.confirmed and
               notification.process_identifier == WORKSTATION_PROCESS_IDENTIFIER,
               notification.describe() if notification else
               f"got {[received.describe() for received in workstation.notifications_since(mark)]}")
        record("Alarm: the default entry's local broadcast UnconfirmedEventNotification is sent too",
               example.output().count(BROADCAST_EVENT_TX) > broadcasts_before,
               f"{example.output().count(BROADCAST_EVENT_TX) - broadcasts_before} broadcast event TX lines")

        # --- 4. Released ----------------------------------------------------------------------------
        mark = workstation.mark()
        hands.send("alarm off")
        notification = workstation.wait_for_notification(
            setup.from_lift(alarm.EVENT_STATE_NORMAL, setup.EVENT_TYPE_CHANGE_OF_STATE), NOTIFICATION_WAIT, mark)
        record("Released: a to-normal ConfirmedEventNotification reaches the written workstation",
               notification is not None and notification.from_state == alarm.EVENT_STATE_OFFNORMAL,
               notification.describe() if notification else
               f"got {[received.describe() for received in workstation.notifications_since(mark)]}")

        # --- 5. Failure Mode ----------------------------------------------------------------------
        answer = setup.write(workstation, args.port, CRIMSON, PROPERTY_RECIPIENT_LIST,
                             wiretest.application_unsigned(5))
        record("A Recipient_List write that is not a list of BACnetDestination is refused",
               answer.answered and answer.frame.pdu_type in (wiretest.PDU_ERROR, wiretest.PDU_REJECT),
               answer.describe())
        octets, answer = recipient_list(workstation, args.port)
        record("Recipient_List unchanged by the refused write", octets == written,
               octets.hex() if octets is not None else answer.describe())
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
