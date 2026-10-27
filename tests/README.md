# B-EC Wire Tests

Tests that drive the running elevator controller over BACnet/IP from outside
it. They are written against the series' shared harness in
[`../wiretest/`](../wiretest/README.md) (vendored, like `common/`); everything
specific to this device is here. Python 3 standard library only - nothing to
`pip install`.

They prove the B-EC Profile Function - ANSI/ASHRAE 135-2024 L.13.2: "A B-EC
device performs elevator control. It supports limited modification of its
elevator objects by another device" - against a Python-simulated landing-call
panel, plus its Failure Modes. Each check has been shown to fail with its
feature removed (see [Mutation results](#mutation-results)).

## Running

Build the example (README "Build"), then from the repository root:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBEC
```

On Windows, `--exe build\Release\BACnetExampleBEC.exe` (or the
`build\static` tree). It ends with `ALL WIRE TESTS PASSED` (exit 0) or the
scripts that failed, in about a minute and a half. `--port` (default 47833) is
the UDP port the test starts the device on; `--port + 1` is the Simulation's
control channel. CI (`.github/workflows/release.yml`) runs it on Linux after the
smoke test.

## The setup

```
landing-call panel / operator workstation (127.0.0.1)   - the Peers: landing calls,
    |  BACnet/IP, unicast                                   reads, COV, acks; Crimson's
BACnetExampleBEC  UDP --port                            confirmed recipient
    ^                                                   - Device 389013, Maroon + Mauve
    |  127.0.0.1 UDP --port + 1, plain text             - test-only control channel
the test, playing the physical world                    (BEC_SIMULATION_CONTROL_PORT)
```

The Peers are Python BACnet clients (`wiretest.Client`, `wiretest.Workstation`),
never another example's binary. Landing calls are always BACnet: a
WriteProperty of Maroon's `Landing_Call_Control` with a raw-encoded
BACnetLandingCallStatus built by `wiretest.services.landing_call_status()`
(wiretest 0.7.0). The control channel only presses the car's
alarm button, blocks its doorway and speeds it up (500 ms per floor, 250 ms per
door move, 600 ms dwell). Retries and the COV-based ordered checks work as in
B-EM-CPP (`ec_setup.client()` / `ec_setup.workstation()`, wiretest's
`retries=2, timeout=0.5`: a visible `[RETRY]` after 0.5 s - Windows loopback
on a loaded machine was measured losing about one datagram in 700).

## `landing_call_test.py` - the Profile Function

1. **Control**: car at floor 1, `STOPPED`, door `CLOSED`; `Landing_Calls`
   empty; `Landing_Call_Control` reads floor 0 / `NONE`; with no call the car
   stays (COV: nothing after the subscription's first notification).
2. **Floor 6, DOWN** is written: SimpleACK; `Landing_Call_Control` reads it
   back; **`Landing_Calls` lists it** and **`Assigned_Landing_Calls`** lists it.
3. **The call clears with the car at 6, `STOPPED`, door opening** - and every
   read that still listed it was taken before the car stood at 6. Every RPM
   snapshot of the moving car is `UP` with the door `SAFETY_LOCKED`; the trip
   takes at least five floor-travel times; COV hears 2, 3, 4, 5, 6 and the door
   `SAFETY_LOCKED` -> `OPENING` -> `OPENED`.
4. **A destination call, 3 -> 8**: accepted; `Landing_Calls` lists it,
   `Assigned_Landing_Calls` shows it as `UP`; the car goes down to 3 and the
   call clears there; **`Registered_Car_Call` lists 8**; the car carries on to
   8 and the car call clears. COV: 5, 4, 3, 4, 5, 6, 7, 8.

## `landing_call_failure_test.py` - Failure Modes

A. **Unserved floors**: calls for floor 9, floor 0 and a destination of 9 are
   **refused with an Error**; `Landing_Calls` stays empty;
   `Landing_Call_Control` keeps the last accepted call; the car does not move.
   (The stack answers Error PROPERTY / WRITE_ACCESS_DENIED: the landing-call
   callback has no errorCode parameter to choose another - TODO.md.)

B. **A faulted car**: at floor 3 the doorway is blocked: `Fault_Signals` =
   { `DOOR_CLOSING_FAULT` }, `Reliability` `FAULTS_LISTED`, `Event_State`
   `FAULT`, and a NORMAL -> FAULT (CHANGE_OF_RELIABILITY) notification. A call
   for 7 is **accepted and in `Landing_Calls`, but `Assigned_Landing_Calls` is
   empty and the car stays at 3**. The doorway clears: FAULT -> NORMAL
   notification, the call is assigned, the car goes to 7, and the call clears.

## `passenger_alarm_test.py` - alarm and acknowledgement

As B-EM-CPP's: CHANGE_OF_STATE alarm (NORMAL -> OFFNORMAL, priority 100, ack
required), GetEventInformation, AcknowledgeAlarm with `Acked_Transitions` and an
**ACK_NOTIFICATION** to the recipients, the return to normal; **Failure Modes**:
AcknowledgeAlarm for the Escalator refused, WriteProperty to `Car_Position`,
`Passenger_Alarm` and `Out_Of_Service` refused (the controller is told where to
go, not where the car is). It also checks that Crimson's seeded `Recipient_List`
entry is the cl. 12.21 local-broadcast default (Process Identifier 0), and that the
alarm is sent to it as a local broadcast (the example's own TX log line).

## `recipient_list_test.py` - Crimson's writable Recipient_List

Started **without** the test-only recipient. Control: `Recipient_List` is the
seeded default entry only. The workstation writes the default entry plus itself
(127.0.0.1, Process Identifier 2, confirmed): SimpleACK, and it reads back exactly
as written. The passenger alarm then reaches the workstation (to-offnormal and
to-normal ConfirmedEventNotifications), and the default entry's local broadcast
is still sent. **Failure Mode**: a write that is not a list of BACnetDestination
is refused and the list is unchanged. Before the list was writable, the write was
refused and the alarm never reached the workstation.

## `outputs_test.py` - the commandable outputs

Chartreuse 55.0 at priority 8, then relinquished back to 20.0; Fuchsia priority
5 beats 10; **Failure Mode**: Indigo state 9 (of 3) refused with Error
VALUE_OUT_OF_RANGE, Present_Value unchanged.

## `discovery_test.py` - every listed property reads as a value

The same walk as B-SS-CPP's discovery test; only the expected-object list
differs.

1. **Who-Is** (for 389013, unicast) -> the device's I-Am.
2. **Device `Object_List`** names exactly the thirteen objects `main.cpp`
   creates: the Device, Analog Input 1, Binary Input 1, Multi-state Input 1,
   Analog Output 1, Binary Output 1, Multi-state Output 1, Network Port 1,
   Elevator Group 1, Lift 1, Escalator 1, Positive Integer Value 1 and
   Notification Class 1. This is the control: a walk over nothing would pass.
3. For each object, **`Property_List`** reads, and a ReadProperty of every
   property it lists - plus `Object_Identifier`, `Object_Name`, `Object_Type`
   and `Property_List`, which cl. 12.1.1.4.1 leaves out of the list - returns a
   ComplexACK. An Error, Reject, Abort or no answer prints an `[UNREADABLE]` line
   and fails the check. 135-2024 cl. 12.1.1.4.1: Property_List holds "one
   property identifier for each property that exists within the object".
4. Network Port 1's `IP_DNS_Server` (406), `FD_BBMD_Address` (418) and
   `FD_Subscription_Lifetime` (419) are each listed and read as a value - the
   three reads Chipkin BACnet Explorer found failing on B-SS at stack 6.0.21
   (B-SS-CPP #20-#22); every example has the same stack Network Port.

## What it found

Run 2026-10-15 at stack `6.x` @ `64b2cfac5`, with `main.cpp` as it was at
example 1.0.2, Windows STATIC build: 18/19.

```
[UNREADABLE] Elevator Group 1 property 470: Error class=2 code=27
[UNREADABLE] Elevator Group 1 property 471: Error class=2 code=27
[FAIL] every property of every object reads as a value (184 reads) - 2 unreadable: Elevator Group 1 470, Elevator Group 1 471
```

Error class 2 code 27 is `property` / `read-access-denied`. Both were the
example's own defects in `GetListElevatorGroupLandingCallStatus` (CHANGELOG
1.1.0):

- **`Landing_Calls` (470)**: the callback answered an empty list by returning
  `true` without supplying an element. The stack's contract
  (`FPCallbackGetListElevatorGroupLandingCallStatus`): "false if list is empty
  (and rangeIndexOrSequence is 0)". It now returns `false`.
- **`Landing_Call_Control` (471)** is one `BACnetLandingCallStatus`, but until a
  landing call was written the callback supplied nothing. It now answers floor
  0, direction `none` (`09 00 19 01`) until a call is written.

After the fix: 19/19, 184 reads, on Windows (STATIC, x3) and Linux (WSL Ubuntu
22.04, SOURCE build, x2), no `[RETRY]`.

## Mutation results

Each feature removed from `main.cpp` (or `simulation/ElevatorCar.cpp`), the
binary rebuilt (its mtime checked), the named script run: it must fail.
Windows STATIC, stack `6.x` @ `64b2cfac5`, 2026-10-16.

| Mutation | Script | Result | First failing check |
|---|---|---|---|
| E1 landing call only recorded (car not sent) | `landing_call_test.py` | CAUGHT (13/24) | The call cleared with the car at floor 6, STOPPED, door opening or open |
| E2 landing call never cleared | `landing_call_test.py` | CAUGHT (15/24) | The call cleared with the car at floor 6, STOPPED, door opening or open |
| E3 call cleared at once, not when the car arrives | `landing_call_test.py` | CAUGHT (12/24) | The call is active: Landing_Calls lists floor 6, DOWN |
| E4 Landing_Calls not served (always empty) | `landing_call_test.py` | CAUGHT (12/24) | The call is active: Landing_Calls lists floor 6, DOWN |
| E5 Assigned_Landing_Calls always empty | `landing_call_test.py` | CAUGHT (22/24) | ... and assigned to the car: Mauve's Assigned_Landing_Calls lists floor 6, DOWN |
| E6 destination ignored (no car call) | `landing_call_test.py` | CAUGHT (21/24) | The passenger is in the car: Registered_Car_Call lists 8 |
| E7 Car_Position constant | `landing_call_test.py` | CAUGHT (19/24) | The call cleared with the car at floor 6, STOPPED, door opening or open |
| E8 Landing_Call_Control not read back | `landing_call_test.py` | CAUGHT (23/24) | Landing_Call_Control reads back floor 6, DOWN |
| E9 unserved floor accepted | `landing_call_failure_test.py` | CAUGHT (11/20) | Landing_Call_Control = floor 9, UP (not served by this group) is refused with an Error |
| E10 faulted car still assigned its calls | `landing_call_failure_test.py` | CAUGHT (19/20) | ... but NOT assigned: Mauve's Assigned_Landing_Calls is empty |
| E12 no FAULT_LISTED algorithm | `landing_call_failure_test.py` | CAUGHT (17/20) | Doorway blocked: Fault_Signals = { DOOR_CLOSING_FAULT }, Reliability FAULTS_LISTED, Event_State FAULT |
| E13 Fault_Signals always empty | `landing_call_failure_test.py` | CAUGHT (17/20) | Doorway blocked: Fault_Signals = { DOOR_CLOSING_FAULT }, Reliability FAULTS_LISTED, Event_State FAULT |
| E14 passenger alarm not reported | `passenger_alarm_test.py` | CAUGHT (8/14) | Alarm pressed: Passenger_Alarm TRUE, Event_State OFFNORMAL, IN_ALARM set |
| E15 AcknowledgeAlarm refused | `passenger_alarm_test.py` | CAUGHT (12/15) | AcknowledgeAlarm for Lift 1's to-offnormal is accepted |
| E16 the app's MSO range check removed | `outputs_test.py` | SURVIVED (8/8) | none - the stack refuses a state above Number_Of_States itself, so the app's check (copied from B-SA's F-OUTPUTS) is redundant; E16b shows the test gates the range |
| E11 door interlock removed (a faulted car leaves without closing its door) | `landing_call_failure_test.py` | CAUGHT (19/20) | Faulted: after 4 floor-travel times the car is still at floor 3, STOPPED |
| E16b Indigo reports 10 states (the stack's own range check widens) | `outputs_test.py` | CAUGHT (6/8) | Indigo = 9 (it has 3 states) is refused with Error VALUE_OUT_OF_RANGE |

E11 first targeted a `!Faulted()` departure guard in the car; that guard was dead code (deleted - the door interlock holds a faulted car, as found in B-EM-CPP) so the run reported a missing anchor, and E11 was re-run against the interlock itself.
