# VeriBACnet results

The latest VeriBACnet run of this folder's project, summarised by hand from
that run's `report.json`. The run's own Results Folder (reports, packet
captures, wire logs) is not published: it holds the testing machine's network
addresses.

| | |
|---|---|
| Date | 2026-10-27 |
| Example | BACnet B-EC (Elevator Controller) Example - C++ v1.2.0 (`common/` 3.5.0, CAS BACnet Stack `6.x` @ `69b6249f`) |
| Profile | B-EC (BACnet Elevator Controller) |
| Transport | BACnet/IP, UDP port 47833 |
| VeriBACnet | 0.20.0 (its test device uses CAS BACnet Stack 6.0.23.0) |
| Test plan | 211 BTL tests (ANSI/ASHRAE 135.1-2023) selected for the B-EC profile and the options this device claims |
| Result | **95 PASS · 0 FAIL · 0 ERROR · 116 SKIP** |

**Judged BTL-clean on BACnet/IP, with a star**: no failure or error is the
example's own fault, every other failure is tracked, and every skipped test has
a stated reason. The star means some of the functions the example exists for
were not measured by VeriBACnet in this run (below). See "What BTL-clean means"
in [README.md](README.md). This is not BTL certification.

**Fixed in the 2026-10-26 run (still in place):**
- Analog Input 1 supports COV, so BACnet requires its COV_Increment property,
  which was missing. It is now present and reads 1.0.
- Notification Class 1's Recipient_List could not be written, and it did not
  hold the one entry BACnet then requires. It is now writable, so a
  workstation can add itself, and alarms reach whatever is written there. Its
  default is that standard entry: local broadcast with an empty address,
  Process Identifier 0, unconfirmed, all days and transitions. Alarms are still
  broadcast on the local network.

Wire Tests check both fixes.

**Measured coverage:** 95 of the 211 selected tests ran (all 95 passed).
Of the 116 skipped, 37 wait on a test-tool or test-script fix (tracked), 48 need
an operator or a value the test tool cannot change by itself, and 31 do not apply
to this device. It cannot create, delete or rename objects over BACnet. It has no
Event Enrollment, Analog Value, Binary Value or writable array object, and only one
event-reporting object. Its Protocol_Revision rules out the older
DeviceCommunicationControl forms.

**Measured now:** ReadProperty and ReadPropertyMultiple (all 24 tests passed),
Who-Is and Who-Has, command prioritization on the outputs, WriteProperty and
WritePropertyMultiple, including their error cases and a write of the
Elevator Group's Landing_Call_Control (14 of 18 WritePropertyMultiple tests ran), TimeSynchronization, GetEventInformation, the
Read Support and EPICS consistency tests, **COV notifications** (SubscribeCOV on
Analog Input 1: the subscription, the notifications and the error cases passed;
the two numeric-COV tests that need the value changed wait for an operator),
**COV-multiple subscriptions** and **ReinitializeDevice**.

**Not measured yet:** event notification (AE-N-I-B), alarm acknowledgement
(AE-ACK-B), DeviceCommunicationControl disable-initiation (DM-DCC-B) and Who-Is
initiation (DM-DDB-A). The event and acknowledgement tests need an operator to
press the lift car's alarm button or obstruct its door, or values that cannot be
fixed in advance on a live device. The disable-initiation tests need a value the
test tool can change and watch over COV. This device's only COV object is a
read-only sensor. The Who-Is initiation test needs an operator to press `d`. The
COV tests that change a value (9.10.1.4, .5, .7, .9, .11) are skipped for the
same reason. All of it is tracked. This example's own Wire Tests cover these
functions: landing calls served by the lift car and both Failure Modes, the car
followed over COV and ReadPropertyMultiple, the passenger alarm (notification,
GetEventInformation, AcknowledgeAlarm), the door fault and the three commandable
outputs.

This run replaces the 2026-10-26 run (210 tests, 94 ran, 6 failed). Since then
VeriBACnet's scripts take more of their objects and values from the device, so
the six failures that came from a script asking for a writable Analog Value
(or a writable Network Port property) now pass: 9.22.1.5, 9.23.1.3, 9.23.2.3
and 9.23.2.15 ran against this device's own outputs, and 7.2.2, 9.22.2.1 and
9.42.1.2 now run too. 8.2.1 and 8.3.1 are no longer failures: they reach Analog
Input 1 and stop at the clause's operator step. Nothing in the example changed.

## Tests that did not pass

None. Every selected test either passed or was skipped with a reason.

## Skipped tests, by reason

| Tests | Why |
|---|---|
| 9.42.1.3 to .11, 9.42.2.6, 9.42.2.7 SubscribeCOVPropertyMultiple | The test tool cannot yet work out the scenario data these tests need for a device it did not build. Tracked. |
| 9.1.1.8 to .11, 9.1.1.15, 9.1.2.1, 9.1.2.3 to .7, 7.3.1.11.1 AcknowledgeAlarm | The tests compare against declared values, such as alarm time stamps, that cannot be fixed in advance on a live device. Tracked. |
| 9.1.1.1 to .6, 9.1.1.14 AcknowledgeAlarm | Need an operator to raise the lift car's alarm. |
| 7.3.1.19.x, 7.3.1.20.x, 7.3.1.22.x, 8.4.17.x, 8.5.17.x, 7.3.2.35.x, 7.3.2.36.x | Need an operator to raise an alarm or a fault on the lift car; the run was unattended. |
| 9.10.1.4, .5, .7, .9, .11 COV; 9.24.1.6 to .10, 9.24.1.12 DeviceCommunicationControl | Need a value the test tool can change and watch over COV. The Analog Output does not offer COV (the device correctly refuses), and the Analog Input is read-only. |
| 7.3.2.10.9 / .10, 9.32.1.12 / .13 | Need an operator: the name and instance are configured by restarting the device with `--deviceName` / `--deviceID`. |
| 8.34.2 Who-Is initiation | Needs an operator: the device sends its Who-Is when a person presses `d`. |
| 9.27.1.1 / 9.27.1.3 ReinitializeDevice | Need an operator to confirm the restart. |
| 9.22.1.3, 9.23.1.5 | No writable non-commandable property has a value the test tool can choose (Landing_Call_Control holds a structured value); the clauses skip the tests then. |
| 8.2.1, 8.2.2, 8.3.1, 8.3.2 COV notification | Need an operator to change Analog Input 1's Present_Value or Status_Flags (it is a read-only sensor and the device correctly refuses the writes). |
| 7.3.2.21.3.1, .2, .4, .5, .6, .7, 7.3.1.10.1 | Need recipient-list or Event_Enable scenarios the test tool cannot yet work out for this device (no object it can drive reports events; the Event_Enable is fixed in `main.cpp`). Tracked. |
| 7.2.8 | Needs an operator to raise an event. |
| 9.23.2.20 | Needs a writable time property; this device has none the test tool can use. Tracked. |
| btl-auto 9.8.2 / 9.8.3 | Automated companions written for another device's Analog Value. |
| 7.3.2.10.3 to .6 Database_Revision | The device cannot create, delete or rename objects over BACnet; the clause skips the tests then. |
| 9.8.2 to 9.8.5 (Event Enrollment), 8.4.2 / 8.5.2 forms, 7.3.1.12 | Need an Event Enrollment, a binary or multi-state object that reports events, or two event-reporting objects; this device has only the Lift. |
| 9.22.2.4, 9.23.2.7, 9.22.2.10, 9.23.2.13, 9.22.2.11, 9.23.2.18, 9.22.1.6 | No writable property has a restricted range, and the device has no writable array, optional-functionality write or writable non-commandable Present_Value; the clauses skip the tests then. |
| 9.24.1.1 to .5, 9.24.2.3, 9.8.6 | Do not apply at this Protocol_Revision, or the device cannot hold enough active events. |

Four more B-EC requirements have no runnable VeriBACnet test yet: 7.3.1.11.3 and
7.3.1.11.4 Acked_Transitions tests, and 8.4 and 8.5 event notification initiation
tests. All tracked.

DeviceCommunicationControl and ReinitializeDevice were tested without a
password: the example has no password option and ships with none set
(`DCC_PASSWORD` in `main.cpp` is empty).

No public issue has been opened for any of these.
