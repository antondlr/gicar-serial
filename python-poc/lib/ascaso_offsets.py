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
    "language": {
        "offset": 36,
        "type": "u8",
        "description": "Language",
        "values": {
            "lang1": "1",
            "lang2": "2",
            "unknown": "value > 2"
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
    "steam_temperature": {
        "offset": 63,
        "type": "u16le", 
        "description": "Steam temperature (value/10)",
        "min": 110,  # in Celsius
        "max": 130,  # in Celsius
        "default": 125,
        "multiplier": 10  # Multiply by 10 for storage
    },
    "offset_temperature": {
        "offset": 77, ## this is wrong
        "type": "u16le",
        "description": "Offset temperature (value/10)",
        "multiplier": 10  # Multiply by 10 for storage
    },
    "standby_temperature": {
        "offset": 82,
        "type": "u16le",
        "description": "Standby temperature (value/10)",
        "multiplier": 10  # Multiply by 10 for storage
    },
    "standby_time": {
        "offset": 79,
        "type": "u8",
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

    "flush_enabled": {
        "offset": 43,
        "type": "u8",
        "description": "flush enabled flag",
        "values": {
            "enabled": "1",
            "disabled": 0
        }
    },

    # Pre-infusion settings
    "pre_infusion_enabled": {
        "offset": 45,
        "type": "u8",
        "description": "Pre-infusion enabled flag",
        "values": {
            "enabled": "1",
            "disabled": 0
        }
    },
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
        "description": "Water connection type",
        "values": {
            "direct": 0,
            "tank": 1
        }
    },
    # Auto on-off timer settings
    "autotimer_enabled": {
        "offset": 126,
        "type": "u8",
        "description": "Power timer enabled",
        "values": {
            "enabled": 1,
            "disabled": 0
        }
    },
    "autotimer_h_on": {
        "offset": 127,
        "type": "u8",
        "description": "Power timer on hour"
    },
    "autotimer_m_on": {
        "offset": 128,
        "type": "u8",
        "description": "Power timer on minute"
    },
    "autotimer_h_off": {
        "offset": 129,
        "type": "u8",
        "description": "Power timer off hour"
    },
    "autotimer_m_off": {
        "offset": 130,
        "type": "u8",
        "description": "Power timer off minute"
    },

    # Counter values (`COUNT_K*_GR1_ADDRESS`)
    "counter_S1": {
        "offset": 134,
        "type": "u16le",
        "description": "S1 counter",
        "readonly": True
    },
    "counter_S2": {
        "offset": 138,
        "type": "u16le",
        "description": "S2 counter",
        "readonly": True
    },
    "counter_L1": {
        "offset": 142,
        "type": "u16le",
        "description": "L1 counter",
        "readonly": True
    },
    "counter_L2": {
        "offset": 146,
        "type": "u16le",
        "description": "L2 counter",
        "readonly": True
    },
    "counter_XL": {
        "offset": 150,
        "type": "u16le",
        "description": "XL counter",
        "readonly": True
    },
    "counter_total": {
        "offset": 210,
        "type": "u16le",
        "description": "Total counter",
        "readonly": True
    }
}

# Machine models
MACHINE_MODELS = {
    1: "Baby T Zero 230V",
    2: "Baby T Plus 230V",
    3: "Baby T Zero 120V",
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
