#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""B-EC Wire Test - the commandable outputs: priority arbitration and an out-of-range command.

    python3 tests/outputs_test.py [--exe build/BACnetExampleBEC] [--port 48035]

Analog Output 1 "Chartreuse", Binary Output 1 "Fuchsia" and Multi-state Output 1 "Indigo" are
the F-OUTPUTS block (canonical in B-SA-CPP): commandable objects whose Present_Value the stack
resolves from a 16-slot Priority_Array plus Relinquish_Default (135-2024 cl. 19.2). They drive
nothing in this example; this test proves they arbitrate as the clause says.

  1. Chartreuse starts at Relinquish_Default 20.0. A write of 55.0 at priority 8 takes it to
     55.0 (Priority_Array[8] = 55.0); writing NULL at 8 relinquishes it back to 20.0.
  2. Fuchsia: ACTIVE at priority 10, then INACTIVE at priority 5 - the higher priority (5) wins;
     relinquish 5 and ACTIVE at 10 shows through.
  3. Failure Mode: Indigo has 3 states; a write of state 9 is refused with Error
     VALUE_OUT_OF_RANGE and Present_Value is unchanged.
"""
import sys

import ec_setup as setup  # first: it puts the vendored wiretest/ on sys.path
from ec_setup import acked
import wiretest
from wiretest import (PROPERTY_PRESENT_VALUE, PROPERTY_PRIORITY_ARRAY, application_enumerated, application_null,
                      application_real, application_unsigned, record)

CHARTREUSE = (wiretest.OBJECT_TYPE_ANALOG_OUTPUT, 1)
FUCHSIA = (wiretest.OBJECT_TYPE_BINARY_OUTPUT, 1)
INDIGO = (14, 1)            # Multi-state Output object type: 14
INACTIVE, ACTIVE = 0, 1


def value(client, port, object_identifier, property_identifier=PROPERTY_PRESENT_VALUE, array_index=None):
    answer = setup.read(client, port, object_identifier, property_identifier, array_index)
    return answer.value if answer.ok else answer.describe()


def main():
    args = setup.parser(__doc__).parse_args()
    example = setup.start_controller(args)
    client = wiretest.Client()     # setup.ask() does the retrying
    try:
        # --- 1. Chartreuse -------------------------------------------------------------------
        record("Chartreuse starts at its Relinquish_Default, 20.0", value(client, args.port, CHARTREUSE) == 20.0,
               f"read {value(client, args.port, CHARTREUSE)}")
        answer = setup.write(client, args.port, CHARTREUSE, PROPERTY_PRESENT_VALUE, application_real(55.0), 8)
        record("Write 55.0 at priority 8 is accepted", acked(answer), answer.describe())
        record("Present_Value 55.0, Priority_Array[8] 55.0",
               (value(client, args.port, CHARTREUSE), value(client, args.port, CHARTREUSE, PROPERTY_PRIORITY_ARRAY, 8))
               == (55.0, 55.0))
        answer = setup.write(client, args.port, CHARTREUSE, PROPERTY_PRESENT_VALUE, application_null(), 8)
        record("Relinquish (NULL) at priority 8: back to 20.0, Priority_Array[8] NULL",
               acked(answer) and value(client, args.port, CHARTREUSE) == 20.0 and
               value(client, args.port, CHARTREUSE, PROPERTY_PRIORITY_ARRAY, 8) is None,
               f"read {value(client, args.port, CHARTREUSE)}")

        # --- 2. Fuchsia ---------------------------------------------------------------------------
        setup.write(client, args.port, FUCHSIA, PROPERTY_PRESENT_VALUE, application_enumerated(ACTIVE), 10)
        setup.write(client, args.port, FUCHSIA, PROPERTY_PRESENT_VALUE, application_enumerated(INACTIVE), 5)
        record("Fuchsia: INACTIVE at priority 5 beats ACTIVE at 10", value(client, args.port, FUCHSIA) == INACTIVE,
               f"read {value(client, args.port, FUCHSIA)}")
        setup.write(client, args.port, FUCHSIA, PROPERTY_PRESENT_VALUE, application_null(), 5)
        record("Relinquish priority 5: ACTIVE at 10 shows through", value(client, args.port, FUCHSIA) == ACTIVE,
               f"read {value(client, args.port, FUCHSIA)}")

        # --- 3. Failure Mode: Indigo, state 9 of 3 ---------------------------------------------------
        before = value(client, args.port, INDIGO)
        answer = setup.write(client, args.port, INDIGO, PROPERTY_PRESENT_VALUE, application_unsigned(9), 8)
        error = wiretest.error_class_and_code(answer.frame.payload) if answer.answered and \
            answer.frame.pdu_type == wiretest.PDU_ERROR else None
        record("Indigo = 9 (it has 3 states) is refused with Error VALUE_OUT_OF_RANGE",
               error is not None and error[1] == wiretest.ERROR_CODE_VALUE_OUT_OF_RANGE, answer.describe())
        record("Indigo's Present_Value is unchanged", value(client, args.port, INDIGO) == before,
               f"read {value(client, args.port, INDIGO)} (was {before})")
    finally:
        client.close()
        example.stop()
        if not all(wiretest.results.RESULTS):
            example.keep_log()
    return wiretest.summary()


if __name__ == "__main__":
    sys.exit(main())
