# BACnet Protocol Implementation Conformance Statement (PICS)

For the **BACnet B-EC (Elevator Controller) C++ example** -
see [README.md](../README.md).

> This is the PICS **for the example as shipped**. It describes a tutorial
> device announcing itself as a Chipkin demo, not a product. When you turn this
> example into your own device, this document is one of the things you rewrite:
> the vendor, model and version rows all come from the
> `CHANGE ALL OF THIS BEFORE YOU SHIP` block at the top of `main.cpp`. The
> example has **not** been submitted for BTL certification.

## 1. Product description

| | |
|---|---|
| **Vendor Name** | Chipkin Automation Systems |
| **Vendor Identifier** | 389 |
| **Product Name** | CAS BACnet Stack Example - B-EC |
| **Product Model Number** | CAS BACnet Stack Example - B-EC |
| **Application Software Version** | 1.3.0 |
| **Firmware Revision** | 6.0.23.0 (the CAS BACnet Stack version) |
| **BACnet Protocol Version** | 1 |
| **BACnet Protocol Revision** | 30 |

**Product Description:** a BACnet/IP elevator controller built on the CAS
BACnet Stack. It reports what an elevator installation (an Elevator Group, a
Lift and an Escalator) is doing - the same object family as the B-EM (Elevator
Monitor) example - and, unlike a B-EM, also **accepts commands**: WriteProperty
to three commandable outputs and to the Elevator Group's landing-call control -
a landing call is served by a simulated lift car (README "What is Simulation"),
which travels to the floor and opens its door - TimeSynchronization, and
ReinitializeDevice. It generates intrinsic event notifications - CHANGE_OF_STATE
on the Lift's `Passenger_Alarm`, FAULT_LISTED on its `Fault_Signals` - answers
ReadProperty/ReadPropertyMultiple for every required property of every object,
and is discoverable by Who-Is/I-Am and Who-Has/I-Have (and can also initiate a
Who-Is on demand). It is a tutorial for implementers of the B-EC profile.

## 2. BACnet standardized device profile (Annex L)

**B-EC - BACnet Elevator Controller.**

This device claims exactly one profile. Because the B-EC requirements are a
superset of B-GENERAL's, a conformant B-EC device also satisfies **B-GENERAL**
(Annex L.8); that is subsumption, not a second claim.

## 3. BIBBs supported (Annex K)

| BIBB | Description |
|---|---|
| DS-RP-B | Data Sharing - ReadProperty - B |
| DS-RPM-B | Data Sharing - ReadPropertyMultiple - B |
| DS-WP-B | Data Sharing - WriteProperty - B |
| DS-WPM-B | Data Sharing - WritePropertyMultiple - B |
| DS-COV-B | Data Sharing - COV - B |
| DS-COVM-B | Data Sharing - COV-Multiple - B |
| AE-N-I-B | Alarm and Event - Notification Internal - B |
| AE-ACK-B | Alarm and Event - ACK - B |
| AE-INFO-B | Alarm and Event - Information - B |
| DM-DDB-A | Device Management - Dynamic Device Binding - A |
| DM-DDB-B | Device Management - Dynamic Device Binding - B |
| DM-DOB-B | Device Management - Dynamic Object Binding - B |
| DM-DCC-B | Device Management - DeviceCommunicationControl - B |
| DM-TS-B | Device Management - TimeSynchronization - B |
| DM-RD-B | Device Management - ReinitializeDevice - B |

No other BIBBs are supported. In particular this device does **not** support
DM-UTC-B (this example synchronizes local time only, not UTC - see
`SERVICE_TIME_SYNCHRONIZATION` in `main.cpp`), AE-CRL-B (not claimed; the
Notification Class's `Recipient_List` is writable, but the profile does not
require the BIBB), scheduling (SCHED-*), or
trending (T-*).

## 4. Application services supported

| Service | Initiate | Execute |
|---|:---:|:---:|
| ReadProperty | no | **yes** |
| ReadPropertyMultiple | no | **yes** |
| WriteProperty | no | **yes** |
| WritePropertyMultiple | no | **yes** |
| SubscribeCOV | no | **yes** |
| SubscribeCOVPropertyMultiple | no | **yes** |
| Who-Is | **yes** (on demand, press `d`) | **yes** |
| I-Am | **yes** | - |
| Who-Has | no | **yes** |
| I-Have | **yes** | - |
| ConfirmedEventNotification / UnconfirmedEventNotification | **yes** (intrinsic alarm) | no |
| ConfirmedCOVNotification / UnconfirmedCOVNotification | **yes** | no |
| ConfirmedCOVNotificationMultiple / UnconfirmedCOVNotificationMultiple | **yes** | no |
| AcknowledgeAlarm | no | **yes** |
| GetEventInformation | no | **yes** |
| DeviceCommunicationControl | no | **yes** |
| TimeSynchronization | no | **yes** |
| ReinitializeDevice | no | **yes** |

COV notifications are sent to each SubscribeCOV / SubscribeCOVPropertyMultiple
subscriber, confirmed or unconfirmed as the subscriber asked (DS-COV-B,
DS-COVM-B: a SubscribeCOVPropertyMultiple subscriber gets the -Multiple form).
An unsolicited I-Am is broadcast to the local subnet at start-up, as well as in
response to Who-Is. Event notifications are sent (unconfirmed, to the local
subnet broadcast) when the Lift's CHANGE_OF_STATE algorithm (`Passenger_Alarm`,
the car's alarm button) or FAULT_LISTED algorithm (`Fault_Signals`, notified as
CHANGE_OF_RELIABILITY) transitions. The Wire Tests add a second, confirmed
recipient through the test-only `BEC_TEST_EVENT_RECIPIENT_PORT` environment
variable; `Number_Of_APDU_Retries` is 3, so an unacknowledged confirmed
notification is sent again after `APDU_Timeout` (10000 ms).

Any other confirmed service is rejected. That rejection is part of the
profile boundary, not a limitation to work around.

## 5. Segmentation capability

Segmentation is **supported in both directions**
(`Segmentation_Supported` = `segmented-both`), by the stack: at `6.x` @
`69b6249f` the customer build compiles `STACK_OPTION_SEGMENTATION` in (stack
#2992), and this example keeps the stack's defaults - `Max_Segments_Accepted`
16 and `APDU_Segment_Timeout` 5000 ms. Table 12-13 footnote 1: "These
properties are required if, and shall be present only if, segmentation of any
kind is supported" - they are not rows in section 11 because its generator
lists only unconditionally required properties. `Max_APDU_Length_Accepted` is
1476 octets, the BACnet/IP maximum. (At the earlier pin `abd4cee1`, this
example answered `no-segmentation`.)

## 6. Standard object types supported

No object is dynamically creatable or deletable. `Present_Value` of the three
Output objects, and `Landing_Call_Control` of the Elevator Group, are the only
writable properties on this device.

| Object type | Instance | Object_Name | Optional properties supported |
|---|:---:|---|---|
| Device | 389013 | Chipkin Example B-EC | Description |
| Analog Input | 1 | Bronze | - |
| Binary Input | 1 | Emerald | - |
| Multi-state Input | 1 | Hot Pink | State_Text |
| Analog Output | 1 | Chartreuse | - |
| Binary Output | 1 | Fuchsia | - |
| Multi-state Output | 1 | Indigo | - |
| Network Port | 1 | Vermilion | - |
| Elevator Group | 1 | Maroon | Group_Mode, Landing_Calls, Landing_Call_Control (writable) |
| Lift | 1 | Mauve | Reliability (FAULT_LISTED), Assigned_Landing_Calls, Registered_Car_Call, Landing_Door_Status; intrinsic reporting (Event_State, Event_Enable, Notification_Class, ...) |
| Escalator | 1 | Mint | Power_Mode, Escalator_Mode |
| Positive Integer Value | 1 | Turquoise | - |
| Notification Class | 1 | Crimson | - |

The device instance is configurable at start-up with `--deviceID`, and the
Device's Object_Name with `--deviceName` (BACnet requires both to be
configurable, cl. 12.1.1.3 and 12.1.1.4). Changing either means restarting
the device; neither is writable over the network. The table shows the
defaults.

## 7. Data link layer options

**BACnet/IP (Annex J)**, UDP port 47808 (0xBAC0) by default, configurable at run
time with `--port`.

BBMD is not supported, Foreign Device registration is not supported, and
BACnet/SC, MS/TP, Ethernet (Annex H) and PTP are not supported.

The stack's Network Port object still lists its BACnet/IP properties in
`Property_List` - including `IP_DNS_Server`, `FD_BBMD_Address` and
`FD_Subscription_Lifetime` - and every one of them reads as a value
(`FD_BBMD_Address` is a Null host, port 0: no BBMD configured). The Wire Tests
read every listed property of every object.

## 8. Device address binding

Static device binding is **not supported**. This device answers Who-Is/Who-Has
and does not initiate any confirmed request to a peer that would require one
(its own Who-Is, DM-DDB-A, is unconfirmed and does not bind an address).

## 9. Networking options

None. The device is not a router, not a BBMD, and does not register as a
foreign device.

## 10. Character sets supported

UTF-8 (ANSI X3.4). Supporting a character set does not imply the device can
handle data in all character sets.

## 11. Objects and properties

<!-- OBJECTS-PROPERTIES:BEGIN (generated by tools/gen-objects-properties.py from docs/objects.json - do not edit here) -->
Every object this example creates, and every REQUIRED property of each (per ANSI/ASHRAE 135-2024 clause 12 and the CAS BACnet Stack's property profiles), plus the optional properties the example turns on. **Served by** says who answers a ReadProperty: the **stack** generates it, or the **app** serves it from a `GetProperty*` callback in `main.cpp`. A ⚠ row is a required property the app does not serve and the stack would fill with a default - that is a defect, not a feature.

### Device 389013 "Chipkin Example B-EC" - the device itself; the instance is configurable with --deviceID and the Object_Name with --deviceName (both at start-up; the heading shows the defaults). The stack rows are device-wide facts only the stack knows - the protocol version and revision it implements, the services and object types it was configured with, the live object list and address-binding table, and Database_Revision, which the stack starts at 0 and increments for each object added at start-up: it reads 13 (the Device and the twelve objects main.cpp adds) and stays 13, because nothing creates, deletes or renames an object afterwards (commanding an output, a landing call, the car moving and the alarm button change values, not the object database). The accepted rows are the stack's configured defaults for APDU limits, segmentation and system status; an application that answered them from its own constants could contradict the stack, so this example does not

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| System_Status | BACnetDeviceStatus | stack default, accepted (Generic Enumerated default: `0`) | no |
| Vendor_Name | CharacterString | app | no |
| Vendor_Identifier | Unsigned16 | app | no |
| Model_Name | CharacterString | app | no |
| Firmware_Revision | CharacterString | app | no |
| Application_Software_Version | CharacterString | app | no |
| Description *(optional, enabled)* | CharacterString | app | no |
| Protocol_Version | Unsigned | stack | no |
| Protocol_Revision | Unsigned | stack | no |
| Protocol_Services_Supported | BACnetServicesSupported | stack | no |
| Protocol_Object_Types_Supported | BACnetObjectTypesSupported | stack | no |
| Object_List | BACnetARRAY[N] of BACnetObjectIdentifier | stack | no |
| Max_APDU_Length_Accepted | Unsigned | stack default, accepted (`CAS_BACNET_DEVICE_DEFAULT_MAX_APDU_LENGTH_ACCEPTED`) | no |
| Segmentation_Supported | BACnetSegmentation | stack default, accepted (`BACnetSegmentation::segmentedBoth` with `STACK_OPTION_SEGME) | no |
| APDU_Timeout | Unsigned | stack default, accepted (`CAS_BACNET_DEVICE_DEFAULT_APDU_TIMEOUT`) | no |
| Number_Of_APDU_Retries | Unsigned | app | no |
| Device_Address_Binding | BACnetLIST of BACnetAddressBinding | stack | no |
| Database_Revision | Unsigned | stack | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Analog Input 1 "Bronze" - REAL, degrees Celsius; starts at 21.5. F-COVM: Present_Value AND Status_Flags are both marked subscribable (SetPropertySubscribable), so a SubscribeCOVPropertyMultiple naming both fires one multi-property notification when the up/down keys nudge this value. COV_Increment 1.0 (required: the object supports COV reporting, cl. 12.2 footnote 2)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |
| COV_Increment *(optional, enabled)* | Real | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Binary Input 1 "Emerald" - starts inactive

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Multi-state Input 1 "Hot Pink" - state 1 of 3: On, Off, Auto

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| State_Text *(optional, enabled)* | BACnetARRAY[N] of CharacterString | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Analog Output 1 "Chartreuse" - F-OUTPUTS (NEW vs B-EM; canonical pattern from B-SA-CPP). REAL setpoint, 16-slot Priority_Array + Relinquish_Default (20.0); commandable. Present_Value itself is resolved by the stack from the Priority_Array - this application's Get callback answers the individual array-index reads (and Relinquish_Default) rather than Present_Value directly, exactly as B-SA's canonical pattern documents

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Real | app | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Units | BACnetEngineeringUnits | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalReal | app | no |
| Relinquish_Default | Real | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Binary Output 1 "Fuchsia" - F-OUTPUTS (NEW vs B-EM). Active/inactive, commandable; Relinquish_Default inactive (0). Out-of-range writes (anything but 0/1) are rejected with value-out-of-range

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | BACnetBinaryPV | app | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Polarity | BACnetPolarity | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalBinaryPV | app | no |
| Relinquish_Default | BACnetBinaryPV | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Multi-state Output 1 "Indigo" - F-OUTPUTS (NEW vs B-EM). State 1..3, commandable; Relinquish_Default state 1. Out-of-range writes (state 0 or >3) are rejected with value-out-of-range. Verified by wire test: WriteProperty of state 9 rejected with value-out-of-range

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | app | yes |
| Status_Flags | BACnetStatusFlags | stack | no |
| Event_State | BACnetEventState | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Number_Of_States | Unsigned | app | no |
| Priority_Array | BACnetARRAY[16] of BACnetOptionalUnsigned | app | no |
| Relinquish_Default | Unsigned | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |
| Current_Command_Priority | BACnetOptionalUnsigned | stack | no |

### Network Port 1 "Vermilion" - BACnet/IP; Network_Type and Protocol_Level are set from BACnetStack_AddNetworkPortObject()'s arguments (IPv4, BACnet Application) at start-up, not a GetProperty callback like the object's other app-served rows; Changes_Pending is likewise computed and answered natively by the stack's Network Port object. Reliability has no fault condition this example detects, so it is accepted at the generic default (normal)

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Reliability | BACnetReliability | stack default, accepted (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Network_Type | BACnetNetworkType | app | no |
| Protocol_Level | BACnetProtocolLevel | app | no |
| Changes_Pending | Boolean | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Elevator Group 1 "Maroon" - F-ELEVATOR (canonical, from B-EM). Machine_Room_ID, Group_ID and Group_Members are NOT stack DEFAULTS - they are genuinely stored and served by BACnetStack_AddElevatorGroupObject (Group_Members is also maintained by BACnetStack_AddLiftOrEscalatorObject as Lift 1/Mauve is added to this group). They are marked accepted only because the stack's generic per-type property profile does not know about this object-specific host-configuration API and so cannot credit them as stack-served. isGroupOfLifts=true and supportLandingCallStatus=true: Group_Mode and LandingCalls are therefore also enabled (see the Lift's note for how the four F-ELEVATOR list/sequence callbacks are exercised) but the stack's generic Elevator Group property profile does not mark either 'required', so neither generates a checked row here - Group_Mode is served by GetPropertyEnumerated (normal) and LandingCalls by GetListElevatorGroupLandingCallStatus (the group's active landing calls, one element per call; an empty list returns false on the first call) regardless. NEW vs B-EM: Landing_Call_Control is writable - BACnetStack_RegisterCallbackSetElevatorGroupLandingCallControl is registered (B-EM deliberately leaves it unregistered) - and a landing call written to it is SERVED: the simulated car travels to the floor, opens its door, and the call leaves Landing_Calls (a destination call then becomes a car call). A call for a floor outside 1-8 is refused (the stack answers Error PROPERTY / WRITE_ACCESS_DENIED: the callback has no errorCode parameter). The last accepted call reads back; before any it reads floor 0, direction none. Proven by tests/landing_call_test.py and landing_call_failure_test.py

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Machine_Room_ID | BACnetObjectIdentifier | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Group_ID | Unsigned8 | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Group_Members | BACnetARRAY[N] of BACnetObjectIdentifier | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Landing_Call_Control *(optional, enabled)* | BACnetLandingCallStatus | app | yes |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Lift 1 "Mauve" - F-ELEVATOR (from B-EM). The Lift presents the car SIMULATION (simulation/ElevatorCar.cpp, the same file as B-EM's; README 'What is Simulation'): Car_Position and Car_Moving_Direction via GetPropertyUnsignedInteger/GetPropertyEnumerated, Car_Door_Status (one door, index 1) via GetPropertyEnumerated with useArrayIndex - SAFETY_LOCKED while the car moves, OPENING/OPENED/CLOSING/CLOSED at a stop - Passenger_Alarm and Out_Of_Service via GetPropertyBool, and Fault_Signals (DOOR_CLOSING_FAULT when a door fails to close) via GetListOfEnumerations. Every change goes to the stack with BACnetStack_UpdateValue. The stack's Lift property profile lists those six required properties (with no default: the application must serve them), so the table below shows them; this example serves them because clause 12.59 requires them. Status_Flags, Elevator_Group, Group_ID and Installation_ID ARE in the generic table (stack-computed/stack-stored) and are accepted for the same reason as Maroon's. Event reporting, both algorithms clause 12.59 names: CHANGE_OF_STATE on Passenger_Alarm (pAlarmValues TRUE; the 's' key or the test-only control channel presses the button) and FAULT_LISTED on Fault_Signals, both to Notification Class 1 (Crimson). Reliability is enabled for the fault algorithm and computed by the stack from it; the app does not serve it. Car_Position, Car_Moving_Direction and Car_Door_Status are SetPropertySubscribable (DS-COVM-B on the car). Optional Assigned_Landing_Calls (the group's active landing calls - Mauve is its only car - and none while the car is faulted), Registered_Car_Call (the car's pending stops that are not landing calls: a destination call's destination) and Landing_Door_Status (floors 1-8: the car's floor follows the car door, the others SAFETY_LOCKED) are enabled and served by the F-ELEVATOR sequence callbacks

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Elevator_Group | BACnetObjectIdentifier | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Group_ID | Unsigned8 | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Installation_ID | Unsigned8 | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Car_Position | Unsigned8 | app | no |
| Car_Moving_Direction | BACnetLiftCarDirection | app | no |
| Car_Door_Status | BACnetARRAY[N] of BACnetDoorStatus | app | no |
| Passenger_Alarm | Boolean | app | no |
| Reliability *(optional, enabled)* | BACnetReliability | stack | no |
| Out_Of_Service | Boolean | app | no |
| Fault_Signals | BACnetLIST of BACnetLiftFault | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Escalator 1 "Mint" - F-ELEVATOR. Not a member of Maroon (a group of Lifts, isGroupOfLifts=true) - added with the spec's 'no reference' sentinel (4194303) for Elevator_Group, as clause 12.60.6 allows. Required Operation_Direction (no stack default), Passenger_Alarm and Out_Of_Service are served by the app; the optional Power_Mode and Escalator_Mode are enabled and served too, for a fuller demonstration. Status_Flags/Elevator_Group/Group_ID/Installation_ID are stack-stored, same reasoning as Mauve's

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Elevator_Group | BACnetObjectIdentifier | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | no |
| Group_ID | Unsigned8 | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Installation_ID | Unsigned8 | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Power_Mode *(optional, enabled)* | Boolean | stack default (Generic Boolean default: `false`) | no |
| Operation_Direction | BACnetEscalatorOperationDirection | app | no |
| Escalator_Mode *(optional, enabled)* | BACnetEscalatorMode | stack default (Generic Enumerated default: `0`) | no |
| Out_Of_Service | Boolean | app | no |
| Passenger_Alarm | Boolean | app | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Positive Integer Value 1 "Turquoise" - not one of the profile's named objects - added explicitly by this application, BEFORE Elevator Group 1 (Maroon), as the object Maroon's Machine_Room_ID references. BACnetStack_AddElevatorGroupObject's own doc comment reads as though the stack creates this object automatically if missing; verified against the running stack, it does not - AddElevatorGroupObject fails outright ('Create the Positive Integer Value object before adding the Elevator Group object') unless the application adds it first. Colour 'Turquoise' per docs/colour-table.md's global positive_integer_value mapping; Present_Value (required, no stack default) is served as an arbitrary plausible room id. Units defaults to no-units (accepted) since a machine-room identifier has none; Out_Of_Service is optional and left at the generic default

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Present_Value | Unsigned | app | no |
| Status_Flags | BACnetStatusFlags | stack | no |
| Units | BACnetEngineeringUnits | stack default, accepted (`BACnetEngineeringUnits::noUnits`) | no |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

### Notification Class 1 "Crimson" - AE-N-I-B / AE-ACK-B / AE-INFO-B. Priority, Ack_Required and Recipient_List are NOT stack DEFAULTS - they are genuinely populated by BACnetStack_AddNotificationClassObject (Priority, Ack_Required) and BACnetStack_AddRecipientToNotificationClass (Recipient_List) at start-up; marked accepted only because the stack's generic per-type property profile does not know about this object-specific host-configuration API. Recipient_List is WRITABLE (as on B-AAC; AE-CRL-B is still not claimed): a written list lasts until restart. Its seeded default is the entry cl. 12.21 requires of a read-only list: local broadcast (network 0, empty MAC), all days, 00:00:00.00-23:59:59.99, Process Identifier 0, unconfirmed, all transitions

| Property | Datatype | Served by | Writable |
|---|---|---|:---:|
| Object_Identifier | BACnetObjectIdentifier | stack | no |
| Object_Name | CharacterString | app | no |
| Object_Type | BACnetObjectType | stack | no |
| Priority | BACnetARRAY[3] of Unsigned | stack default, accepted (Generic UnsignedInteger default: `0`) | no |
| Ack_Required | BACnetEventTransitionBits | stack default, accepted (Generic BitString default: empty bitstring (zero bits - NOT ) | no |
| Recipient_List | BACnetLIST of BACnetDestination | stack default, accepted (None known - a read fails with `unknown-property` or an empt) | yes |
| Property_List | BACnetARRAY[N] of BACnetPropertyIdentifier | stack | no |

<!-- OBJECTS-PROPERTIES:END -->

## 12. References

- ANSI/ASHRAE Standard 135-2024, Annex A (PICS template), Annex K (BIBBs),
  Annex L (device profiles), Clause 12 (object types), Clause 13 (alarm and
  event services).
- [README.md](../README.md) - what this example is and how to build it.
- [TUTORIAL.md](../TUTORIAL.md) - how to extend it, and how to keep this
  document honest when you do.
