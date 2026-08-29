# Ascaso Baby T (and others) Memory Map

| Address | Length | Description | Value Format | Model Compatibility | Notes |
|---------|--------|-------------|--------------|---------------------|-------|
| 0 | 1 | Unknown | Integer | ? | Reads FF |
| 1 | 1 | Reset | Boolean | All | Reads **0x55**, not a 0/1 boolean - 0x55 is a conventional "memory initialised" marker, so this may be a magic byte rather than a command. **Never written to**: if it does trigger a reset, the cost is the whole settings block |
| 2 | 1 | Unknown | Integer | ? | Reads FF |
| 3 | 1 | Unknown | Integer | ? | Reads FF |
| 4 | 1 | Monday Auto On Hour | Integer (0-23) | Model 5+ | Weekly timer. Reads FF here - the whole weekly-timer block (4-31) is uninitialised on a Baby T |
| 5 | 1 | Monday Auto On Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 6 | 1 | Monday Auto Off Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 7 | 1 | Monday Auto Off Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 8 | 1 | Tuesday Auto On Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 9 | 1 | Tuesday Auto On Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 10 | 1 | Tuesday Auto Off Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 11 | 1 | Tuesday Auto Off Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 12 | 1 | Wednesday Auto On Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 13 | 1 | Wednesday Auto On Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 14 | 1 | Wednesday Auto Off Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 15 | 1 | Wednesday Auto Off Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 16 | 1 | Thursday Auto On Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 17 | 1 | Thursday Auto On Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 18 | 1 | Thursday Auto Off Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 19 | 1 | Thursday Auto Off Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 20 | 1 | Friday Auto On Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 21 | 1 | Friday Auto On Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 22 | 1 | Friday Auto Off Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 23 | 1 | Friday Auto Off Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 24 | 1 | Saturday Auto On Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 25 | 1 | Saturday Auto On Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 26 | 1 | Saturday Auto Off Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 27 | 1 | Saturday Auto Off Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 28 | 1 | Sunday Auto On Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 29 | 1 | Sunday Auto On Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 30 | 1 | Sunday Auto Off Hour | Integer (0-23) | Model 5+ | Weekly timer |
| 31 | 1 | Sunday Auto Off Minute | Integer (0-59) | Model 5+ | Weekly timer |
| 32 | 1 | Number of Groups | Integer | All | |
| 33 | 1 | Level Probe Sensitivity | Integer | Model 5+ | 0=Low, 1=Medium, 2=High. A Barista/Big Dream setting (as are 73/81/133); reads plausibly on a Baby T |
| 34 | 2 | Serial Number | Integer | All | u16. Does **not** match the machine number printed on the rating plate - that number appears nowhere in the read window, in either byte order or as BCD - so this is presumably an internal serial rather than the plate number. Unverified. The plate number is available separately from the trailing digits of the Bluetooth advertised name |
| 36 | 1 | Language | Integer | All | Values: 1, 2 |
| 37 | 1 | Unknown | Integer | ? | Reads 1, constant. Sits between Language (36) and Flush Enabled (38) |
| 38 | 1 | Flush Enabled | Boolean | All | 0=Disabled, 1=Enabled. Was wrongly listed at 43 (model>=5 stores value+1) |
| 39 | 1 | Unknown | Integer | ? | Reads 0, constant. Sits between the Flush (38) and Pre-infusion (40) flags; likely padding |
| 40 | 1 | Pre-infusion Enabled | Boolean | All | 0=Disabled, 1=Enabled. Was wrongly listed at 45 |
| 41 | 1 | S1 Pump-off Soak Time | Integer | Models 1-4 | Value * 10 (seconds). Writable, 0.0-5.0 s; default 3.0 s. See "The pump-off soak" below |
| 42 | 1 | S2 Pump-off Soak Time | Integer | Models 1-4 | Value * 10 (seconds). Writable, 0.0-5.0 s |
| 43 | 1 | L1 Pump-off Soak Time | Integer | Models 1-4 | Value * 10 (seconds). Writable, 0.0-5.0 s |
| 44 | 1 | L2 Pump-off Soak Time | Integer | Models 1-4 | Value * 10 (seconds). Writable, 0.0-5.0 s |
| 45 | 1 | XL Pump-off Soak Time (inert) | Integer | Models 1-4 | The fifth slot of the soak array at 41-44, i.e. the XL/continuous selection. A real register - it accepts and stores a written value - but the machine ignores it: with 2.0 s set here an XL delivery still pumped continuously with no pause. Reads 0. Exposed read-only |
| 46 | 1 | Group 1 Short Shot 1 Pre-infusion | Integer | Models 1-4 | Value * 10 (seconds), 0-5 s. This is the pump-ON time only; the pump-OFF soak lives at 41-44. The XL/continuous selection has no pre-infusion |
| 47 | 1 | Group 1 Short Shot 2 Pre-infusion | Integer | Models 1-4 | Value * 10 (seconds) |
| 48 | 1 | Group 1 Long Shot 1 Pre-infusion | Integer | Models 1-4 | Value * 10 (seconds) |
| 49 | 1 | Group 1 Long Shot 2 Pre-infusion | Integer | Models 1-4 | Value * 10 (seconds) |
| 50 | 1 | XL Pre-infusion (inert) | Integer | Models 1-4 | The fifth slot of the pre-infusion array at 46-49. Stores a written value but has no effect, tested the same way as 45. Reads 0. Exposed read-only |
| 51 | 1 | Unknown | Integer | ? | Reads 0, constant. Padding between the pre-infusion array and the Temperature Unit at 52 |
| 52 | 1 | Temperature Unit | Boolean | All | 0=Celsius, 1=Fahrenheit |
| 53 | 2 | Group 1 Coffee Temperature | Integer | Models 1-4 | Value * 10 (e.g., 93.0°C = 930) |
| 55 | 2 | Coffee Boiler PID P | Integer | All | Reads 30. See "Boiler PID parameters" below |
| 57 | 2 | Coffee Boiler PID I | Integer | All | Reads 15 |
| 59 | 2 | Coffee Boiler PID d | Integer | All | Reads 40 |
| 61 | 2 | Coffee Boiler PID b | Integer | All | Reads 10 |
| 63 | 2 | Steam Temperature | Integer | All | Value * 10 |
| 65 | 2 | Steam Boiler PID P | Integer | All | Reads 80 |
| 67 | 2 | Steam Boiler PID I | Integer | All | Reads 15 |
| 69 | 2 | Steam Boiler PID d | Integer | All | Reads 100 |
| 71 | 2 | Steam Boiler PID b | Integer | All | Reads 5 |
| 73 | 1 | Boiler Fill Timeout | Integer | Model 5+ | 0-240 |
| 74 | 2 | Filter Alarm | Integer | Model 5+ | u16, not 1 byte |
| 76 | 1 | Model Information | Integer | All | Stores model number (1-8) |
| 77 | 2 | Temperature Offset (alt register) | Integer | Models 1-4 | (Value - 99) / 10. Only live when byte 79 != 0; otherwise the machine uses offset 89 instead |
| 79 | 1 | Offset Register Select | Boolean | Models 1-4 | 0 = offset temperature lives at 89, non-zero = at 77. NOT standby time (that is the u16 at 84) |
| 80 | 1 | Shot Timer Enabled | Boolean | All | 0=Disabled, 1=Enabled. The manual's `Cr` parameter: stopwatch shown on the right display while brewing |
| 81 | 1 | Parameter CE | Integer | All | Power configuration, 1-3. See "Parameter CE" below |
| 82 | 2 | Economy Temperature | Integer | All | Value * 10 |
| 84 | 2 | Standby (Economy) Time | Integer | All | u16, minutes - the manual's `tiE`: inactivity time after which the steam boiler drops to the standby temperature at 82 (`teE`). **0 disables the standby function** |
| 86 | 1 | Steam Boiler Enable | Boolean | All | 0=Off, 1=On |
| 87 | 1 | Water Source | Boolean | All | 0=Direct Connection, 1=Tank (older note had these swapped). Baby T One (models 1/3) is tank-only |
| 88 | 1 | Unknown | Integer | ? | Reads 1, constant. Sits between Water Source (87) and the Temperature Offset at 89 |
| 89 | 2 | Group 1 Temperature Offset | Integer | Models 1-4 | Value * 10, signed. This is the "Offset temperature" the machine uses when byte 79 == 0 (the normal case) |
| 91 | 2 | Group 1 Short Shot 1 Dose | Integer | All | Pulses * 2 = ml |
| 93 | 2 | Group 1 Short Shot 2 Dose | Integer | All | Pulses * 2 = ml |
| 95 | 2 | Group 1 Long Shot 1 Dose | Integer | All | Pulses * 2 = ml |
| 97 | 2 | Group 1 Long Shot 2 Dose | Integer | All | Pulses * 2 = ml |
| 99 | 2 | Unknown (Group 2) | Integer | ? | u16, reads 6000 (0x1770), constant. Immediately precedes the Group 2 dose block, as 109 does for Group 3. At the usual tenths scaling 6000 would be 60.0 s, which would fit a per-group maximum dose time - unconfirmed |
| 101 | 2 | Group 2 Short Shot 1 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 103 | 2 | Group 2 Short Shot 2 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 105 | 2 | Group 2 Long Shot 1 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 107 | 2 | Group 2 Long Shot 2 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 109 | 2 | Unknown (Group 3) | Integer | ? | u16, reads 6000, constant. Same position relative to the Group 3 doses as 99 is to Group 2's |
| 111 | 2 | Group 3 Short Shot 1 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 113 | 2 | Group 3 Short Shot 2 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 115 | 2 | Group 3 Long Shot 1 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 117 | 2 | Group 3 Long Shot 2 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 119 | 2 | Unknown | Integer | ? | u16, reads 6000, constant. Third of the same pattern, but with no dose block after it |
| 121 | 1 | Unknown | Integer | ? | Reads 8, constant |
| 122 | 1 | Unknown | Integer | ? | Reads 12, constant |
| 123 | 1 | Unknown | Integer | ? | Reads 16, constant. 121-123 form an ascending 8/12/16 run with no obvious partner |
| 124 | 1 | Group 1 Enable | Boolean | All | 1=On, 0=Off. The machine's "coffee group" setting: turning it off leaves the steam boiler heating while the coffee group stays cold. Written as a plain u8 |
| 125 | 1 | Group 2 Enable | Boolean | Model 5+ | |
| 126 | 1 | Group 3 Enable | Boolean | Model 5+ | Not the autotimer flag on a Baby T: auto start/shutdown "enabled" = hour/minute bytes (127-130) != 100 (the "not set" sentinel) |
| 127 | 1 | Auto On Hour | Integer (0-23) | All | Daily timer; 100 = not set |
| 128 | 1 | Auto On Minute | Integer (0-59) | All | Daily timer |
| 129 | 1 | Auto Off Hour | Integer (0-23) | All | Daily timer; 100 = not set |
| 130 | 1 | Auto Off Minute | Integer (0-59) | All | Daily timer |
| 131 | 1 | Unknown | Integer | ? | Reads 0, constant. Padding between the Auto Off Minute (130) and Machine State (132) |
| 132 | 1 | Machine State | Integer | All | 4=Off, 6=On |
| 133 | 1 | Exposition Mode | Boolean | Model 5+ | Showroom/demo mode, 0/1 |
| 134 | 4 | Group 1 K1 (S1) Button Counter | Integer | All | u32 slots, 4 bytes apart. "Reset counter" writes u32 0 to 134/138/142/146/150 (not 210) |
| 138 | 4 | Group 1 K2 (S2) Button Counter | Integer | All | |
| 142 | 4 | Group 1 K3 (L1) Button Counter | Integer | All | |
| 146 | 4 | Group 1 K4 (L2) Button Counter | Integer | All | |
| 150 | 4 | Group 1 K5 (Flush/continuous) Button Counter | Integer | All | Flush / continuous ("XL") button |
| 154 | 4 | Group 2 K1 Button Counter | Integer | Model 5+ | |
| 158 | 4 | Group 2 K2 Button Counter | Integer | Model 5+ | |
| 162 | 4 | Group 2 K3 Button Counter | Integer | Model 5+ | |
| 166 | 4 | Group 2 K4 Button Counter | Integer | Model 5+ | |
| 170 | 4 | Group 2 K5 Button Counter | Integer | Model 5+ | |
| 174 | 4 | Group 3 K1 Button Counter | Integer | Model 5+ | |
| 178 | 4 | Group 3 K2 Button Counter | Integer | Model 5+ | |
| 182 | 4 | Group 3 K3 Button Counter | Integer | Model 5+ | |
| 186 | 4 | Group 3 K4 Button Counter | Integer | Model 5+ | |
| 190 | 4 | Group 3 K5 Button Counter | Integer | Model 5+ | |
| 194 | 4 | Tea 1 Counter | Integer | All | 4-byte slot like the button counters; upper 2 bytes zero in every dump. Reads 0 on a Baby T Plus |
| 198 | 4 | Tea 2 Counter | Integer | All | Reads 0 on a Baby T Plus |
| 202 | 4 | Unknown counter slot | Integer | ? | A fourth 4-byte slot in the 194/198/202/206 run, immediately before the resettable total. Zero in every dump - probably a third tea/drink counter this machine has no button for |
| 206 | 4 | Total Counter | Integer | All | The machine's own resettable total, exposed as `counter_total` - the manual's `SP`, "number of partial services since the last reset" (it counts coffees, so a double selection counts as two). Its own accumulator, not a live sum of 134..150: zeroing those leaves it unchanged and it keeps counting up from the old value, so the reset clears it explicitly |
| 210 | 4 | Total Coffee Counter | Integer | All | Lifetime total, exposed as `counter_lifetime` - the manual's `ST`, "number of total services of the machine". Not affected by a counter reset |
| 214 | 4 | Water Counter | Integer | All | Identical to 210 in all 8 dumps taken on a Baby T Plus - all of them predate a counter reset, so whether it is a true alias or its own accumulator is still open |
| 218 | 2 | Unknown | Integer | ? | Reads 0, constant. Trailing zeros after the Water Counter, at the end of the populated region |
| 220 | 5 | Uninitialised | - | - | Reads FF, as does everything up to 289. Offsets 0-4 read `FF 55 FF FF FF` |
| 237 | 1 | Group 1 Short Shot 1 Pre-infusion | Integer | Model 5+ | |
| 238 | 1 | Group 1 Short Shot 2 Pre-infusion | Integer | Model 5+ | |
| 239 | 1 | Group 1 Long Shot 1 Pre-infusion | Integer | Model 5+ | |
| 240 | 1 | Group 1 Long Shot 2 Pre-infusion | Integer | Model 5+ | |
| 242 | 1 | Group 2 Short Shot 1 Pre-infusion | Integer | Model 5+ | |
| 243 | 1 | Group 2 Short Shot 2 Pre-infusion | Integer | Model 5+ | |
| 244 | 1 | Group 2 Long Shot 1 Pre-infusion | Integer | Model 5+ | |
| 245 | 1 | Group 2 Long Shot 2 Pre-infusion | Integer | Model 5+ | |
| 247 | 1 | Group 3 Short Shot 1 Pre-infusion | Integer | Model 5+ | |
| 248 | 1 | Group 3 Short Shot 2 Pre-infusion | Integer | Model 5+ | |
| 249 | 1 | Group 3 Long Shot 1 Pre-infusion | Integer | Model 5+ | |
| 250 | 1 | Group 3 Long Shot 2 Pre-infusion | Integer | Model 5+ | |
| 252 | 2 | Group 1 Coffee Temperature | Integer | Model 5+ | Value * 10 |
| 254 | 2 | Group 2 Coffee Temperature | Integer | Model 5+ | Value * 10 |
| 256 | 2 | Group 3 Coffee Temperature | Integer | Model 5+ | Value * 10 |
| 258 | 2 | Group 1 Temperature Offset | Integer | Model 5+ | Offset value * 10 + 99 |
| 260 | 2 | Group 2 Temperature Offset | Integer | Model 5+ | Offset value * 10 + 99 |
| 262 | 2 | Group 3 Temperature Offset | Integer | Model 5+ | Offset value * 10 + 99 |
| 264 | 2 | Coffee Economy Temperature | Integer | Model 5+ | Value * 10 |
| 266 | 2 | Coffee Economy Timer | Integer | Model 5+ | |
| 276 | 1 | Maintenance Alarm | Integer | Model 5+ | |
| 280 | 2 | Hot Water Short Dose | Integer | Model 5+ | |
| 282 | 2 | Hot Water Long Dose | Integer | Model 5+ | |
## Notes from live dumps (2026-09-02, Baby T Plus 230V)

- This interface is a **configuration store, not a status interface**: nothing in it reflects what the machine is doing - no boiler temperature, no clock, no shot timer, and no alarms (an AL1 was raised deliberately and not one of the 2048 readable bytes moved).
- Offsets 0-4 read `FF 55 FF FF FF`; everything from 220 upwards is `FF`. See "Address space" below for why `0xA000` reads back as offset 0.
- 99-123 hold the Group 2/3 default doses (0x1770, 110, 220, 150, 300 pulses pattern) that a Baby T never uses.
- No live clock register exists; the clock is write-only via the `0xA000` command (see protocol.md).

## Parameter CE (offset 81)

Power configuration: how many heating elements the machine may run at the same
time, always prioritising the coffee group. It exists to cap the machine's
total current draw to suit the circuit it is installed on - it is an
electrical installation setting, not a brewing one.

Valid values are **1-3**; the manual gives the standard setting as **CE=2 for
all models**. Total current by setting:

| Model | Coffee | Steam | Max A | CE=1 | CE=2 | CE=3 |
|-------|--------|-------|-------|------|------|------|
| Baby T 230V | 1 x 1000 W | 1 x 1200 W | 10 A | 5.5 A | 10 A | 10 A |
| Baby T 110V | 1 x 1000 W | 2 x 600 W | 20 A | 9 A | 12 A | 20 A |

At a lower setting the steam boiler is the one held back, since the coffee
group has priority - so an unexpectedly low value can look like poor steam
recovery. The test machine (Baby T Plus 230V) reads **1**.

## Boiler PID parameters (offsets 55-61 and 65-71)

The machine's programming menu exposes four temperature-control parameters,
**P / I / d / b**, alongside Parameter CE. The memory map has exactly four
u16s directly after each boiler's setpoint, in two identically shaped blocks:

| Block | Setpoint | P | I | d | b |
|-------|----------|---|---|---|---|
| Coffee | 53 (92.0 C) | 55 = 30 | 57 = 15 | 59 = 40 | 61 = 10 |
| Steam | 63 (121.1 C) | 65 = 80 | 67 = 15 | 69 = 100 | 71 = 5 |

The count, the position and the fact that the steam boiler carries the looser
values all fit, but the identification is **inferred from structure, not
confirmed**, and the scaling of each term is documented nowhere. They are
exposed as hidden-by-default config numbers. Their 1-200 range is a guard
rail rather than a documented limit - 200 is twice the largest factory value
(steam d = 100) and 1 avoids a degenerate zero gain/band. Nothing here has
ever been written to a machine. Changing them
alters boiler regulation directly, so treat them as service parameters.

## Button naming

`S1` / `S2` are the short key's single and double selections, `L1` / `L2` the
long key's. This ordering is what offsets 41-44, 46-49 and 91-97 use, and it
is verified against the machine itself - note the manual's own prose lists
its four settings in a different order (S, L, S-double, L-double), which does
not reflect the byte order. The XL / continuous selection is a fifth button
with its own counter (150) and no dose or pre-infusion setting of its own.

Each selection therefore has two timings: the pump-ON pre-infusion at 46-49
and the pump-OFF soak at 41-44 that follows it.

## Notes on the constant regions

None of the bytes marked Unknown above ever change across any dump taken, so
none of them carries live state.

The five-slot reading of the timing arrays is confirmed. The machine has five
selections (S1, S2, L1, L2 and XL), and both arrays carry a fifth entry - 45
after the four soak times, 50 after the four pump-on times. Writing 2.0 s to
each was accepted and read back, so they are real registers rather than
padding, which leaves 51 as the only true pad byte in that stretch. They are
inert all the same: with both set, an XL delivery still pumped straight
through with no pause, so the continuous-delivery path ignores them, exactly
as the machine's documentation says. Both were restored to 0 and are exposed
read-only.

The three u16s reading 6000 (99, 109, 119) sit one field ahead of each dose
block, and 99-123 as a whole holds the Group 2/3 defaults that a Baby T never
uses.
## The pump-off soak (offsets 41-44)

These are settable, and the setting audibly changes the pause between the
pump-ON pre-infusion and the main shot. Established on hardware:

| | |
|---|---|
| Valid range | **0.0 - 5.0 s** (raw 0-50), the same range as the pump-ON times |
| Granularity | tenths of a second - 2.5 s and 3.1 s both store fine |
| Default | 3.0 s on all four |
| Above 5.0 s | refused: the machine raises a visible fault (blinking lights, but it keeps brewing) **and resets all four registers to 3.0 s** |

The reset-on-overflow is worth knowing about, because it makes a rejected
write look like a write that silently did nothing - the register you aimed at
reads 3.0 s afterwards whatever it held before, and so do its three
neighbours. Combined with the bridge updating its entities optimistically on
the machine's `OK`, an out-of-range write appears to succeed for one refresh
and then "revert". Every early attempt here used 5.8 s or 6.0 s, i.e. above
the limit, which is why the setting was briefly written off as read-only.

A write is acknowledged with `OK` either way, so `OK` is not evidence the
value was accepted - always read the register back.

Offsets 45 and 50 (the fifth, XL slots) read 0 and have never been shown to
accept a write; they stay read-only.

## Address space

**The address is masked to 11 bits.** Only the low `0x7FF` is decoded and the
rest of the address is discarded, for reads and writes alike: `r10290005` and
`rA0290005` both return the same bytes as `r00290005`, and writing to `0x1029`
changes offset `0x029`. So the space is **2048 bytes, aliased 32 times** over
the 16-bit address field. (A first pass concluded 12 bits, having only tested
addresses like `0x1000` and `0x2000` that alias to zero under either mask; a
full sweep settled it - every byte at `+2048` is identical to its counterpart
below, so bit 11 is ignored too, while `0x400` is not aliased.)

Reading all 2048 bytes finds data in exactly two places: offset **1** (the
`0x55` marker) and **32-219** (the settings block). Every other byte reads
`FF`. There is no second data region anywhere.

**`0xA000` is the one exception, and only when writing.** The clock command
(`w A000 0007`, see protocol.md) is special-cased by the module before the
address is masked: it sets the real-time clock rather than writing to
offset 0. Two independent observations confirm this. Reading `0xA000`
returns offset 0's content, so the read path has no such special case - which
is why the clock cannot be read back at all. And the machine's clock has been
synced from the app, yet offsets 0-6 still read `FF 55 FF FF FF FF FF`; had
the write been masked they would be holding a timestamp.

That distinction matters: if the clock write *were* masked it would land on
offsets 0-6, including the `0x55` at offset 1, which looks like a
"memory initialised" marker. Nothing here has ever written to offset 1, and
nothing should.

## Known gaps

**The machine's pairing PIN is a documented default**, printed in the manual
as the authorisation code for the app rather than being unique per machine.

The advertised Bluetooth name is `ASCASOXXXX`, where the manual describes the
digits as the serial number of the *Bluetooth module* - not necessarily the
machine number on the rating plate, although they matched on the unit tested.
That is what the bridge's "Machine Number" is derived from.

