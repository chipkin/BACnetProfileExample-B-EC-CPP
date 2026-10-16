# SPDX-License-Identifier: CC0-1.0
# Public-domain example code (CC0) - see ../LICENSE.
"""BACnetLandingCallStatus: encode one for a WriteProperty, decode what an Elevator Group reads back.

GENERIC - proposed for wiretest/ 0.7.0. wiretest 0.6.0 can already send any value octets
with write_property(); what it lacks is the constructed value itself. Production verbatim from
ANSI/ASHRAE 135-2024 clause 21.6:

    BACnetLandingCallStatus ::= SEQUENCE {
        floor-number  [0] Unsigned8,
        command       CHOICE { direction [1] BACnetLiftCarDirection, destination [2] Unsigned8 },
        floor-text    [3] CharacterString OPTIONAL
    }

Landing_Call_Control (cl. 12.58.10) is one BACnetLandingCallStatus; Landing_Calls (12.58.9) is a
BACnetLIST of them; Assigned_Landing_Calls (12.59.11) is an array, per car door, of
BACnetAssignedLandingCalls (a list of { floor-number [0], direction [1] }) - same tags, no [2]/[3].

    write_property(port, 57, 1, 471, landing_call_status(7, direction=DIRECTION_UP))
    decode_landing_calls(answer.value_octets)  ->  [{"floor": 7, "direction": 3}, ...]
"""
from wiretest import codec

# BACnetLiftCarDirection (cl. 21).
DIRECTION_UNKNOWN, DIRECTION_NONE, DIRECTION_STOPPED, DIRECTION_UP, DIRECTION_DOWN, DIRECTION_UP_AND_DOWN = range(6)


def landing_call_status(floor, direction=None, destination=None, floor_text=None):
    """The value octets of one BACnetLandingCallStatus; give exactly one of direction / destination."""
    if (direction is None) == (destination is None):
        raise ValueError("a landing call has a direction or a destination, not both")
    octets = codec.context_unsigned(0, floor)
    octets += codec.context_enumerated(1, direction) if direction is not None else codec.context_unsigned(2, destination)
    if floor_text is not None:
        octets += codec.context_character_string(3, floor_text)
    return octets


def decode_landing_calls(octets):
    """Every BACnetLandingCallStatus (or BACnetAssignedLandingCalls entry) in `octets`, in order,
    as dicts with 'floor' and 'direction' or 'destination' (and 'floor_text' if present).
    Opening/closing tags (an array element's list) are skipped."""
    calls = []
    position = 0
    while octets and position < len(octets):
        number, is_context, kind, body, position = codec.read_tag(octets, position)
        if kind != "value" or not is_context:
            continue
        if number == 0:
            calls.append({"floor": int.from_bytes(body, "big")})
        elif calls and number == 1:
            calls[-1]["direction"] = int.from_bytes(body, "big")
        elif calls and number == 2:
            calls[-1]["destination"] = int.from_bytes(body, "big")
        elif calls and number == 3:
            calls[-1]["floor_text"] = body[1:].decode("utf-8", errors="replace")
    return calls
