# Changelog

All notable changes to this project are documented in this file.

## [1.0.0] - unreleased

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
  available test-client library (`bacpypes3` 0.0.106). WritePropertyMultiple
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
