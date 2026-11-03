# TODO

Defects this example cannot fix itself. A defect that stops a Wire Test check is
reported as a `[KNOWN GAP]` line ([`tests/`](tests/README.md)): reported on every
run, not counted as a failure. **There are none at Stack Pin `6.x` @ `1e7dffe2b`**
- every check of the Profile Function and its Failure Modes passes (Wire Tests on
Windows, 2026-11-01).

## Observed in the stack, not affecting a check

### 1. A refused landing call cannot say why

Filed: [#3966](https://github.com/chipkin/cas-bacnet-stack/issues/3966).


- **What:** `BACnetStack_RegisterCallbackSetElevatorGroupLandingCallControl`'s
  callback has no `errorCode` out-parameter (every `SetProperty*` callback has
  one). When it returns false - here, a call for a floor the group does not
  serve - the stack answers Error PROPERTY / WRITE_ACCESS_DENIED
  (`BACnetBusinessLogic.cpp` `SetSpecificPropertyUsingCallbacks`, which never
  sets `errorCode` for this property). VALUE_OUT_OF_RANGE would tell the client
  what it did wrong; WRITE_ACCESS_DENIED reads as "this property is not
  writable", which is false.
- **Effect here:** the call is still refused and nothing registers
  (`tests/landing_call_failure_test.py` checks for an Error, not its code).
- **Evidence:** `landing_call_failure_test.py` output, `Error class=2 code=40`,
  Windows STATIC and Linux, 2026-10-16.

## Fixed in the stack at the pin

Both were observed here at earlier stack revisions; the fix for each is in the
pinned revision (`1e7dffe2b`). Kept as a reference for support.

- **After a car door fault cleared, a held Passenger_Alarm was not re-judged**
  ([#3967](https://github.com/chipkin/cas-bacnet-stack/issues/3967), closed). The
  `UpdateValue` of `Fault_Signals` that cleared a fault ran CHANGE_OF_STATE on the
  empty `Fault_Signals` list instead of `Passenger_Alarm` (debug log:
  `monitoredValue has invalid datatype=[255]`).
- **`SetPropertySubscribable` left `COV_Increment` absent**
  (`chipkin/cas-bacnet-stack#4602`, closed). The stack now enables it, reading
  1.0, when `Present_Value` is made subscribable. This example still enables and
  serves Analog Input 1's `COV_Increment` itself (read-only, 1.0), as cl. 12.2
  requires for an Analog Input that supports COV reporting.

## Known limitations of this example

- **A written `Recipient_List` is lost at restart.** Notification Class 1's
  `Recipient_List` is writable, but the list lives only in memory and returns to
  the standard default (local broadcast) when the example restarts (cl. 12.21.8).
  Whether the examples should keep it is an open question.
- **Analog Input 1's `Out_Of_Service` is read-only.** A test tool therefore
  cannot drive that input to exercise COV, event or DeviceCommunicationControl
  scenarios; use the `up` / `down` keys on the console instead.
- **`ReinitializeDevice` STARTBACKUP / STARTRESTORE are not supported**; they
  answer Error (SERVICES, OPTIONAL_FUNCTIONALITY_NOT_SUPPORTED). COLDSTART and
  WARMSTART are supported.
- **Operator-driven conformance rows stay manual** (AE-N-I-B, AE-ACK-B and
  DM-DDB-A steps that need a person to press a key).
- **Time synchronization and restart are not covered by the Wire Tests**; they
  were checked by hand.
