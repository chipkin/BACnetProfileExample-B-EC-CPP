# TODO

Defects this example cannot fix itself. A defect that stops a Wire Test check is
reported as a `[KNOWN GAP]` line ([`tests/`](tests/README.md)): reported on every
run, not counted as a failure. **There are none at Stack Pin `6.x` @ `64b2cfac5`**
- every check of the Profile Function and its Failure Modes passes.

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

### 2. `UpdateValue(Fault_Signals)` logs a CHANGE_OF_STATE error

Filed: [#3967](https://github.com/chipkin/cas-bacnet-stack/issues/3967). Verification found it is more than a log line: after a fault
clears, CHANGE_OF_STATE is evaluated on the now-empty Fault_Signals list instead of
Passenger_Alarm, so a Passenger_Alarm that stayed TRUE through the fault is not re-judged.


Same as B-EM-CPP `TODO.md` 1: with CHANGE_OF_STATE on `Passenger_Alarm` and
FAULT_LISTED on `Fault_Signals`, the `UpdateValue` of `Fault_Signals` that clears
a fault (FAULT -> NORMAL) logs
`BACnetChangeOfStateEventAlgorithm::SetMonitoredValue() - Error: monitoredValue has invalid datatype=[255]`.
No effect on any check.
