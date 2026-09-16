# Tutorial - extending and reviewing the B-EC example

[README.md](README.md) says what this example *is*. This document is the *how*:
how to extend it into your own controller, what each object type needs the
application to serve, how to review the result for conformance, and what goes
wrong when you get it subtly right.

Read this once before you start changing `main.cpp`. The most expensive
mistake in this example is silent, and it already bit this repository once -
see [The Relinquish_Default bug](#the-relinquish_default-bug-a-real-defect-caught-by-wire-testing).

- [Extending the example](#extending-the-example)
- [What each object type needs you to serve](#what-each-object-type-needs-you-to-serve)
- [Who serves what: a representative object](#who-serves-what-a-representative-object)
- [The Relinquish_Default bug](#the-relinquish_default-bug-a-real-defect-caught-by-wire-testing)
- [Reviewing your device](#reviewing-your-device)
- [Troubleshooting](#troubleshooting)

## Extending the example

The example is intentionally as small as a controller with this many BIBBs can
be - it separates cleanly into a few named feature blocks (see `main.cpp`'s
file header and `AGENTS.md`'s Conventions section):

- **F-OUTPUTS** - three commandable outputs, the canonical pattern copied
  verbatim from `BACnetProfileExample-B-SA-CPP`: the `Commandable` struct,
  `CommandWrite`/`CommandRelinquish`, `ReadPrioritySlot`, `GetCommandable`,
  and the `SetProperty*` callbacks.
- **F-ELEVATOR** - the Elevator Group / Lift / Escalator object family,
  unchanged from `BACnetProfileExample-B-EM-CPP`, except that
  `BACnetStack_RegisterCallbackSetElevatorGroupLandingCallControl` is now
  registered so `Landing_Call_Control` is writable.
- **F-TIMESYNC** - TimeSynchronization, the canonical pattern copied verbatim
  from `BACnetProfileExample-B-LD-CPP`.
- **F-REINIT** - ReinitializeDevice with a deferred (post-ACK) restart, the
  pattern shared by B-AAC/B-ASC/B-LSC.

**Change a sensor's value or name** - edit the constants / callbacks in
`main.cpp` (e.g. the initial value of `g_analogInput1Value`, or the `"Bronze"`
string in `GetPropertyCharString`).

**Change the device identity before you ship** - vendor ID, vendor name, model
name, description, firmware revision, device name and the DCC/ReinitializeDevice
password are all in the `CHANGE ALL OF THIS BEFORE YOU SHIP` block at the top of
`main.cpp`, with a per-field note on each saying what to change it to. That
block is the authoritative checklist; it is in the source rather than here so
it cannot be skipped by someone who only reads the code.

**Adding a fourth commandable output, or a new elevator object** - walk every
`Get*`/`Set*` callback branch for that object type, one at a time, against a
working object of the same type (B-SA's Real/Enumerated/UnsignedInteger three
for a new output; the Lift/Escalator callbacks for a new elevator object).
Then **read back every required property of the new object and diff it against
a working one**. A half-added object is not caught by "it scanned OK" - see
below for exactly why, and for the real bug this mistake already caused here.

> **Why falling through a callback is SILENT.**
> Most `GetProperty*` callbacks match on **both** object type *and* instance,
> so a new instance falls through every one of them. The stack errors only for
> the handful of properties it refuses to invent - on this device that is
> `Present_Value`, `Number_Of_States`, `Relinquish_Default`, `Local_Date`,
> `Local_Time`, a Network Port's `APDU_Length`, and (elevator-specific)
> `Car_Position`, `Car_Moving_Direction`, `Car_Door_Status`, `Passenger_Alarm`
> and `Operation_Direction`. For everything else it **silently substitutes a
> default**:
>
> | Property | If you forget to serve it | Loud? |
> |---|---|:--:|
> | `Present_Value` (input/output) | Error (`read-access-denied`) | yes |
> | `Car_Position`, `Passenger_Alarm`, etc. | Error (`value-not-initialized`) | yes |
> | `Object_Name` | reads back as the string **`"undefined"`** | **no** |
> | `Units` | reads back as **`no-units` (95)** | **no** |
> | `Out_Of_Service` | served on type alone for most objects - works by accident | n/a |
>
> It is worse than "wrong value": the object's `Property_List` **still
> advertises the property**. So the object actively claims to have it, and
> then answers with a default. Nothing on the wire says you forgot anything -
> **"it scanned OK" is exactly the failure mode, not evidence against it.**
> Set the `errorCode` out-parameter only where *this device* knows the read is
> wrong (this file does it for `State_Text` with an out-of-range index, and for
> the out-of-range WriteProperty checks in the `SetProperty*` callbacks) -
> naming an error on the catch-all breaks the properties the stack is supposed
> to answer for you (the Device's `Max_APDU_Length_Accepted` among them).

## What each object type needs you to serve

The application must serve every REQUIRED property the stack does not
generate. It differs per type - this is the checklist, so you do not have to
infer it:

| Object type | You must serve | Plus |
|---|---|---|
| Analog Input | `Present_Value` (Real), `Object_Name`, `Units` | - |
| Binary Input | `Present_Value` (Enumerated), `Object_Name` | `Polarity` |
| Multi-state Input | `Present_Value` (Unsigned), `Object_Name` | `Number_Of_States` |
| Analog Output | `Object_Name`, `Units`, `Priority_Array` slots, `Relinquish_Default` | commandable `Present_Value` |
| Binary Output | `Object_Name`, `Polarity`, `Priority_Array` slots, `Relinquish_Default` | commandable `Present_Value`, range-check the write |
| Multi-state Output | `Object_Name`, `Number_Of_States`, `Priority_Array` slots, `Relinquish_Default` | commandable `Present_Value`, range-check the write |
| Network Port | `Object_Name`, `Out_Of_Service`, `Network_Type`, `Protocol_Level`, `Changes_Pending`, IP octet strings | - |
| Elevator Group | `Object_Name` | the four F-ELEVATOR list/sequence callbacks; `SetElevatorGroupLandingCallControl` for the write side |
| Lift | `Object_Name`, `Car_Position`, `Car_Moving_Direction`, `Car_Door_Status`, `Passenger_Alarm`, `Out_Of_Service`, `Fault_Signals` | the alarm's intrinsic ChangeOfState algorithm |
| Escalator | `Object_Name`, `Operation_Direction`, `Passenger_Alarm`, `Out_Of_Service` | - |
| Positive Integer Value | `Present_Value`, `Object_Name` | must exist before `AddElevatorGroupObject` |
| Notification Class | `Object_Name` | seeded via `AddNotificationClassObject`/`AddRecipientToNotificationClass`, not a `Get` callback |

## Who serves what: a representative object

The single most common question when reading this file is "who answers this
property?" For **Analog Output 1 ("Chartreuse")** - one of the two genuinely
new object shapes in this profile (the other is the Elevator Group's write
path) - the whole picture:

| Property | Served by | How |
|---|---|---|
| `Object_Identifier` | **stack** | generated from the object you added |
| `Object_Type` | **stack** | generated |
| `Property_List` | **stack** | generated |
| `Status_Flags` | **stack** | generated |
| `Event_State` | **stack**, sort of | no intrinsic alarming on this object, so nothing serves it - it reads `normal` only because that is the enumeration's zero value and the stack substitutes a datatype default |
| `Out_Of_Service` | **you** | `GetPropertyBool` - matched on object type only |
| `Object_Name` | **you** | `GetPropertyCharString` |
| `Units` | **you** | `GetPropertyEnumerated` |
| `Present_Value` | **stack**, computed | resolved from the highest-priority non-null `Priority_Array` slot, or `Relinquish_Default` if all are null |
| `Priority_Array` | **you**, per slot | `GetPropertyReal` (is-slot-set query is `GetPropertyBool`) answers each of the 16 array indices |
| `Relinquish_Default` | **you** | `GetPropertyReal` |
| `Current_Command_Priority` | **stack** | computed from the `Priority_Array` |
| WriteProperty of `Present_Value` | **you** | `SetPropertyReal` stores the value at the written priority; `SetPropertyNull` relinquishes a slot |

Every object, not just this one, is in [docs/PICS.md](docs/PICS.md).

## The Relinquish_Default bug (a real defect, caught by wire testing)

This is not a hypothetical - it happened during this repository's own
implementation, and it is the sharpest illustration of the silent-failure
pattern above. Adapting B-SA's Get-callback pattern to a new commandable
object needs BOTH the `ReadPrioritySlot` case AND the
`PROPERTY_IDENTIFIER_RELINQUISH_DEFAULT` case in **every** branch. Binary
Output 1 ("Fuchsia")'s `GetPropertyEnumerated` branch was written with the
array-slot case and the `Polarity` case, but the `Relinquish_Default` case was
initially **omitted**.

The build was clean - zero warnings - and `Present_Value` reads for the other
two outputs (Analog, Multi-State) worked fine, masking the bug until a wire
test against Binary Output specifically returned `read-access-denied` on
**both** `Relinquish_Default` **and** `Present_Value`: the stack cannot resolve
a commandable object's `Present_Value` from an all-null `Priority_Array`
without a servable `Relinquish_Default`. It was fixed before this
repository's first release (see `CHANGELOG.md`'s `[1.0.0]` entry, "Fixed").

**The lesson, stated plainly: when you copy this pattern again, diff every
`Get` callback branch against B-SA's three (Real/Enumerated/UnsignedInteger)
property by property, not just by eye.** A zero-warning build proves nothing
about which properties a new branch actually serves.

## Reviewing your device

After you have changed anything, review it against the conformance statement
rather than against "it looked fine in the explorer":

1. Regenerate [docs/PICS.md](docs/PICS.md) after editing `docs/objects.json`
   (see [Keeping the PICS honest](#keeping-the-pics-honest) below). A ⚠ row is
   a required property nothing serves.
2. Read **every** property listed for **every** object with a BACnet client,
   and compare the value against the PICS. `"undefined"`, `no-units`, `0`, and
   `value-not-initialized`/`read-access-denied` are the shapes a missed
   callback takes.
3. Diff a new object of a type against the existing one of that type. Anything
   that differs and shouldn't is a callback that matched on instance.
4. **F-OUTPUTS**: WriteProperty each output's `Present_Value` at a priority,
   confirm the readback; relinquish (WriteProperty NULL) and confirm it falls
   back to `Relinquish_Default`; write an out-of-range value to Binary Output
   (anything but 0/1) or Multi-State Output (0 or >3) and confirm
   `value-out-of-range`.
5. **F-ELEVATOR**: WriteProperty a landing call to `Landing_Call_Control` and
   confirm it reads back through `GetListElevatorGroupLandingCallStatus`. This
   specific write path was code-reviewed but **not** independently
   wire-verified during this repository's own implementation - see
   `CHANGELOG.md` - confirm it yourself if you touch this code.
6. Confirm services this profile does **not** implement (e.g. AE-CRL-B -
   `Recipient_List` is not writable here) are still rejected.

### Keeping the PICS honest

`docs/PICS.md` is partly generated. `docs/objects.json` describes each object
and who serves which property; the series tool regenerates the object tables
from it plus the stack's own `docs/property-profile-reference.md` at the
pinned commit:

```bash
python tools/gen-objects-properties.py BACnetProfileExample-B-EC-CPP            # rewrite
python tools/gen-objects-properties.py BACnetProfileExample-B-EC-CPP --check    # fail if stale
```

(That tool lives in the example-series repository, not in this one. If you
only have this repository, edit the generated block by hand and keep it
matching the callbacks in `main.cpp`.)

When you add an object or a property to `main.cpp`, update `docs/objects.json`
in the same change and regenerate. The `app` list is what the callbacks serve;
`accepted` is for a required property you deliberately leave to the stack's
default, and each one needs a justification. Anything required, not in `app`
and not in `accepted`, comes out as a ⚠ row - that is a defect, not a feature.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| On start-up the app prints a wall of red `Error:` lines but the device works | **Expected - this is not your bug.** Two benign sources, both from the stack's own debug logging: (1) the device receives its **own** broadcast I-Am and logs a decode cascade (*"Services is not supported service=[0]"* ... *"Failed to process the incoming NPDU"*) - any BACnet/IP device that listens for broadcasts hears itself; (2) a one-time *"UUID has not been set. A UUID must be set for the BACnetSC device to start."* - the stack starts a BACnet/SC datalink these IP-only examples never configure. It appears once and does not spam. On a healthy start-up roughly half the output is these lines. |
| CMake error: *"CAS BACnet Stack adapter not found under: ..."* | Submodules not initialized. Run `git submodule update --init --recursive` (or pass `-D CAS_STACK_DIR=...`). |
| `CASBACnetStackDLL.h: No such file or directory` | Same - submodules not checked out. |
| Windows: *"No CMAKE_CXX_COMPILER could be found"* | Install Visual Studio with the "Desktop development with C++" workload, then re-run from a fresh terminal. |
| First build seems stuck for minutes | Normal - it's compiling ~600 stack files. Only the first build is slow. |
| App prints *"Failed to bind UDP port 47808"* | Another BACnet program is already using 47808. Stop it, or run with `--port <n>`. |
| Client sends Who-Is but sees no I-Am | Firewall is blocking UDP 47808, or the client and device are on different subnets (Who-Is is a broadcast). Allow the port; test on the same subnet first. |
| WriteProperty to a commandable output returns an error instead of the expected `value-out-of-range` | Confirm you're writing to `Present_Value` on Chartreuse/Fuchsia/Indigo, not another property, and that the value is decodable as the object's datatype (Real for Chartreuse, 0/1 for Fuchsia, an Unsigned state for Indigo). |
| `Landing_Call_Control` write appears to succeed but a subsequent read shows no queued call | Confirm the WriteProperty targets Elevator Group 1 (Maroon) and property `Landing_Call_Control`, not `Landing_Calls` (the group's own queue, which this example never populates independently - see `docs/objects.json`'s note on Maroon). |
| Replies show an unexpected device instance or vendor | Another BACnet device is already answering on this host/port. On Linux/macOS two processes can share the port and both reply; on Windows the example asks for `SO_EXCLUSIVEADDRUSE` (`common/SimpleUDP.cpp`) so this shows up as a bind failure instead. Stop the other device, or use `--port`. |
