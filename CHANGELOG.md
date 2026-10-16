# Changelog

All notable changes to this project are documented in this file.

## [1.2.0] - unreleased

Profile-functional (series bar, `docs/GLOSSARY.md` in the series repository).
ANSI/ASHRAE 135-2024 L.13.2: "A B-EC device performs elevator control. It
supports limited modification of its elevator objects by another device." A
landing call written over BACnet is now served.

### Added

- **The lift car Simulation** (`simulation/`, the same files as B-EM-CPP 1.2.0;
  README "What is Simulation"): floors 1-8, one floor every 2 s, door cycle,
  collective control, a door interlock, and a doorway that can be obstructed
  into `DOOR_CLOSING_FAULT`. No simulated passengers: the car moves only for
  landing calls.
- **Landing calls are served** (cl. 12.58.10): an accepted write to Maroon's
  `Landing_Call_Control` (a direction or a destination call) enters
  `Landing_Calls` (now the group's active calls, cl. 12.58.9) and the car's
  `Assigned_Landing_Calls`, sends the car, and clears the moment the car stops
  at the floor. A destination call then becomes a car call
  (`Registered_Car_Call`) to its destination.
- **Failure Modes**: a call for a floor outside 1-8 (or a destination outside
  1-8) is refused with an Error; a call while the car is faulted is accepted
  into `Landing_Calls` but not assigned, and served once the car recovers.
- **Lift 1 "Mauve" presents the car** (`Car_Position`, `Car_Moving_Direction`,
  `Car_Door_Status`, `Fault_Signals`, `Landing_Door_Status`, all live and
  subscribable where they change) and arms **FAULT_LISTED** on
  `Fault_Signals` with `Reliability` enabled; to-fault is now enabled.
- **`Number_Of_APDU_Retries` = 3** (cl. 12.11.29).
- **Test-only hooks**, neither a command-line option: `BEC_SIMULATION_CONTROL_PORT`
  (loopback control channel: alarm button, doorway, speed) and
  `BEC_TEST_EVENT_RECIPIENT_PORT` (a confirmed Crimson recipient at 127.0.0.1).
- **`s` key**: press / release the car's passenger alarm button.
- **Wire Tests**: `landing_call_test.py` (the Profile Function),
  `landing_call_failure_test.py` (both Failure Modes, with FAULT_LISTED
  notifications), `passenger_alarm_test.py` (CHANGE_OF_STATE, GetEventInformation,
  AcknowledgeAlarm with ACK_NOTIFICATION; the car's status refuses writes) and
  `outputs_test.py` (priority arbitration; MSO state 9 refused). Generic helpers
  proposed for `wiretest/` 0.7.0 in `tests/`: `landing_call.py`
  (BACnetLandingCallStatus encoder/decoder), `simulation_control.py`,
  `property_multiple.py`, `cov_multiple.py`. Default port 48035.

### Changed

- The passenger alarm no longer toggles on a 30-second timer; it is the car's
  alarm button (`s`, or the control channel).
- ReinitializeDevice COLDSTART also clears the landing calls and the car's stops.
- `main.cpp`'s header cited Annex L.14 for B-EC; it is L.13.2.
- Application_Software_Version 1.2.0.
- Wire Tests use the shared `wiretest/` 0.7.0: `tests/landing_call.py`, `simulation_control.py`, `property_multiple.py` and `cov_multiple.py` are folded into it (`wiretest.services`, `wiretest.SimulationControl`), and `ec_setup.ask()` is `wiretest.Client` / `Workstation(retries=2, timeout=0.5)`.

## [1.1.0] - unreleased

### Fixed

- **Elevator Group 1 (Maroon) had two properties a client could not read**,
  found by the new discovery Wire Test: `Landing_Calls` (470) and
  `Landing_Call_Control` (471) both answered Error `property` /
  `read-access-denied`. Both are answered by `GetListElevatorGroupLandingCallStatus`:
  - `Landing_Calls`: the callback answered "no calls" by returning `true`
    without supplying an element; the stack's contract is to return `false` on
    the first call for an empty list. It now does, and `Landing_Calls` reads as
    an empty list.
  - `Landing_Call_Control` is a single `BACnetLandingCallStatus`, not a list,
    but before any landing call was written the callback had nothing to supply.
    It now answers floor 0, direction `none` until a call is written (and again
    after a COLDSTART). A raw-encoded WriteProperty (`09 07 19 03`, floor 7 up)
    then reads back unchanged - checked by hand, the write path the README used
    to say was never wire-verified.

### Added

- **Wire Tests** (`tests/`, README "Wire Tests"): `tests/discovery_test.py`,
  B-SS-CPP's discovery test with this example's object list - Who-Is, the
  Device's `Object_List` (control: exactly the thirteen objects), then every
  object's `Property_List` and a ReadProperty of every listed property; any
  Error, Reject, Abort or silence fails. `tests/run_wire_tests.py` runs it; CI
  runs it on Linux after the smoke test. 19/19 on Windows and Linux.
- `wiretest/` 0.5.0, the series' shared Wiretest Harness, vendored verbatim.

### Changed

- **`common/` 3.3.0 -> 3.4.0** and **`wiretest/` 0.5.0 -> 0.6.0**, both copied
  verbatim (`common/` from B-SS-CPP `5d78299`, `wiretest/` from B-LS-CPP). With
  `common/` 3.4.0 a broadcast the stack addresses to this socket's own address
  goes to the subnet broadcast instead; `wiretest/` 0.6.0 only adds helpers.
  `tests/discovery_test.py` now sends its Who-Is a second time, with a visible
  `[RETRY]` line, if no I-Am comes back in 3 s: Who-Is is unconfirmed and the
  example's UDP receive can drop a datagram on Windows. Discovery results are
  unchanged: 19/19 on Windows and Linux, no `[RETRY]`.
- **Stack Pin** `6.x` @ `abd4cee1` (6.0.21) -> `6.x` @ `64b2cfac5` (6.0.23). No
  API change needed.
- **`common/` 3.0.0 -> 3.3.0** (B-SS-CPP `b640a81`, verbatim).
- **Protocol_Revision 24 -> 30** (the stack's default at the new pin).
- **Segmentation is now supported** (`segmented-both`, `Max_Segments_Accepted`
  16, `APDU_Segment_Timeout` 5000 ms): the stack's customer build compiles
  segmentation in from this pin (stack #2992). `docs/PICS.md` section 5 updated.
- **README and comments are honest about what the controller controls**: a
  status note says the example is BIBB-conformant but not yet
  Profile-functional - a landing call is stored and read back, nothing moves
  the car, and the outputs drive nothing. `main.cpp` no longer says a write
  "actually commands a landing call", and a comment copied from B-EM that called
  this device read-only is gone. The README's "wire-verified" paragraph now says
  what is checked by the Wire Tests and what only by hand.
- README, AGENTS.md and PICS version lines: stack 6.0.23, `common/` 3.3.0,
  Protocol_Revision 30 (the README still said example v1.0.0 and `common/`
  2.5.0). The series profile table is re-synced. APP_VERSION 1.0.2 -> 1.1.0.

## [1.0.2] - unreleased

### Changed

- **Device renamed from the series' colour placeholder "Rainbow" to "Chipkin
  Example B-EC"** so devices from different examples in the series are
  distinguishable from each other on the same BACnet network - every example
  previously announced the identical Object_Name "Rainbow", which made two
  examples on one subnet indistinguishable by name. Sub-object names (Analog
  Input 1 "Bronze", etc.) are unchanged - only the Device object's name
  changed. `docs/colour-table.md` (series root) updated to match. APP_VERSION
  bumped 1.0.1 -> 1.0.2.

## [1.0.1] - unreleased

### Fixed

- **`Application_Software_Version` (12) and `Firmware_Revision` (44) were
  hardcoded and stale.** `Application_Software_Version` now reads
  `APP_VERSION` directly (one source of truth, can't drift from
  `--version`'s own banner again). `Firmware_Revision` is now built at
  runtime from the CAS BACnet Stack's own `BACnetStack_GetAPIMajorVersion()`/
  `GetAPIMinorVersion()`/`GetAPIPatchVersion()`/`GetAPIBuildVersion()` (the
  same 4 calls `common/CASExampleHelper.cpp`'s `PrintVersion()` already uses
  for the startup banner), populated once right after `LoadBACnetFunctions()`
  succeeds. Same fix as `BACnetProfileExample-B-SCHUB-CPP` v1.1.13, applied
  series-wide after a real device read via BACnet Explorer found the stale
  values.

## [Unreleased]

### Changed

- Restructured documentation to match the series' README/TUTORIAL/PICS split
  (see `BACnetProfileExample-B-SS-CPP`, `docs/readme-tutorial-pics-restructure`):
  `README.md` cut down to this example only (series framing, the generic
  profile explanation, "Before you ship", "Link mode", "Troubleshooting",
  "Extending the example", "Objects and properties", and the CC0 paragraph
  removed - 607 -> 350 lines), a new `TUTORIAL.md` (extending the example,
  what each object type needs served, a representative object's served-by
  breakdown, the Relinquish_Default bug carried over verbatim, "Reviewing your
  device", and Troubleshooting), and a new `docs/PICS.md` (ANSI/ASHRAE 135
  Annex A shape, every row read from `main.cpp`).
- `docs/objects.json` gained a `Device` entry (first in the list) so the
  generated tables include the Device object; regenerated with
  `tools/gen-objects-properties.py` - **0 ⚠ rows**.
- **Build switched from a prebuilt STATIC library to the adapter's default
  SOURCE mode**: `cmake -B build -S .` / `cmake --build build --config
  Release`, with no `tools/build-stack-static.sh` step and no
  `-DCAS_BACNET_STACK_LINK=STATIC` flag. `CMakeLists.txt`, `AGENTS.md`, and
  `.github/workflows/release.yml` (dropped the static-library cache/build
  steps and the matrix `lib:` entries; link-mode assertion now expects
  `SOURCE`; `metrics.json` now records `"link_mode": "SOURCE"`; the packaged
  release artifact now also includes `TUTORIAL.md` and `docs/PICS.md`) were
  all updated to match. The v1.0.0 footprint numbers in `README.md` were
  measured from the old STATIC build; a note says the next release refreshes
  them under the SOURCE build documented now.
- `main.cpp`'s `CHANGE ALL OF THIS BEFORE YOU SHIP` block absorbed the
  per-field ship guidance that used to live only in the README's "Before you
  ship" table, including the `DEVICE_NAME` uniqueness warning.
- Re-synced the series table (`tools/sync-profile-table.sh
  BACnetProfileExample-B-EC-CPP`) and `AGENTS.md`'s layout/build sections.

## [1.0.0] - 2026-09-15

### Added

- Initial B-EC (Elevator Controller) example, built by seeding from
  `BACnetProfileExample-B-EM-CPP` (Wave 2, read-only Elevator Monitor) and
  adding writes back.
- CAS BACnet Stack pinned to `6.x` @ `abd4cee1c7f28ca8e1af4720849c4081082bbe82`
  (reports 6.0.21), linked as a **STATIC** library
  (`CAS_BACNET_STACK_LINK=STATIC`; built first by `tools/build-stack-static.sh`
  from the stack's own project files - see README "Link mode").
- `common/` vendored from `BACnetProfileExample-B-SS-CPP` (series source of
  truth) at v2.5.0, copied verbatim.
- Everything B-EM already has: DS-RP-B, DS-RPM-B, DS-COV-B, DS-COVM-B,
  AE-N-I-B, AE-ACK-B, AE-INFO-B, DM-DDB-B, DM-DOB-B, DM-DCC-B, the base
  sensors, Network Port, Elevator Group/Lift/Escalator family, Notification
  Class, and the intrinsic ChangeOfState alarm on the Lift's Passenger_Alarm.
- **F-OUTPUTS** (canonical pattern from `BACnetProfileExample-B-SA-CPP`,
  copied verbatim): DS-WP-B, DS-WPM-B. Three new commandable objects - Analog
  Output 1 "Chartreuse" (REAL setpoint), Binary Output 1 "Fuchsia"
  (active/inactive), Multi-State Output 1 "Indigo" (state 1..3) - each with a
  16-slot Priority_Array, Relinquish_Default, and range-validated
  WriteProperty.
- **F-ELEVATOR delta**: Elevator Group 1 "Maroon"'s `Landing_Call_Control` is
  now writable - `BACnetStack_RegisterCallbackSetElevatorGroupLandingCallControl`
  is registered (B-EM deliberately left it unregistered). A commanded landing
  call is recorded and read back through the same
  `GetListElevatorGroupLandingCallStatus` callback B-EM already registers.
- **DM-DDB-A**: this profile now initiates discovery. Reuses the existing
  `d` key (`KeyCommand::DiscoverRemote`, claimed by `BACnetProfileExample-B-LS-CPP`
  in `docs/menu-keys.md`) to broadcast a demo Who-Is on demand - no new
  `common/` key was needed.
- **F-TIMESYNC** (canonical pattern from `BACnetProfileExample-B-LD-CPP`,
  copied verbatim): DM-TS-B. `Local_Date`/`Local_Time` seeded from the host
  clock at start-up, updated by TimeSynchronization thereafter. Only
  `TimeSynchronization` is enabled, not `UTCTimeSynchronization` - the same
  choice B-LD makes (this profile allows either).
- **F-REINIT** (canonical pattern shared by B-AAC/B-ASC/B-LSC): DM-RD-B.
  ReinitializeDevice (COLDSTART/WARMSTART) is accepted and acted on from the
  main loop via `CASExampleHelper::RequestRestart`/`RestartDue`, after the
  SimpleAck has had time to reach the wire. COLDSTART restores every
  commanded/simulated value to its power-on state and re-announces with an
  I-Am.
- `docs/objects.json` extended for the three new output objects and the
  Elevator Group's newly-writable `Landing_Call_Control`; the generated
  "Objects and properties" README block regenerated (0 ⚠ rows).
- The series profile-table block and footprint placeholder in README.

### Fixed

- Binary Output 1 "Fuchsia" was initially missing its `Relinquish_Default`
  case in `GetPropertyEnumerated` (present for Analog and Multi-State Output,
  omitted for Binary Output while adapting B-SA's pattern). Caught by wire
  test, not by the zero-warning build: without it, both `Relinquish_Default`
  and `Present_Value` failed with `read-access-denied` on the wire, because
  the stack could not resolve a commandable object's `Present_Value` without
  a servable `Relinquish_Default`. Fixed before release.

### Notes

- Every BIBB this profile requires is implemented against the pinned stack;
  no `TODO.md` gap exists for a required capability.
- One item flagged, not faked: `Landing_Call_Control`'s WriteProperty path
  was code-reviewed against the stack's doc comment and the export was
  confirmed to exist at this pin, and the object builds/registers/runs
  correctly, but it was **not** independently wire-verified with a live
  client in this session - `BACnetLandingCallStatus`'s write-side
  SEQUENCE-CHOICE encoding could not be cleanly expressed through the
  test-client library available in this session. WritePropertyMultiple
  is enabled and reachable (a WPM APDU sent to the device returns a real
  BACnet reject/response rather than "unsupported service"), but a
  successful multi-property write was not completed end-to-end in this
  session for the same client-encoding reason - DS-WP-B (single-property
  WriteProperty, the code path WPM decomposes into) *was* fully verified for
  all three output types including out-of-range rejection, so the same
  per-property Set callbacks WPM calls are proven correct. Every other new
  capability (F-OUTPUTS single WriteProperty with range validation,
  TimeSynchronization, and ReinitializeDevice COLDSTART with power-on-state
  restore) **was** wire-verified against a running instance. See the PR
  description for the full verification list.
