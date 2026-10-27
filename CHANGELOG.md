# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_No changes yet._

## [1.3.0] - 2026-10-27

Built on CAS BACnet Stack 6.x (`69b6249f`).

### Added

- **`--deviceName <text>`** sets the Device's Object_Name at start-up, like
  `--deviceID` sets its instance (ASHRAE 135-2024 cl. 12.1.1.3 and 12.1.1.4).
  Object_Name must be unique on the internetwork, so two units can now be
  installed together. The default is unchanged (`Chipkin Example B-EC`); a name
  must be 1 to 255 bytes with no control characters, otherwise a warning is
  printed and the default is kept. A WriteProperty of the Device's Object_Name
  is refused.
- **`--xml`** prints each received and sent frame as an XML block.

### Changed

- **Notification Class 1's Recipient_List is writable**, so a management
  station can point the alarms at itself. A written list lasts until the
  example restarts.
- **`--help` lists only the options the example reads.** It no longer lists
  `--dcc-password`; the DeviceCommunicationControl / ReinitializeDevice
  password is the `DCC_PASSWORD` constant in `main.cpp`.
- **ReinitializeDevice START_BACKUP / START_RESTORE** (not supported by this
  example) now returns Error (SERVICES, OPTIONAL_FUNCTIONALITY_NOT_SUPPORTED)
  instead of an Abort, as the standard requires.
- **Test scripts** under `tests/` default to this example's own port, 47833.
- Vendored `common/` updated to 3.5.0; see `common/CHANGELOG.md`.
- **Documentation**: the PICS lists the COV notifications the device
  initiates and the Elevator Group's optional properties, and now matches what
  the device serves (Lift required properties, `Property_List` on the Elevator
  Group, Lift, Escalator and Positive Integer Value). No behaviour change.

### Fixed

- **Notification Class 1's default Recipient_List entry** is now the standard
  default of ASHRAE 135-2024 cl. 12.21: local broadcast, Process Identifier 0,
  unconfirmed, all transitions. Alarms are still broadcast on the local subnet.
- **Analog Input 1 now has COV_Increment** (read-only, 1.0), as required by
  cl. 12.2 for an Analog Input that supports COV reporting.
- **PICS: Database_Revision** is documented as 13, the value the device
  actually reports.
- **Requests no longer go unanswered on Windows**: a request arriving just as
  a receive timed out could be silently discarded (vendored `common/` 3.4.1).
- **The Device's Description** read as an empty string because it was too long
  for the stack to hold; it is now shorter and reads correctly.

## [1.2.0] - 2026-10-16

Built on CAS BACnet Stack 6.x (`64b2cfac5`, 6.0.23).

This release makes the example Profile-functional for B-EC (ANSI/ASHRAE
135-2024 Annex L.13.2): a landing call written over BACnet now moves the car.
It also rolls up the earlier 1.0.1 through 1.1.0 work, which was never
released separately.

### Added

- **Lift car simulation** (`simulation/`, see README "What is Simulation"):
  floors 1 to 8, one floor every 2 seconds, door cycle, collective control, a
  door interlock, and a doorway that can be obstructed into
  `DOOR_CLOSING_FAULT`. The car moves only for landing calls.
- **Landing calls are served** (cl. 12.58.10): a write to Elevator Group 1's
  `Landing_Call_Control` enters `Landing_Calls` and the car's
  `Assigned_Landing_Calls`, sends the car, and clears when the car stops at the
  floor. A destination call becomes a car call to its destination. A call for
  a floor outside 1-8 is refused with an Error; a call while the car is
  faulted is accepted but served only after the car recovers.
- **Lift 1 presents the car**: `Car_Position`, `Car_Moving_Direction`,
  `Car_Door_Status`, `Fault_Signals` and `Landing_Door_Status` are live and
  subscribable. FAULT_LISTED is armed on `Fault_Signals` with `Reliability`
  enabled.
- **`Number_Of_APDU_Retries`** is 3 (cl. 12.11.29).
- **`s` key** presses and releases the car's passenger alarm button.
- **Automated self-tests** under `tests/`: object discovery, landing calls and
  their failure modes, passenger alarm and acknowledgement, output priority
  arbitration.

### Changed

- **Segmentation is supported** (`segmented-both`, 16 segments, 5000 ms
  segment timeout); `docs/PICS.md` updated.
- **Protocol_Revision** is 30.
- **The passenger alarm** is driven by the car's alarm button, not a 30-second
  timer.
- **ReinitializeDevice COLDSTART** also clears the landing calls and the car's
  stops.
- **Device renamed** from "Rainbow" to "Chipkin Example B-EC" so examples from
  this series can be told apart on one network.
- **Build** uses the stack's source mode by default
  (`cmake -B build -S .` then `cmake --build build --config Release`); no
  prebuilt static library step is needed.
- **Documentation** restructured into README, `TUTORIAL.md` and `docs/PICS.md`;
  the README now states what the example does and does not control.
- Application_Software_Version is 1.2.0.

### Fixed

- **Elevator Group 1 `Landing_Calls` and `Landing_Call_Control`** could not be
  read (read-access-denied). They now read as an empty list and floor 0,
  direction none, until a call is written.
- **`Application_Software_Version` and `Firmware_Revision`** were hard-coded
  and stale; they now follow the example and stack versions.

## [1.0.0] - 2026-09-15

Built on CAS BACnet Stack 6.x (`abd4cee1`, 6.0.21).

### Added

- **Initial B-EC (Elevator Controller) example**, an elevator monitor plus
  control: DS-RP-B, DS-RPM-B, DS-COV-B, DS-COVM-B, AE-N-I-B, AE-ACK-B,
  AE-INFO-B, DM-DDB-B, DM-DOB-B, DM-DCC-B, the base sensors, Network Port,
  the Elevator Group / Lift / Escalator family, Notification Class, and an
  intrinsic ChangeOfState alarm on the Lift's `Passenger_Alarm`.
- **Commandable outputs** (DS-WP-B, DS-WPM-B): Analog Output 1, Binary Output
  1 and Multi-State Output 1, each with a 16-slot Priority_Array,
  Relinquish_Default and range-checked WriteProperty.
- **Writable `Landing_Call_Control`** on Elevator Group 1.
- **Device discovery** (DM-DDB-A): the `d` key broadcasts a Who-Is.
- **Time synchronization** (DM-TS-B): local date and time start from the host
  clock and follow TimeSynchronization.
- **ReinitializeDevice** (DM-RD-B): COLDSTART and WARMSTART are accepted;
  COLDSTART restores power-on values and re-announces with an I-Am.
- README, `TUTORIAL.md` and `docs/PICS.md`.
