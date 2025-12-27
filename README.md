### What is this?

Information about the serial protocol used by ~~select Gicar-based espresso machines~~ the Ascaso Baby T espresso machine  
There's also a working python implementation, to read or adjust settings.

### Why?

There's 2 ways to program this machine: by pressing a LOT of buttons, or by using the bluetooth interface and an app. 
The app would be really useful, if it actually worked as advertised. In my experience:  
- the iOS app doesn't work at all.  
- the android app *kinda* works. Clunky UI but gets the job done. I only have access to a frustratingly slow, old, android tablet though.  
- for the app to work, you'd need to forget and re-pair the device every. single. time. This seems to be a bug or design flaw in the serial-to-bluetooth bridge adapter.

### What have you found?

The manufacturer wasn't exaggerating when they claimed the Baby T uses "the same internals as the big boy professional machines"!    
Control board is a Gicar `3d5 Maestro Deluxe Full Range "664" 3SSR`, capable of driving 3 group heads, which is the same as in their flagship model (Big Dream).    

This is where it gets interesting: The bluetooth daughter board (which is ESP32 based and actually capable of bluetooth + wifi) is just acting as a serial bridge. Commands sent and received through the app are 1:1 sent over serial to the main controller board.   
Turns our, the protocol is pretty straightforward, too. 

### What does it mean?

You can read or write the settings of your machine with your laptop, just pair with the bluetooth adapter and run the commands.  
Alternatively, connect directly to the serial port.  
Fair warning; while this seems to work fine for me, your machine may explode. Proceed at your own risk. No warranties given, etc. 

### Can I help?

Yes, please! Feel free to submit PR's, fork the repo, etc. 

Here's an incomplete list in no particular order of nice-to-haves:  
- Confirm that other models or later makes of the baby T use the same board (or at least, same serial interface and protocol).  
- Port to ESPHome... this would be awesome, if I ever find some time i may take a crack at it. 
- Add proper support for the Ascaso Barista T and Ascaso Big Dream (both are 2-3 group head machines. Current python POC has hardcoded offsets for the Baby T).  
- Add the _other_ serial connection that has the shot timer data, etc. This protocol has been properly reverse engineered already; search for Lelit mods.  
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
