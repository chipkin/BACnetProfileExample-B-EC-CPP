# AGENTS.md

Guidance for AI coding agents working in this repository. See
<https://agents.md/> for the format. Human contributors should read
[README.md](README.md) first, then [TUTORIAL.md](TUTORIAL.md).

## What this project is

A **tutorial** C++ example that implements the BACnet **B-EC (Elevator
Controller)** profile as fully as the standard CAS BACnet Stack supports. It
is one of a series - one git repo per BACnet profile. B-EC seeded from
[B-EM](https://github.com/chipkin/BACnetProfileExample-B-EM-CPP) (Elevator
Monitor, read-only) and adds writes back: DS-WP-B / DS-WPM-B on three
commandable outputs and the Elevator Group's `Landing_Call_Control`, DM-DDB-A
(discovery on demand), DM-TS-B (TimeSynchronization), and DM-RD-B
(ReinitializeDevice). Everything B-EM has (DS-RP-B / DS-RPM-B, COV/COV-Multiple,
intrinsic alarming, DM-DCC-B, the elevator object family) is unchanged. The
top priority is that the code reads like a tutorial a customer can learn from
and copy-paste. Favour clarity over cleverness.

## Layout

This repository is self-contained:

- `main.cpp` - the example device.
- `common/` - the shared helper (vendored).
- `README.md` - what this example is. Keep it short and about THIS example only.
- `TUTORIAL.md` - how to extend and review the example. Long-form material that
  would bloat the README belongs here.
- `docs/PICS.md` - the Protocol Implementation Conformance Statement. Its
  objects-and-properties section is GENERATED from `docs/objects.json`; do not
  hand-edit between the `OBJECTS-PROPERTIES` markers.
- `docs/objects.json` - the input to that generator. Update it in the same change
  as any `main.cpp` change that adds an object or a `GetProperty*` branch.
- `submodules/cas-bacnet-stack/` - the **CAS BACnet Stack** as a git submodule
  (private; compiled from source). After cloning, run
  `git submodule update --init --recursive`.

The `PROFILE-TABLE` block in README.md is also generated, from the example-series
repository's `docs/profile-table.md`. Edit it there, not here.

## Build

Plain CMake, identical on every platform, in the adapter's default SOURCE mode
(the stack's sources are compiled into the executable - no prebuilt library, no
DLL, no per-platform pre-step):

```bash
git submodule update --init --recursive   # once, if not cloned with --recursive
cmake -B build -S .
cmake --build build --config Release
```

The first build compiles the whole stack (~600 files) and takes a few minutes;
rebuilds after that are incremental and fast. Use `-D CAS_STACK_DIR=...` only if
your stack lives outside the bundled submodule. Do not reintroduce a link-mode
flag or a series-root build script into the documented build: a customer
downloads this repository on its own and must be able to build it with the two
commands above.

## Run

```bash
./build/BACnetExampleBEC [--port 47808] [--deviceID 389013]   # Linux/macOS
.\build\Release\BACnetExampleBEC.exe [--port 47808] [--deviceID 389013]   # Windows
```

Interactive keys while running: `h` help, `q` quit, up/down nudge Analog Input
1 (Bronze) - also the F-COVM demonstration - and `d` broadcasts a demo Who-Is
(DM-DDB-A). WriteProperty is exercised over the wire (no interactive key
commands a write - use a BACnet client).

## Conventions

- Device is named "Chipkin Example B-EC"; objects use the series' colour names; vendor id 389.
- **F-OUTPUTS is the canonical pattern from `BACnetProfileExample-B-SA-CPP`,
  copied verbatim** - the `Commandable` struct, `CommandWrite`/`CommandRelinquish`,
  `ReadPrioritySlot`, `GetCommandable`, `BACNET_PRIORITY_ARRAY_SIZE`, and the
  Set* callbacks (`SetPropertyReal`, `SetPropertyEnumerated`,
  `SetPropertyUnsignedInteger`, `SetPropertyNull`). If you extend this pattern
  to a new object type, walk EVERY Get callback branch for that type - see
  "the Relinquish_Default bug" below for what happens if you miss one.
- F-ELEVATOR: unchanged from B-EM's `AddElevatorGroupObject` /
  `AddLiftOrEscalatorObject` pattern - see B-EM's AGENTS.md for the full
  writeup. The one genuinely new piece:
  **`RegisterCallbackSetElevatorGroupLandingCallControl` IS registered here**
  (B-EM deliberately does not register it). The queued call is stored in
  `g_queuedLandingCall` and read back through
  `GetListElevatorGroupLandingCallStatus`, which now branches on
  `propertyIdentifier` (`Landing_Call_Control` vs `Landing_Calls`) - B-EM's
  read-only version ignored that parameter because it only ever answered
  `Landing_Calls`.
- F-TIMESYNC is the canonical pattern from `BACnetProfileExample-B-LD-CPP`,
  copied verbatim - `SyncedDateTime`, `InitSyncedDateTimeFromHost`,
  `SetSystemTime`, `GetPropertyDate`/`GetPropertyTime`. Only
  `SERVICE_TIME_SYNCHRONIZATION` is enabled, not the UTC variant - this
  profile allows either (DM-TS-B or DM-UTC-B); B-LD makes the same choice.
- F-REINIT is the pattern shared by B-AAC/B-ASC/B-LSC - `PasswordAccepted`,
  `ReinitializeDevice`, and the main-loop's deferred-restart block using
  `CASExampleHelper::RequestRestart`/`RestartDue`. **Never act on a restart
  inside the `ReinitializeDevice` callback itself** - the SimpleAck has not
  reached the wire yet at that point; always defer to the main loop.
- **The Relinquish_Default bug** (fixed before this repository's first
  release, kept here as a warning): when adapting B-SA's Get-callback pattern
  to a new commandable object, EVERY branch needs BOTH the `ReadPrioritySlot`
  case AND the `PROPERTY_IDENTIFIER_RELINQUISH_DEFAULT` case. Binary Output's
  `GetPropertyEnumerated` branch was written with the array-slot case and the
  `Polarity` case but the `Relinquish_Default` case was omitted - the build
  was clean (zero warnings) and `Present_Value` reads for the OTHER two
  outputs (Analog, Multi-State) worked fine, masking the bug until a wire
  test against Binary Output specifically returned `read-access-denied` on
  BOTH `Relinquish_Default` and `Present_Value` (the stack cannot resolve a
  commandable object's `Present_Value` from an all-null Priority_Array
  without a servable `Relinquish_Default`). When you copy this pattern again,
  diff every Get callback branch against B-SA's three (Real/Enumerated/
  UnsignedInteger), property by property, not just by eye.
- `docs/property-profile-reference.md`'s generated Lift table is **incomplete**
  relative to the required properties documented in
  `CASBACnetStackDLL.h`'s own comment above
  `BACnetStack_AddLiftOrEscalatorObject` (a documentation gap in the stack
  repo, unchanged from B-EM). Trust the DLL header's doc comment; `docs/objects.json`'s
  notes record exactly which properties this affects.
- F-COVM: unchanged from B-EM - `BACnetStack_SetPropertySubscribable` on two
  properties of Analog Input 1, plus `BACnetStack_SetCOVMultipleSettings`.
- Intrinsic alarming: unchanged from B-EM - see B-EM's AGENTS.md.
- DeviceCommunicationControl (DM-DCC-B): unchanged from B-EM. Shares
  `PasswordAccepted` with `ReinitializeDevice` in this repository (B-EM had
  its own inline password check since it had no `ReinitializeDevice`).
- Match the surrounding code style: `const`-correct parameters, check every stack
  return value, keep `main.cpp` linear and well-commented.
- **Never edit `common/` in this repo alone** - it is a vendored copy shared by
  every example in the series, with its own version (`COMMON_VERSION`) and
  changelog (`common/CHANGELOG.md`). To change it: edit, bump the version, add
  a changelog entry, then re-copy `common/` into every example repository.
  This repository needed **no** `common/` change - the `d` key
  (`KeyCommand::DiscoverRemote`) was already claimed by B-LS-CPP.

## How to verify a change

There are no unit tests; verification is behavioural:

1. Build, then run one instance on a clear UDP port.
2. With a BACnet client (e.g. the CAS BACnet Explorer, or `bacpypes3`/`BAC0`),
   send **Who-Is** and confirm **I-Am** from the device instance.
3. **ReadProperty** every required property of every object and confirm the
   values; confirm `Protocol_Revision` is 24 and `Object_List` lists all
   thirteen objects.
4. **F-OUTPUTS**: WriteProperty each output's `Present_Value` at a priority,
   confirm the readback; relinquish (WriteProperty NULL) and confirm it falls
   back to `Relinquish_Default`; write an out-of-range value to Binary/Multi-
   State Output and confirm `value-out-of-range`.
5. **F-ELEVATOR**: ReadProperty every Elevator Group / Lift / Escalator
   property (unchanged checklist from B-EM); WriteProperty a landing call to
   `Landing_Call_Control` and confirm it reads back (this specific write was
   NOT independently wire-verified during this repository's own
   implementation - see CHANGELOG.md - confirm it if you touch this code).
6. **DS-COVM-B / DS-COV-B**: unchanged from B-EM.
7. **Alarming**: unchanged from B-EM.
8. **DM-TS-B**: TimeSynchronization to an arbitrary date/time; confirm
   `Local_Date`/`Local_Time` read back the commanded value.
9. **DM-RD-B**: ReinitializeDevice COLDSTART; confirm a SimpleAck and that
   the commandable outputs/elevator state read back their power-on values
   afterward.
10. **DM-DDB-A**: press `d`; confirm a Who-Is broadcast on the wire.
11. **Device management**: unchanged from B-EM.
12. If you changed the objects or their properties, regenerate `docs/PICS.md`
    (`python tools/gen-objects-properties.py BACnetProfileExample-B-EC-CPP` from
    the series root) and confirm no row comes out flagged with ⚠.

Verification is manual (no in-repo test suite ships). During development
`bacpypes3` was used against a running instance on a clear `--port` (mind the
SO_REUSEADDR gotcha - kill stale instances first).

## Releasing

Bump `APP_VERSION` in `main.cpp` and add an entry to [CHANGELOG.md](CHANGELOG.md),
then tag `vX.Y.Z`. The GitHub Actions workflow builds and publishes the release.

## License

See [LICENSE](LICENSE). The CAS BACnet Stack is a separate, commercially
licensed product and is not covered by it.
