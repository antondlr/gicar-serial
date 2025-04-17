# Ascaso Baby T (and others) Memory Map

| Address | Length | Description | Value Format | Model Compatibility | Notes |
|---------|--------|-------------|--------------|---------------------|-------|
| 1 | 1 | Reset | Boolean | All | |
| 4 | 1 | Monday Auto On Hour | Integer (0-23) | Model 5+ | Weekly timer |
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
| 33 | 1 | Level Probe | Integer | All | |
| 36 | 1 | Language | Integer | All | Values: 1, 2 |
| 43 | 1 | Flush Enabled | Boolean | All | 0=Disabled, 1=Enabled |
| 45 | 1 | Pre-infusion Enabled | Boolean | All | 0=Disabled, 1=Enabled |
| 46 | 1 | Group 1 Short Shot 1 Pre-infusion | Integer | Models 1-4 | Value * 10 (seconds) |
| 47 | 1 | Group 1 Short Shot 2 Pre-infusion | Integer | Models 1-4 | Value * 10 (seconds) |
| 48 | 1 | Group 1 Long Shot 1 Pre-infusion | Integer | Models 1-4 | Value * 10 (seconds) |
| 49 | 1 | Group 1 Long Shot 2 Pre-infusion | Integer | Models 1-4 | Value * 10 (seconds) |
| 52 | 1 | Temperature Unit | Boolean | All | 0=Celsius, 1=Fahrenheit |
| 53 | 2 | Group 1 Coffee Temperature | Integer | Models 1-4 | Value * 10 (e.g., 93.0°C = 930) |
| 63 | 2 | Steam Temperature | Integer | All | Value * 10 |
| 73 | 1 | Boiler Fill Timeout | Integer | All | |
| 74 | 1 | Filter Alarm | Integer | All | |
| 76 | 1 | Model Information | Integer | All | Stores model number (1-8) |
| 77 | 2 | Temperature Offset | Integer | All | Value * 10 |
| 79 | 1 | Standby Time | Integer | All | Minutes |
| 81 | 1 | Parameter CE | Integer | All | |
| 82 | 2 | Economy Temperature | Integer | All | Value * 10 |
| 84 | 1 | Economy Timer | Integer | All | |
| 86 | 1 | Steam Boiler Enable | Boolean | All | 0=Off, 1=On |
| 87 | 1 | Water Source | Boolean | All | 0=Tank, 1=Plumbing |
| 89 | 2 | Group 1 Temperature Offset | Integer | Models 1-4 | Direct value * 10 |
| 91 | 2 | Group 1 Short Shot 1 Dose | Integer | All | Pulses * 2 = ml |
| 93 | 2 | Group 1 Short Shot 2 Dose | Integer | All | Pulses * 2 = ml |
| 95 | 2 | Group 1 Long Shot 1 Dose | Integer | All | Pulses * 2 = ml |
| 97 | 2 | Group 1 Long Shot 2 Dose | Integer | All | Pulses * 2 = ml |
| 101 | 2 | Group 2 Short Shot 1 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 103 | 2 | Group 2 Short Shot 2 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 105 | 2 | Group 2 Long Shot 1 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 107 | 2 | Group 2 Long Shot 2 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 111 | 2 | Group 3 Short Shot 1 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 113 | 2 | Group 3 Short Shot 2 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 115 | 2 | Group 3 Long Shot 1 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 117 | 2 | Group 3 Long Shot 2 Dose | Integer | Model 5+ | Pulses * 2 = ml |
| 124 | 1 | Group 1 Enable | Boolean | All | 0=Off, >0=On |
| 125 | 1 | Group 2 Enable | Boolean | Model 5+ | |
| 126 | 1 | Auto Timer Enable/Group 3 Enable | Boolean | All | 0=Disabled, 1=Enabled |
| 127 | 1 | Auto On Hour | Integer (0-23) | All | Daily timer |
| 128 | 1 | Auto On Minute | Integer (0-59) | All | Daily timer |
| 129 | 1 | Auto Off Hour | Integer (0-23) | All | Daily timer |
| 130 | 1 | Auto Off Minute | Integer (0-59) | All | Daily timer |
| 132 | 1 | Machine State | Integer | All | 4=Off, 6=On |
| 133 | 1 | Exposition Mode | Boolean | All | |
| 134 | 2 | Group 1 K1 Button Counter | Integer | All | |
| 138 | 2 | Group 1 K2 Button Counter | Integer | All | |
| 142 | 2 | Group 1 K3 Button Counter | Integer | All | |
| 146 | 2 | Group 1 K4 Button Counter | Integer | All | |
| 150 | 2 | Group 1 K5 Button Counter | Integer | All | |
| 154 | 2 | Group 2 K1 Button Counter | Integer | Model 5+ | |
| 158 | 2 | Group 2 K2 Button Counter | Integer | Model 5+ | |
| 162 | 2 | Group 2 K3 Button Counter | Integer | Model 5+ | |
| 166 | 2 | Group 2 K4 Button Counter | Integer | Model 5+ | |
| 170 | 2 | Group 2 K5 Button Counter | Integer | Model 5+ | |
| 174 | 2 | Group 3 K1 Button Counter | Integer | Model 5+ | |
| 178 | 2 | Group 3 K2 Button Counter | Integer | Model 5+ | |
| 182 | 2 | Group 3 K3 Button Counter | Integer | Model 5+ | |
| 186 | 2 | Group 3 K4 Button Counter | Integer | Model 5+ | |
| 190 | 2 | Group 3 K5 Button Counter | Integer | Model 5+ | |
| 194 | 2 | Tea 1 Counter | Integer | All | |
| 198 | 2 | Tea 2 Counter | Integer | All | |
| 210 | 2 | Total Coffee Counter | Integer | All | |
| 214 | 2 | Total Water Counter | Integer | All | |
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
