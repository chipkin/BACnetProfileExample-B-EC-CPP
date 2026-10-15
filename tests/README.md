# B-EC Wire Tests

Tests that drive the running elevator controller over BACnet/IP from outside
it. They are written against the series' shared harness in
[`../wiretest/`](../wiretest/README.md) (vendored, like `common/`); everything
specific to this device is here. Python 3 standard library only - nothing to
`pip install`.

What they cover today is **discovery**: a client can find the device and read
every property it says it has. They do not yet prove the B-EC Profile Function
(L.13.2: elevator control with limited modification by another device): a
landing call is stored but nothing moves the car, and writes, COV, alarming,
time synchronization and restart are still verified by hand (README "Verify").

## Running

Build the example (README "Build"), then from the repository root:

```bash
python3 tests/run_wire_tests.py --exe build/BACnetExampleBEC
```

On Windows, `--exe build\Release\BACnetExampleBEC.exe`. It ends with
`ALL WIRE TESTS PASSED` (exit 0) or the scripts that failed. `--port` (default
47862) is the UDP port the test starts the device on. It takes a few seconds.
CI (`.github/workflows/release.yml`) runs it on Linux after the smoke test.

## The setup

```
test client (127.0.0.1, ephemeral UDP port)  - the Peer
    |  BACnet/IP, unicast
BACnetExampleBEC  UDP --port                 - Device 389013
```

The Peer is a Python BACnet client (`wiretest.Client`), never another example's
binary. It plays a client such as Chipkin BACnet Explorer.

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
