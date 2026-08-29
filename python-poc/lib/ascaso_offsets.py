"""
Ascaso Baby T Memory Map

This module contains a dictionary of known memory offsets and default values
for the Ascaso Baby T espresso machine.
"""

# Memory map for Ascaso Baby T
MEMORY_MAP = {
    # Model information
    "model": {
        "offset": 76,
        "type": "u8",
        "description": "Machine model",
        "values": {
            "baby_t": "0 < value < 5",
            "barista": "value == 5",
            "barista_3": "value == 6",
            "big_dream": "value == 7",
            "big_dream_3": "value == 8"
        }
    },

    # Machine states
    # get:   if (nibbleAdapter.getCharAt(STATO_MACCHINA_ADDRESS) <= 4) {
    #        this.StatoMacchina = 0;
    #    } else {
    #        this.StatoMacchina = 1;
    #    }
    # set:   if (this.StatoMacchina == 0) {
    #        nibbleAdapter.setCharAt(4, STATO_MACCHINA_ADDRESS);
    #    } else {
    #        nibbleAdapter.setCharAt(6, STATO_MACCHINA_ADDRESS);
    #    }
    "power_state": { 
        "offset": 132,
        "type": "u8",
        "description": "Machine power state",
        "values": {
            "on": 6,
            "off": 4
        }
    },
    "steam_state": {
        "offset": 86,
        "type": "u8",
        "description": "Steam boiler state",
        "values": {
            "on": 1,
            "off": 0
        }
    },
    "coffee_group_state": {
        "offset": 124,
        "type": "u8",
        "description": "Coffee group state",
        "values": {
            "on": "value > 0",
            "off": 0
        }
    },
    
    # Temperature settings
    "temperature_unit": {
        "offset": 52,
        "type": "u8",
        "description": "Temperature unit setting",
        "values": {
            "celsius": 0,
            "fahrenheit": 1
        }
    },
    "coffee_temperature": {
        "offset": 53,
        "type": "u16le",
        "description": "Coffee temperature (value/10)",
        "min": 80,  # in Celsius
        "max": 110,  # in Celsius
        "default": 93,
        "multiplier": 10  # Multiply by 10 for storage
    },
    # Boiler PID parameters: four u16s directly after each boiler setpoint,
    # matching the four (P/I/d/b) the machine's programming menu exposes.
    # Scaling undocumented.
    "pid_coffee_p": {"offset": 55, "type": "u16le", "description": "Coffee boiler PID P"},
    "pid_coffee_i": {"offset": 57, "type": "u16le", "description": "Coffee boiler PID I"},
    "pid_coffee_d": {"offset": 59, "type": "u16le", "description": "Coffee boiler PID d"},
    "pid_coffee_b": {"offset": 61, "type": "u16le", "description": "Coffee boiler PID b"},
    "pid_steam_p": {"offset": 65, "type": "u16le", "description": "Steam boiler PID P"},
    "pid_steam_i": {"offset": 67, "type": "u16le", "description": "Steam boiler PID I"},
    "pid_steam_d": {"offset": 69, "type": "u16le", "description": "Steam boiler PID d"},
    "pid_steam_b": {"offset": 71, "type": "u16le", "description": "Steam boiler PID b"},
    "steam_temperature": {
        "offset": 63,
        "type": "u16le", 
        "description": "Steam temperature (value/10)",
        "min": 110,  # in Celsius
        "max": 130,  # in Celsius
        "default": 125,
        "multiplier": 10  # Multiply by 10 for storage
    },
    # "Offset temperature" as the machine displays it is
    #   (byte79 == 0 or model >= 5) ? u16@89 / 10 : (u16@77 - 99) / 10
    # i.e. byte 79 selects which register is live. Both raw registers are
    # exposed here; ascaso_read.py derives the displayed value as
    # "offset_temperature". (An earlier version read 77/10 unconditionally.)
    "offset_temperature_register_select": {
        "offset": 79,
        "type": "u8",
        "description": "0 = offset temperature lives at 89, non-zero = at 77"
    },
    "offset_temperature_alt": {
        "offset": 77,
        "type": "u16le",
        "description": "Alt offset temperature register: (value - 99) / 10, only live when byte 79 != 0"
    },
    "group1_temperature_offset": {
        "offset": 89,
        "type": "u16le",
        "description": "Group 1 temperature offset (value/10), the normal offset-temperature register",
        "multiplier": 10
    },
    # From the original project notes. Reads consistently with the machine
    # menu; write unverified.
    "shot_timer_enabled": {
        "offset": 80,
        "type": "u8",
        "description": "Shot timer",
        "values": {
            "disabled": 0,
            "enabled": 1
        }
    },
    "standby_temperature": {
        "offset": 82,
        "type": "u16le",
        "description": "Standby (economy) temperature (value/10), 80-125",
        "multiplier": 10  # Multiply by 10 for storage
    },
    "standby_time": {
        # u16, not u8 - a u8 read here silently drops the high byte
        # (offset 85) whenever the real value needs it.
        "offset": 84,
        "type": "u16le",
        "description": "Standby time in minutes"
    },
    
    # Dose settings
    "dose_S1": {
        "offset": 91,
        "type": "u16le",
        "description": "S1 dose in ml (value/2)",
        "multiplier": 2  # Multiply by 2 for storage
    },
    "dose_S2": {
        "offset": 93,
        "type": "u16le", 
        "description": "S2 dose in ml (value/2)",
        "multiplier": 2
    },
    "dose_L1": {
        "offset": 95,
        "type": "u16le",
        "description": "L1 dose in ml (value/2)",
        "multiplier": 2
    },
    "dose_L2": {
        "offset": 97,
        "type": "u16le",
        "description": "L2 dose in ml (value/2)",
        "multiplier": 2
    },

    # Offset fixed to 38 (was 43), verified on hardware.
    "flush_enabled": {
        "offset": 38,
        "type": "u8",
        "description": "flush enabled flag",
        "values": {
            "enabled": 1,
            "disabled": 0
        }
    },

    # Pre-infusion settings
    # Offset fixed to 40 (was 45), verified on hardware.
    "pre_infusion_enabled": {
        "offset": 40,
        "type": "u8",
        "description": "Pre-infusion enabled flag",
        "values": {
            "enabled": 1,
            "disabled": 0
        }
    },
    # Pump-OFF (soak) time per selection - 3.0 s on every dump taken.
    "pre_infusion_soak_S1": {"offset": 41, "type": "u8", "multiplier": 10, "description": "S1 pump-off soak time"},
    "pre_infusion_soak_S2": {"offset": 42, "type": "u8", "multiplier": 10, "description": "S2 pump-off soak time"},
    "pre_infusion_soak_L1": {"offset": 43, "type": "u8", "multiplier": 10, "description": "L1 pump-off soak time"},
    "pre_infusion_soak_L2": {"offset": 44, "type": "u8", "multiplier": 10, "description": "L2 pump-off soak time"},
    # Experimental: fifth slot of each array, i.e. the XL selection. Both read 0.
    "pre_infusion_soak_XL": {"offset": 45, "type": "u8", "multiplier": 10, "description": "XL pump-off soak time (experimental)"},
    "pre_infusion_S1": {
        "offset": 46,
        "type": "u8",
        "description": "S1 pre-infusion time in seconds (value/10)",
        "default": 3.0,
        "multiplier": 10  # Multiply by 10 for storage
    },
    "pre_infusion_S2": {
        "offset": 47,
        "type": "u8",
        "description": "S2 pre-infusion time in seconds (value/10)",
        "multiplier": 10
    },
    "pre_infusion_L1": {
        "offset": 48,
        "type": "u8",
        "description": "L1 pre-infusion time in seconds (value/10)",
        "multiplier": 10
    },
    "pre_infusion_XL": {"offset": 50, "type": "u8", "multiplier": 10, "description": "XL pre-infusion (experimental)"},
    "pre_infusion_L2": {
        "offset": 49,
        "type": "u8",
        "description": "L2 pre-infusion time in seconds (value/10)",
        "multiplier": 10
    },
    
    # Water settings
    "water_connection": {
        "offset": 87,
        "type": "u8",
        "description": "Water supply (0 = direct connection, 1 = tank)",
        "values": {
            "direct": 0,
            "tank": 1
        }
    },
    # Auto on-off timer settings. There is NO enable flag on a Baby T: the
    # machine treats hour/minute == 100 as "not set" and disabling writes
    # 100/100. Byte 126 is "Group 3 enable" on the multi-group models.
    "group3_enabled": {
        "offset": 126,
        "type": "u8",
        "description": "Group 3 enable (model 5+ only; not the autotimer flag)",
        "values": {
            "enabled": 1,
            "disabled": 0
        }
    },
    "autotimer_h_on": {
        "offset": 127,
        "type": "u8",
        "description": "Power timer on hour (100 = not set)"
    },
    "autotimer_m_on": {
        "offset": 128,
        "type": "u8",
        "description": "Power timer on minute"
    },
    "autotimer_h_off": {
        "offset": 129,
        "type": "u8",
        "description": "Power timer off hour (100 = not set)"
    },
    "autotimer_m_off": {
        "offset": 130,
        "type": "u8",
        "description": "Power timer off minute"
    },

    # Counter values - 4-byte slots (a reset writes u32 zeros). Slot 5 (150)
    # is the flush / continuous ("XL") button counter.
    "counter_S1": {"offset": 134, "type": "u32le", "description": "S1 counter", "readonly": True},
    "counter_S2": {"offset": 138, "type": "u32le", "description": "S2 counter", "readonly": True},
    "counter_L1": {"offset": 142, "type": "u32le", "description": "L1 counter", "readonly": True},
    "counter_L2": {"offset": 146, "type": "u32le", "description": "L2 counter", "readonly": True},
    "counter_flush": {"offset": 150, "type": "u32le", "description": "Flush (continuous) counter", "readonly": True},
    # The machine's own resettable total (its counter menu's running total).
    "counter_total": {"offset": 206, "type": "u32le", "description": "Total counter", "readonly": True},
    # Lifetime total; a counter reset leaves this one alone.
    "counter_lifetime": {"offset": 210, "type": "u32le", "description": "Lifetime counter", "readonly": True},
    # Has mirrored counter_lifetime exactly in every dump taken so far.
    "serial_number": {"offset": 34, "type": "u16le", "description": "Serial number", "readonly": True},
    "counter_water": {"offset": 214, "type": "u32le", "description": "Water counter", "readonly": True},
    # Tea counters use 4-byte slots like the button counters; zero on a Baby T Plus.
    "counter_tea_1": {"offset": 194, "type": "u32le", "description": "Tea 1 counter", "readonly": True},
    "counter_tea_2": {"offset": 198, "type": "u32le", "description": "Tea 2 counter", "readonly": True},

    # Barista/Big Dream (model >= 5) settings that the vendor app never shows
    # for a Baby T. They read back plausibly on a Baby T.
    "level_probe": {
        "offset": 33,
        "type": "u8",
        "description": "Water level probe sensitivity",
        "values": {
            "low": 0,
            "medium": 1,
            "high": 2
        }
    },
    "boiler_fill_timeout": {
        "offset": 73,
        "type": "u8",
        "description": "Boiler filling-up timeout (0-240)"
    },
    "parameter_ce": {
        "offset": 81,
        "type": "u8",
        "description": "Parameter CE (0-6; meaning unknown)"
    },
    # Showroom/demo mode (a Barista/Big Dream setting).
    "exposition_mode": {
        "offset": 133,
        "type": "u8",
        "description": "Exposition (showroom/demo) mode",
        "values": {
            "enabled": 1,
            "disabled": 0
        }
    }
}

# Machine models
MACHINE_MODELS = {
    # Model names as shown by the machine / vendor app
    1: "Baby T One 230V",
    2: "Baby T Plus 230V",
    3: "Baby T One 120V",
    4: "Baby T Plus 120V",
    5: "Barista T 2 Groups",
    6: "Barista T 3 Groups",
    7: "Big Dream 2 Groups",
    8: "Big Dream 3 Groups"
}

# Default response if a file can't be loaded
DEFAULT_RESPONSE = (
    "r000500D7"
    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
    "0101020200010100011E1E1E1E002600282D000000A2031E000F0028000A00"
    "E30450000F006400050078000002D101000102F2032D00010101000068006A008E006801"
    "70176E00DC0096002C0170176E00DC0096002C017017080C1001010164646464000600010000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000030000009E1E00009E1E00000000"
    "E7"
)
