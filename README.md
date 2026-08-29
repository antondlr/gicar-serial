### What is this?

Information about the serial protocol used by ~~select Gicar-based espresso machines~~ the Ascaso Baby T espresso machine.  
There's a working python implementation to read or adjust settings, and an **ESPHome bridge** that puts the whole machine in Home Assistant over the machine's own Bluetooth - see below.

### Why?

There's 2 ways to program this machine: by pressing a LOT of buttons, or by using the bluetooth interface and an app. 
The app would be really useful, if it actually worked as advertised. In my experience:  
- the iOS app doesn't work at all.  
- the android app *kinda* works. Clunky UI but gets the job done. I only have access to a frustratingly slow, old, android tablet though.  
- for the app to work, you'd need to forget and re-pair the device every. single. time. This seems to be a bug or design flaw in the serial-to-bluetooth bridge adapter.

**Newer machines probably don't have this problem.** A revision list attributed to Espressopool, [reproduced on Kaffee-Netz](https://www.kaffee-netz.de/threads/ascaso-duo-pdi-vs-baby-t-zero.147872/page-4/), says a new Bluetooth chip was fitted from **serial 362 onward** - Ascaso doesn't publish the breakpoint, so it's dealer information, but it lines up with who complains. The machines that are hard to discover and hard to stay connected to are the early ones. If yours is a later unit, ignore the moaning above.

### What have you found?

The manufacturer wasn't exaggerating when they claimed the Baby T uses "the same internals as the big boy professional machines"!    
Control board is a Gicar `3d5 Maestro Deluxe Full Range "664" 3SSR`, capable of driving 3 group heads, which is the same as in their flagship model (Big Dream).    

This is where it gets interesting: The bluetooth daughter board (which is ESP32 based and actually capable of bluetooth + wifi) is just acting as a serial bridge. Commands sent and received through the app are 1:1 sent over serial to the main controller board.   
Turns our, the protocol is pretty straightforward, too. 

### What does it mean?

You can read or write the settings of your machine with your laptop, just pair with the bluetooth adapter and run the commands.  
Alternatively, connect directly to the serial port.  
Fair warning; while this seems to work fine for me, your machine may explode. Proceed at your own risk. No warranties given, etc. 

### ESPHome bridge

`esphome/` contains an ESPHome external component (`gicar`) and two configs:

- `gicar-bridge.yaml` - generic, flash it as-is to any classic ESP32 (WROOM/devkit; not S2/S3/C3, they lack classic Bluetooth):
  ```
  cd esphome && esphome run gicar-bridge.yaml
  ```
  On first boot it opens the **Gicar Bridge Setup** WiFi hotspot with a captive portal to pick your network. Pick it, and that should be the whole setup: the pairing PIN the manual documents (`8483`) is built in, so the bridge finds any `ASCASO*` device, pairs and starts reading on its own. If your machine wants a different PIN, set it in the **Bluetooth PIN** entity at `http://gicar-bridge.local` and it's kept in flash. Add it to Home Assistant via the ESPHome integration (auto-discovered).
- `ascaso-bridge.yaml` - example of a personalised instance: includes the generic one as a package and adds WiFi credentials + PIN from `secrets.yaml` (copy `secrets.yaml.example`).

What you get: power / steam boiler / coffee group switches, auto start & shutdown (on/off + HH:MM), dose, pre-infusion and pre-infusion soak per button, flush / pre-infusion / shot-timer toggles, coffee / steam / offset / standby temperatures, standby time, counters (per button, resettable total, lifetime total, reset), temperature unit, and hidden-by-default groups for the boiler PID parameters and machine config (model, water supply, level probe, boiler fill timeout, parameter CE, exposition mode). Plus clock sync from NTP, a machine restart / Bluetooth reconnect pair, and an automatic recovery reboot if the Bluetooth stack wedges. Every write is an atomic single-field write followed by a full re-read, so what you see is always the machine's actual state.

There's also a `raw_command` API action (deliberately not an entity, so it adds nothing to Home Assistant) that sends an arbitrary protocol command and logs the reply - see `python-poc/raw_cmd.py`. 

Completely unintrusive: nothing is wired into the machine. The ESP32 talks to the machine's own Bluetooth module exactly like the vendor app would - the only "modification" is that the app can't be connected at the same time (the module accepts one client).

That convenience costs a hop, though. The full path for a single setting is:

```
Home Assistant --WiFi--> our ESP32 --classic BT--> OEM Bluetooth daughterboard --RS232--> Gicar control board
```

The daughterboard is itself an ESP32 doing nothing but relaying bytes to the control board's serial port, so every read crosses two radios and a serial link to reach a board that is three inches away from it. The Bluetooth hop is also the unreliable one: it is the link that drops, that needs re-pairing, and that occasionally wedges hard enough to need a reboot. Replacing the daughterboard with our own ESP32 wired straight to the control board's `CN13` RS232 header would delete the middleman and the whole class of Bluetooth problems with it - it needs a MAX3232-class level shifter and a 12V->5V buck, and the protocol work in this repo would carry over unchanged. Worth doing if you are comfortable inside the machine; the Bluetooth route is what you want if you are not.

Things the vendor app can't do:

- **Pre-infusion soak time.** Each button has a pump-ON pre-infusion time *and* a pump-OFF soak that follows it, and the soak is settable from 0.0 to 5.0 s (default 3.0). Neither the app nor the machine's own keypad menu offers it - the manual just says the pause "is always 3 s". It is the one setting here that changes how the shot is pulled rather than just how much comes out, so it is worth playing with. Write a value above 5.0 s and the machine raises a fault and resets all four buttons to 3.0 s, so the entities are bounded to the range it accepts.
- **Boiler PID parameters.** Four terms per boiler (P/I/d/b), hidden by default. The machine's keypad menu has them; the app never reads or writes those offsets. Treat them as service parameters - changing them alters boiler regulation, and there is no live temperature on this interface to judge the result by.
- **Shot timer toggle.** The stopwatch on the machine's display. Again in the keypad menu, absent from the app.
- **Counters that are actually correct.** The app's own 32-bit read multiplies two of the four bytes by zero, so it can only ever represent 16 bits and will misreport any counter past 65535. This reads them as real u32.

Underneath, a `raw_command` action can send any protocol command and log the reply, so probing something new doesn't need a firmware change.

Rough edges / not implemented:
- Only tested on one machine, a Baby T Plus 230V.
- Fahrenheit is not implemented - everything is Celsius (the machine stores Celsius internally regardless of the unit setting).
- **Only models 1-4 (the Baby T family) are supported.** The protocol covers eight models - Baby T One/Plus in 230V and 120V (1-4), Barista T 2/3 groups (5-6) and BigDream 2/3 groups (7-8) - but this component implements the Baby T layout only. Reading a Barista T or BigDream would produce wrong values, not an error, because on model >= 5 the machine switches **every u16 and u32 field to big-endian** while this code assumes little-endian throughout. Supporting them properly means: model-aware byte order; restoring chunked reads (their fields run from the weekly timer at offset 4 up to a maintenance alarm at 276, which is past the 250-byte single-response cap); and entities for the second and third groups, the weekly timer and the extra alarms. That is perhaps a day's work, but none of it can be verified without the hardware - and this machine faults visibly when it dislikes a write, so shipping an untested write path for a machine class nobody can test on would be worse than not shipping it. If you have a Barista T or a BigDream and want to help, that is the single most useful thing you could do.
- This interface stores configuration only - no boiler temperature, shot timer or alarms, all of which we checked for. Live values would need the other serial connection.
- The Bluetooth module on early machines is flaky (see the revision note above). The bridge scans, backs off and reconnects on its own, and reboots itself if the stack wedges outright, so it recovers unattended - but on a pre-362 machine expect the occasional dropped connection regardless.

### Can I help?

Yes, please! Feel free to submit PR's, fork the repo, etc. 

Here's an incomplete list in no particular order of nice-to-haves:  
- Confirm that other models or later makes of the baby T use the same board (or at least, same serial interface and protocol).  
- Add proper support for the Ascaso Barista T and Ascaso Big Dream (both are 2-3 group head machines. Current python POC has hardcoded offsets for the Baby T).  
- Add the _other_ serial connection that has the shot timer data, etc. That one is already documented by the Lelit community; search for Lelit MaraX mods.  
- Support for non-ascaso machines, there _must_ be others that are compatible as the vast majority of espresso machines are Gicar based. 
- Custom PCB would be pretty dope, i'd buy one.

### Python CLI Usage

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Reading machine state:**
```bash
# Read from cached state file (states/latest.txt)
python3 python-poc/ascaso_read.py

# Read from serial port (Bluetooth or USB)
python3 python-poc/ascaso_read.py --serial-port /dev/tty.AscasoBabyT

# Verbose output (all settings grouped by category)
python3 python-poc/ascaso_read.py --verbose

# JSON output
python3 python-poc/ascaso_read.py --json

# Filter results (e.g., only temperature-related values)
python3 python-poc/ascaso_read.py --verbose --filter temp

# Read custom memory offset (offset, size in bytes)
python3 python-poc/ascaso_read.py custom 53 2
```

**Writing settings:**
```bash
# Power on/off
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT power on
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT power off

# Set temperatures (in °C)
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT coffee-temp 93.5
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT steam-temp 140
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT standby-temp 80

# Steam on/off
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT steam on

# Temperature unit (C or F)
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT unit C

# Dose settings (S1, S2, L1, L2 in ml)
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT dose S1 30

# Pre-infusion time (S1, S2, L1, L2 in seconds, 0.0-9.9)
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT pre-infusion S1 3.0

# Autotimer
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT autotimer enable
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT autotimer disable
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT autotimer set --on-time 07:00 --off-time 22:00

# Dry-run mode (show command without sending)
python3 python-poc/ascaso_write.py --read-only power on

# Write to custom memory offset
python3 python-poc/ascaso_write.py --serial-port /dev/tty.AscasoBabyT custom 53 935 2
```

### Is this AI slop?

Yes. Yes it is. But it actually works, which is kinda mind blowing. 

### License

[Apache License 2.0](LICENSE). Do what you like with it, keep the notice, and
no warranty is given - see the "your machine may explode" caveat above, which
is not entirely a joke.

The protocol documentation here was worked out by observing the machine and
reading its manual. Nothing from the vendor's app is redistributed in this
repository.

