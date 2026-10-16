# BACnet B-EC (Elevator Controller) - C++ example

A tutorial example showing how to implement the BACnet **B-EC (Elevator
Controller)** device profile, in C++, using the
[CAS BACnet Stack](https://store.chipkin.com/services/stacks/bacnet-stack). It
answers **ReadProperty / ReadPropertyMultiple**, accepts **WriteProperty /
WritePropertyMultiple** to three commandable outputs and to the Elevator
Group's **landing-call control - and serves the call**: a lift car (a
[Simulation](#what-is-simulation)) travels to the floor, opens its door, and the
call clears. It supports **SubscribeCOV** and **SubscribeCOVPropertyMultiple**,
generates **intrinsic alarms** (an EventNotification when a passenger presses
the car's alarm button, and a fault notification when a car door fails to
close), accepts
**AcknowledgeAlarm** and answers **GetEventInformation**, handles
**DeviceCommunicationControl**, **initiates discovery** (Who-Is) on demand,
accepts **TimeSynchronization**, and accepts **ReinitializeDevice**.

**[Download a prebuilt binary](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP/releases)**
(Windows and Linux x64) - or build it yourself, see [Build](#build) below.

- **[TUTORIAL.md](TUTORIAL.md)** - how to extend this example and how to review
  it for conformance. Read it when you start turning this into your own device.
- **[docs/PICS.md](docs/PICS.md)** - the Protocol Implementation Conformance
  Statement: every object, every property, and who answers it.

> **Versions:** this document describes **example v1.2.0**, built and verified
> against **CAS BACnet Stack 6.0.23** (`6.x` @ `64b2cfac5`), at
> **Protocol_Revision 30**, with the vendored `common/` helper at **v3.4.0**.
> Running the example prints all three - if what it prints disagrees with this
> line, trust the program and check `CHANGELOG.md`.

> **Status: Profile-functional.** ANSI/ASHRAE 135-2024 L.13.2: "A B-EC device
> performs elevator control. It supports limited modification of its elevator
> objects by another device." A landing call written over BACnet is served by
> the car, a call it cannot serve is refused, a faulted car holds its calls
> until it recovers, and the [Wire Tests](#wire-tests) prove it against a
> Python-simulated landing-call panel - each check shown to fail with its
> feature removed. The three commandable outputs still drive nothing; they
> arbitrate priorities, and a Wire Test proves that too.

## The scenario: a landing call, answered

What a B-EC is for, in one sentence: **it runs the lift a building system
calls.** The Peer is whatever sends landing calls on a real site - a
destination-dispatch kiosk, a BMS, a security system calling the car to a
floor - or the Python client in [`tests/`](tests/README.md). It writes
Maroon's `Landing_Call_Control` (cl. 12.58.10: "A write to this property is
equivalent to a passenger pressing a call button at a landing, indicating
either desired direction of travel or destination floor"):

1. Someone at floor 6 presses DOWN: the Peer writes `{ floor 6, direction
   DOWN }`. `Landing_Call_Control` reads it back; Maroon's `Landing_Calls`
   (12.58.9: "a currently active call for the group of lifts") and the car's
   `Assigned_Landing_Calls` (12.59.11) list it.
2. The car locks its door (`SAFETY_LOCKED`), goes `UP` one floor at a time at
   its speed - `Car_Position` 2, 3, 4, 5, 6 - stops, and opens its door. The
   moment it stops at 6 the call leaves `Landing_Calls`.
3. A **destination call** `{ floor 3, destination 8 }`: the car goes down to 3,
   the landing call clears, the passenger's destination appears in
   `Registered_Car_Call`, and the car carries on to 8.
4. **Failure Mode - a floor the group does not serve.** The car serves floors
   1-8. A call for floor 9, floor 0, or a destination of 9 is **refused** with
   an Error; nothing registers and the car does not move.
5. **Failure Mode - a faulted car.** Something blocks the doorway at a stop:
   the door cannot close, the car raises `DOOR_CLOSING_FAULT` in
   `Fault_Signals` (cl. 12.59.32: "A door is failing to close"), the Lift's
   FAULT_LISTED algorithm takes it to `FAULT`, and the recipients get a
   to-fault notification. A landing call written now is **accepted** - the
   passenger pressed the button, it is in `Landing_Calls` - but **not
   assigned**: `Assigned_Landing_Calls` stays empty and the car stays where it
   is. Clear the doorway: the door closes, the fault clears, the call is
   assigned, and the car goes.

The passenger alarm (the `s` key) is reported exactly as in B-EM: a
CHANGE_OF_STATE alarm on `Passenger_Alarm`, listed by GetEventInformation and
acknowledged with AcknowledgeAlarm, with an ACK_NOTIFICATION to the recipients.
Every step is printed on the console as it happens.

### What is Simulation

The lift car is **Simulation**: `simulation/ElevatorCar.cpp` - the same file as
[B-EM](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP)'s - stands in
for the elevator a real B-EC drives over its own bus. It knows nothing about
BACnet. It serves floors 1-8, moves one floor every 2 s, opens its door for 1 s,
holds it 2 s, closes it for 1 s, runs its stops collectively, and only leaves a
floor with its door closed and locked. Unlike B-EM there are no simulated
passengers: the car moves only for the landing calls written to it.

Everything BACnet does with the car is real: the landing-call callback sends
it, the Lift's properties are read from it, every change goes to the stack
with `BACnetStack_UpdateValue` (which drives COV and both event algorithms).

The Wire Tests reach into the Simulation through a **test-only control
channel** (`simulation/SimulationControl.cpp`): a loopback-only UDP socket, off
unless `BEC_SIMULATION_CONTROL_PORT` names a port. It presses the alarm button,
blocks the doorway and speeds the car up for a test; landing calls always come
over BACnet. A second test-only variable, `BEC_TEST_EVENT_RECIPIENT_PORT`, adds
the test's workstation (127.0.0.1) to Notification Class 1 as a confirmed
recipient (`Recipient_List` is not writable in this profile). Neither is a
command-line option. Delete `simulation/` and drive your elevator instead.

## What is a B-EC (Elevator Controller) profile?

A **B-EC** (ANSI/ASHRAE 135, Annex L.13) is a **controller**: like a B-EM
(Elevator Monitor) it reports what an elevator installation - lifts,
escalators, the group that coordinates them - is doing, with COV and alarms,
but unlike a B-EM it also **accepts commands**: WriteProperty to a set of
outputs and a landing call on the Elevator Group, TimeSynchronization, and
ReinitializeDevice.

This example seeds from
[B-EM](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) (an Elevator
*Monitor*, read-only) and adds writes back: **F-OUTPUTS** (commandable
Analog/Binary/Multi-State Output, canonical pattern from
[B-SA-CPP](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP)),
**F-TIMESYNC** (canonical pattern from
[B-LD-CPP](https://github.com/chipkin/BACnetProfileExample-B-LD-CPP)), and
**F-REINIT** (the deferred-restart pattern shared by B-AAC/B-ASC/B-LSC).
**F-COVM** and **F-ELEVATOR** (the Elevator Group / Lift / Escalator object
family) are unchanged from B-EM, which remains their canonical source.

## The device this example creates

```
Device 389013  "Chipkin Example B-EC"   (Vendor 389 - Chipkin Automation Systems)
    ├── Analog Input  1            "Bronze"      read-only sensor (REAL, deg C); F-COVM demo (COV on 2 properties)
    ├── Binary Input  1            "Emerald"     read-only sensor (active/inactive)
    ├── Multi-State Input 1        "Hot Pink"    read-only sensor (state 1..3)
    ├── Analog Output 1            "Chartreuse"  REAL setpoint; commandable (F-OUTPUTS)
    ├── Binary Output 1            "Fuchsia"     active/inactive; commandable
    ├── Multi-State Output 1       "Indigo"      state 1..3; commandable
    ├── Network Port 1             "Vermilion"   the BACnet/IP port (required)
    ├── Elevator Group 1           "Maroon"      groups Mauve; F-ELEVATOR; Landing_Call_Control writable - the car serves the call
    ├── Lift 1                     "Mauve"       the (simulated) car: position, direction, door; CHANGE_OF_STATE on Passenger_Alarm, FAULT_LISTED on Fault_Signals
    ├── Escalator 1                "Mint"        not grouped (escalators aren't lifts)
    ├── Positive Integer Value 1   "Turquoise"   Maroon's Machine_Room_ID target (added before Maroon)
    └── Notification Class 1       "Crimson"     routes Mauve's alarm and fault events
```

Object names follow the series' colour convention (Device is always
"Chipkin Example B-EC"). Every required property of every object, and who answers it, is in
[docs/PICS.md](docs/PICS.md).

## What this example supports

### BIBBs (BACnet Interoperability Building Blocks)

| BIBB | Description | Supported |
|------|-------------|:---------:|
| DS-RP-B | Data Sharing - ReadProperty - B | ✅ |
| DS-RPM-B | Data Sharing - ReadPropertyMultiple - B | ✅ |
| DS-WP-B | Data Sharing - WriteProperty - B | ✅ (F-OUTPUTS + Elevator Group's Landing_Call_Control) |
| DS-WPM-B | Data Sharing - WritePropertyMultiple - B | ✅ |
| DS-COV-B | Data Sharing - COV - B | ✅ |
| DS-COVM-B | Data Sharing - COV-Multiple - B | ✅ (unchanged from B-EM) |
| AE-N-I-B | Alarm and Event - Notification Internal - B | ✅ (intrinsic ChangeOfState on the Lift's Passenger_Alarm) |
| AE-ACK-B | Alarm and Event - ACK - B | ✅ |
| AE-INFO-B | Alarm and Event - Information - B | ✅ |
| DM-DDB-A | Device Management - Dynamic Device Binding - A | ✅ (on demand - the `d` key) |
| DM-DDB-B | Device Management - Dynamic Device Binding - B | ✅ |
| DM-DOB-B | Device Management - Dynamic Object Binding - B | ✅ |
| DM-DCC-B | Device Management - DeviceCommunicationControl - B | ✅ |
| DM-TS-B | Device Management - TimeSynchronization - B | ✅ (local time only, same choice B-LD makes) |
| DM-RD-B | Device Management - ReinitializeDevice - B | ✅ (COLDSTART and WARMSTART) |

No other BIBBs are supported - in particular AE-CRL-B (the Notification
Class's `Recipient_List` is not writable here) and DM-UTC-B (this example
synchronizes local time only).

### Services (executed / B-side, plus what this device initiates)

| Service | Notes |
|---------|-------|
| ReadProperty / ReadPropertyMultiple | Responds to property reads (DS-RP-B / DS-RPM-B). |
| WriteProperty / WritePropertyMultiple | Accepts writes to the three outputs' `Present_Value` and the Elevator Group's `Landing_Call_Control` (DS-WP-B / DS-WPM-B). |
| SubscribeCOV / SubscribeCOVPropertyMultiple | Analog Input 1 (Bronze) is subscribable on `Present_Value` and `Status_Flags`. |
| ConfirmedEventNotification / UnconfirmedEventNotification | Sent when the Lift's intrinsic ChangeOfState algorithm transitions (AE-N-I-B). |
| AcknowledgeAlarm | Accepts an operator's acknowledgement of the Lift's alarm (AE-ACK-B). |
| GetEventInformation | Answers with the Lift's current event state (AE-INFO-B). |
| Who-Is / I-Am | Answers Who-Is with I-Am, and broadcasts an I-Am on start-up; also **initiates** a Who-Is on demand (press `d`) (DM-DDB-A/B). |
| Who-Has / I-Have | Answers Who-Has with I-Have (DM-DOB-B). |
| DeviceCommunicationControl | Accepts an optional password-protected enable/disable-initiation request (DM-DCC-B). |
| TimeSynchronization | Updates `Local_Date`/`Local_Time` from the request (DM-TS-B). |
| ReinitializeDevice | Accepts COLDSTART/WARMSTART, deferred until the SimpleACK reaches the wire (DM-RD-B). |

### Object types

| Object type | Instance | Name |
|-------------|:--------:|------|
| Device | 389013 | Chipkin Example B-EC |
| Analog Input | 1 | Bronze |
| Binary Input | 1 | Emerald |
| Multi-State Input | 1 | Hot Pink |
| Analog Output | 1 | Chartreuse |
| Binary Output | 1 | Fuchsia |
| Multi-State Output | 1 | Indigo |
| Network Port | 1 | Vermilion |
| Elevator Group | 1 | Maroon |
| Lift | 1 | Mauve |
| Escalator | 1 | Mint |
| Positive Integer Value | 1 | Turquoise |
| Notification Class | 1 | Crimson |

## Requires the CAS BACnet Stack (licensed product)

This example **builds against the CAS BACnet Stack, which is a commercial Chipkin
product** - it is not free or open source, and there is no public/trial build.
The stack is referenced here as the **private** git submodule
`submodules/cas-bacnet-stack`; you can only fetch and build it once you have a CAS
BACnet Stack license and access to that repository.

**To get the CAS BACnet Stack (and access to build this example), contact
Chipkin:** <https://store.chipkin.com/services/stacks/bacnet-stack> or
sales@chipkin.com.

You do not need a stack licence to *read* this example, or to run a
[prebuilt release binary](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP/releases).
The licence is what lets you *build* it - that is the part the stack submodule
gates.

## What's in this repository

This is a **self-contained** project. It ships:

- `main.cpp` - the example device.
- `common/` - the shared helper (UDP, callbacks, CLI, keyboard) vendored in.
- `CMakeLists.txt` - the build, the same on Windows, Linux, and macOS.
- `docs/PICS.md` - the conformance statement.
- `tests/` - the Wire Tests (see [Wire Tests](#wire-tests)), and `wiretest/`, the
  series' shared Python harness they are written against (vendored, like `common/`).
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack as a git submodule**
  (private; requires a license - see above). Its sources are compiled into the
  executable, so there is no library or DLL to build, ship, or install.

## Prerequisites

- A C++17 compiler (MSVC, GCC, or Clang).
- CMake >= 3.15.
- Git (to fetch the stack submodule).

### Windows

- **C++ compiler** - install
  [Visual Studio Community](https://visualstudio.microsoft.com/downloads/)
  (free) and select the **"Desktop development with C++"** workload.
- **CMake** - from <https://cmake.org/download/>, or `winget install Kitware.CMake`.

### Linux / macOS

- Debian/Ubuntu: `sudo apt install build-essential cmake git`
- macOS: `xcode-select --install` and `brew install cmake`

## Build

CMake only, and the same two commands on every platform:

```bash
git clone --recursive https://github.com/chipkin/BACnetProfileExample-B-EC-CPP.git
cd BACnetProfileExample-B-EC-CPP

cmake -B build -S .
cmake --build build --config Release
```

Already cloned without `--recursive`? Run `git submodule update --init --recursive`
first - the build needs the stack submodule.

> **The first build takes a few minutes** - it compiles the entire CAS BACnet
> Stack (~600 source files) into the executable. Rebuilds after that are
> incremental and take seconds.

If your CAS BACnet Stack lives somewhere other than the bundled submodule, point
CMake at it: `cmake -B build -S . -D CAS_STACK_DIR=/path/to/cas-bacnet-stack`.

## Run

```bash
# Linux / macOS
./build/BACnetExampleBEC

# Windows
.\build\Release\BACnetExampleBEC.exe
```

Expected output:

```
BACnet B-EC (Elevator Controller) Example - C++ v1.1.0
CAS BACnet Stack version: 6.0.23.0
Common helper (common/) version: 3.4.0
FYI: Listening for BACnet/IP on UDP port 47808 (Network Port 1).
TX 21 bytes to 192.168.3.255:47808 (broadcast) (Network Port 1)
FYI: Device 389013 ("Chipkin Example B-EC") ready. Vendor ID 389. Accepts WriteProperty to Chartreuse/Fuchsia/Indigo and Landing_Call_Control on Maroon. Press 'd' to broadcast a demo Who-Is (DM-DDB-A), or 'h' for help.
```

The `TX` line is the start-up I-Am the device broadcasts to announce itself. It
goes to the **local subnet broadcast** address (here `192.168.3.255`, computed
from the Network Port's interface), not the global `255.255.255.255`. As
clients talk to the device you'll see `RX ... bytes from ...` and `TX ... bytes
to ...` lines showing the traffic.

The device listens on UDP **47808** (BACnet/IP). Allow that port through your
firewall. To use a different port, pass `--port` (see below).

> **A wall of red `Error:` lines at start-up is expected and is not your bug** -
> it is the stack's own debug logging (the device hearing its own broadcast I-Am,
> and a one-time BACnet/SC UUID notice). [TUTORIAL.md](TUTORIAL.md#troubleshooting)
> explains both.

### Command-line options

| Option | Default | Meaning |
|--------|---------|---------|
| `--port <n>` | `47808` | UDP port to listen on (BACnet/IP). |
| `--deviceID <n>` | `389013` | The device's BACnet instance number (BACnet requires this to be configurable). |
| `--help`, `-h` | - | Show usage and exit. |
| `--version` | - | Print the example, stack, and `common/` helper versions, then exit. |

### Interactive commands

While the example runs, these keys are available:

| Key | Action |
|-----|--------|
| `h` | Show the version information and this command list. |
| `q` | Quit. |
| up arrow | Increase Analog Input 1 (`Bronze`) by 1.1 (also the F-COVM demonstration). |
| down arrow | Decrease Analog Input 1 (`Bronze`) by 1.1. |
| `d` | Broadcast a demo Who-Is (DM-DDB-A). |
| `s` | Simulation: press (or release) the car's passenger alarm button. |

Landing calls and every other write are exercised over the wire; there is no
interactive key that commands one - use a BACnet client. The console prints
each floor the car reaches and each call it serves.

## Verify

Use a BACnet client such as the
[**CAS BACnet Explorer**](https://store.chipkin.com/products/tools/cas-bacnet-explorer):

1. **Discover** - send a **Who-Is**. The device replies with **I-Am** from
   instance **389013** (vendor **389**). It also broadcasts an I-Am at
   start-up.
2. **Browse the object model** - the device shows thirteen objects: the Device
   (`Chipkin Example B-EC`), the three read-only sensors, the three commandable outputs,
   the Network Port (`Vermilion`), the Elevator Group/Lift/Escalator family,
   the Positive Integer Value, and the Notification Class. Reading the
   Device's `Object_List` returns all thirteen; `Protocol_Revision` = 30.
3. **F-OUTPUTS** - WriteProperty Chartreuse's `Present_Value` at a priority,
   confirm the readback, relinquish (WriteProperty NULL), confirm it falls
   back to `Relinquish_Default` (20.0). WriteProperty Fuchsia to `active`,
   confirm the readback. WriteProperty Indigo to state 2, confirm the
   readback; write Indigo to an out-of-range state (9) and confirm
   `value-out-of-range`.
4. **F-COVM** - SubscribeCOVPropertyMultiple naming Analog Input 1 (Bronze)'s
   `Present_Value` AND `Status_Flags`. A plain SubscribeCOV also still works.
5. **F-ELEVATOR** - ReadProperty every required property of Maroon/Mauve/Mint;
   WriteProperty a landing call to Maroon's `Landing_Call_Control` (before any
   write it reads floor 0, direction `none`), e.g. floor 6, direction down
   (`09 06 19 04`). Watch `Landing_Calls`, then Mauve's `Car_Position` climb to
   6 and the call clear. A call for floor 9 is refused.
6. **DM-TS-B** - TimeSynchronization to an arbitrary date/time; confirm
   `Local_Date`/`Local_Time` read back the commanded value.
7. **DM-RD-B** - ReinitializeDevice COLDSTART; confirm a SimpleAck and that
   the commandable outputs read back their `Relinquish_Default` afterward.
8. **DM-DDB-A** - press `d`; confirm a Who-Is broadcast on the wire.
9. **Confirm the profile boundary** - a WriteProperty to `Recipient_List` on
   the Notification Class (Crimson) is rejected: AE-CRL-B is not a required
   BIBB for this profile.

**What has been checked on the wire, and how.** The Wire Tests below cover
steps 1-3 and 5 (and the alarm), in CI. Steps 4 (Bronze's COV), 6-9 were
checked by hand in earlier sessions and are not yet reproducible from this
repository.

For a property-by-property review against the conformance statement, see
[TUTORIAL.md](TUTORIAL.md).

## Wire Tests

The scenario above, automated. Python clients - the Peers: a landing-call
panel, an operator workstation that is also Crimson's event recipient, a COV
subscriber - drive the running example over BACnet/IP from outside it. The
landing calls are raw-encoded BACnetLandingCallStatus values
(`wiretest.services.landing_call_status`). Python 3 standard library only:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBEC          # Linux/macOS
python tests\run_wire_tests.py --exe build\Release\BACnetExampleBEC.exe   # Windows
```

| Script | Proves |
|---|---|
| `discovery_test.py` | every object and every property it lists reads as a value |
| `landing_call_test.py` | the Profile Function: a landing call (direction, then destination) is served - the car travels, opens, the call clears |
| `landing_call_failure_test.py` | Failure Modes: unserved floors refused; a faulted car (`DOOR_CLOSING_FAULT`, FAULT_LISTED) holds its calls unassigned, then serves them |
| `passenger_alarm_test.py` | the passenger alarm reported, listed, acknowledged (with ACK_NOTIFICATION); the car's status refuses writes |
| `outputs_test.py` | the commandable outputs arbitrate priorities; an out-of-range state is refused |

It ends with `ALL WIRE TESTS PASSED` (exit 0), in about a minute and a half.
Ports: `--port` (default 48035) and `--port + 1` for the control channel. CI
runs it on Linux after the smoke test. [tests/README.md](tests/README.md) says
what each check proves and which mutation of `main.cpp` makes it fail. Time
synchronization and restart are not yet covered.


## The BACnet profile example series

<!-- PROFILE-TABLE:BEGIN (generated from cas-bacnet-stack-examples/docs/profile-table.md - do not edit here) -->
There is one example repository per standardized device profile in ASHRAE 135-2024 Annex L. An example marked ⛔ is blocked: the stack cannot yet perform that profile's function through its customer interface, and the example's README says what it does today. Pick the profile your device claims, then the language you build in. "Ask" means the example hasn't been built yet for that language - [contact Chipkin](https://store.chipkin.com/contact-us) if you need one.

### Controllers (Annex L.4)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-SS** Smart Sensor | [B-SS-CPP](https://github.com/chipkin/BACnetProfileExample-B-SS-CPP) | [B-SS-Node](https://github.com/chipkin/BACnetProfileExample-B-SS-Node) | [B-SS-CS](https://github.com/chipkin/BACnetProfileExample-B-SS-CS) | [B-SS-Rust](https://github.com/chipkin/BACnetProfileExample-B-SS-Rust) | [B-SS-Python](https://github.com/chipkin/BACnetProfileExample-B-SS-Python) | [B-SS-Go](https://github.com/chipkin/BACnetProfileExample-B-SS-Go) |
| **B-SA** Smart Actuator | [B-SA-CPP](https://github.com/chipkin/BACnetProfileExample-B-SA-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ASC** Application Specific Controller | [B-ASC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ASC-CPP) | [B-ASC-Node](https://github.com/chipkin/BACnetProfileExample-B-ASC-Node) | Ask | Ask | Ask | Ask |
| **B-AAC** Advanced Application Controller | [B-AAC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AAC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-BC** Building Controller | [B-BC-CPP](https://github.com/chipkin/BACnetProfileExample-B-BC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Life safety controllers (Annex L.5)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LSC** Life Safety Controller | [B-LSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-LSC-CPP) 🚧 | Ask | Ask | Ask | Ask | Ask |
| **B-ALSC** Advanced Life Safety Controller | [B-ALSC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ALSC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Access control controllers (Annex L.6)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-ACC** Access Control Controller | [B-ACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACC-CPP) ⛔ blocked on [stack #2150](https://github.com/chipkin/cas-bacnet-stack/issues/2150), [#2044](https://github.com/chipkin/cas-bacnet-stack/issues/2044) | Ask | Ask | Ask | Ask | Ask |
| **B-AACC** Advanced Access Control Controller | [B-AACC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AACC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Lighting controllers (Annex L.11)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-LD** Lighting Device | [B-LD-CPP](https://github.com/chipkin/BACnetProfileExample-B-LD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-LS** Lighting Supervisor | [B-LS-CPP](https://github.com/chipkin/BACnetProfileExample-B-LS-CPP) | Ask | Ask | Ask | Ask | Ask |

### Elevator controllers (Annex L.13)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-EM** Elevator Monitor | [B-EM-CPP](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-EC** Elevator Controller | [B-EC-CPP](https://github.com/chipkin/BACnetProfileExample-B-EC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-AEC** Advanced Elevator Controller | [B-AEC-CPP](https://github.com/chipkin/BACnetProfileExample-B-AEC-CPP) | Ask | Ask | Ask | Ask | Ask |

### Authentication and authorization (Annex L.14)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-AS** Authorization Server | [B-AS-CPP](https://github.com/chipkin/BACnetProfileExample-B-AS-CPP) ⛔ blocked on [stack #2043](https://github.com/chipkin/cas-bacnet-stack/issues/2043) | Ask | Ask | Ask | Ask | Ask |

### Miscellaneous (Annex L.7, combinable with any one family)

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-BBMD** Broadcast Management Device | [B-BBMD-CPP](https://github.com/chipkin/BACnetProfileExample-B-BBMD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACDC** Access Control Door Controller | [B-ACDC-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACDC-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-ACCR** Access Control Credential Reader | [B-ACCR-CPP](https://github.com/chipkin/BACnetProfileExample-B-ACCR-CPP) ⛔ blocked on [stack #3934](https://github.com/chipkin/cas-bacnet-stack/issues/3934) | Ask | Ask | Ask | Ask | Ask |
| **B-RTR** Router | [B-RTR-CPP](https://github.com/chipkin/BACnetProfileExample-B-RTR-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GW** Gateway | [B-GW-CPP](https://github.com/chipkin/BACnetProfileExample-B-GW-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-DAP** Device Address Proxy | [B-DAP-CPP](https://github.com/chipkin/BACnetProfileExample-B-DAP-CPP) ⛔ blocked on [stack #2032](https://github.com/chipkin/cas-bacnet-stack/issues/2032) | Ask | Ask | Ask | Ask | Ask |
| **B-SCHUB** BACnet/SC Hub | [B-SCHUB-CPP](https://github.com/chipkin/BACnetProfileExample-B-SCHUB-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-GENERAL** General device (Annex L.8) | *(satisfied by every example above)* | — | — | — | — | — |

### Operator interfaces and workstations (Annex L.1–L.3, L.9–L.10, L.12)

Client-side profiles.

| Profile | C++ | Node.js | C# | Rust | Python | Go |
|---|---|---|---|---|---|---|
| **B-OD** Operator Display | [B-OD-CPP](https://github.com/chipkin/BACnetProfileExample-B-OD-CPP) | Ask | Ask | Ask | Ask | Ask |
| **B-OWS** Operator Workstation | planned | — | — | — | — | — |
| **B-AWS** Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-XAWS** Extended Advanced Operator Workstation | planned | — | — | — | — | — |
| **B-LSAP** Life Safety Annunciator Panel | planned | — | — | — | — | — |
| **B-LSWS** Life Safety Workstation | planned | — | — | — | — | — |
| **B-ALSWS** Advanced Life Safety Workstation | planned | — | — | — | — | — |
| **B-ACSD** Access Control Security Display | planned | — | — | — | — | — |
| **B-ACWS** Access Control Workstation | planned | — | — | — | — | — |
| **B-AACWS** Advanced Access Control Workstation | planned | — | — | — | — | — |
| **B-LOD** Lighting Operator Display | planned | — | — | — | — | — |
| **B-ALWS** Advanced Lighting Workstation | planned | — | — | — | — | — |
| **B-LCS** Lighting Control Station | planned | — | — | — | — | — |
| **B-ALCS** Advanced Lighting Control Station | planned | — | — | — | — | — |
| **B-ED** Elevator Display | planned | — | — | — | — | — |
| **B-EWS** Elevator Workstation | planned | — | — | — | — | — |
| **B-AEWS** Advanced Elevator Workstation | planned | — | — | — | — | — |

🚧 = in progress. ⛔ = Blocked Example (blocked on the named stack gap). "Ask" = not yet built for that language; contact Chipkin if you need it. Profile definitions: ANSI/ASHRAE 135-2024 Annex L. BIBB definitions: Annex K. Get the stack: <https://store.chipkin.com/services/stacks/bacnet-stack>.
<!-- PROFILE-TABLE:END -->

## References

- **ANSI/ASHRAE 135** (BACnet) - the protocol standard. Object model
  (Clause 12), alarming/events (Clause 13), services (Clause 15), BACnet/IP
  (Annex J), device profiles (Annex L).
- **What is BACnet?** - Chipkin's introduction:
  <https://docs.chipkin.com/protocols/bacnet/>.
- **CAS BACnet Stack** - product page and documentation:
  <https://store.chipkin.com/services/stacks/bacnet-stack>.
- **CAS BACnet Explorer** - client for testing this device:
  <https://store.chipkin.com/products/tools/cas-bacnet-explorer>.
- **B-EM example** (the read-only seed this repository extends) -
  <https://github.com/chipkin/BACnetProfileExample-B-EM-CPP>.
- **B-SA example** (the F-OUTPUTS pattern this reuses) -
  <https://github.com/chipkin/BACnetProfileExample-B-SA-CPP>.
- **B-LD example** (the F-TIMESYNC pattern this reuses) -
  <https://github.com/chipkin/BACnetProfileExample-B-LD-CPP>.
- **Shared helper used by this example** - [`common/README.md`](common/README.md).

See also [TUTORIAL.md](TUTORIAL.md), [docs/PICS.md](docs/PICS.md),
[CHANGELOG.md](CHANGELOG.md), and [AGENTS.md](AGENTS.md).
