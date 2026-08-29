import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import sensor
from esphome.const import (
    DEVICE_CLASS_TEMPERATURE,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    UNIT_CELSIUS,
    UNIT_MINUTE,
    UNIT_SECOND,
)

from . import CONF_GICAR_ID, GicarBridge, gicar_ns

GicarSensor = gicar_ns.class_("GicarSensor", sensor.Sensor)

UNIT_MILLILITER = "mL"

# Read-only view of any numeric MEMORY_MAP key (python-poc/lib/
# ascaso_offsets.py). The default config only uses the counters - every
# other numeric field has a writable `number:` twin that already shows the
# value, so exposing both just clutters Home Assistant.
_TEMP = dict(
    unit_of_measurement=UNIT_CELSIUS,
    device_class=DEVICE_CLASS_TEMPERATURE,
    accuracy_decimals=1,
    state_class=STATE_CLASS_MEASUREMENT,
)
_COUNTER = dict(accuracy_decimals=0, state_class=STATE_CLASS_TOTAL_INCREASING)

NUMERIC_FIELDS = {
    "coffee_temperature": _TEMP,
    "steam_temperature": _TEMP,
    "offset_temperature": dict(unit_of_measurement=UNIT_CELSIUS, accuracy_decimals=1),
    "standby_temperature": _TEMP,
    "standby_time": dict(unit_of_measurement=UNIT_MINUTE, accuracy_decimals=0),
    "dose_S1": dict(unit_of_measurement=UNIT_MILLILITER, accuracy_decimals=0),
    "dose_S2": dict(unit_of_measurement=UNIT_MILLILITER, accuracy_decimals=0),
    "dose_L1": dict(unit_of_measurement=UNIT_MILLILITER, accuracy_decimals=0),
    "dose_L2": dict(unit_of_measurement=UNIT_MILLILITER, accuracy_decimals=0),
    "pre_infusion_S1": dict(unit_of_measurement=UNIT_SECOND, accuracy_decimals=1),
    "pre_infusion_S2": dict(unit_of_measurement=UNIT_SECOND, accuracy_decimals=1),
    "pre_infusion_L1": dict(unit_of_measurement=UNIT_SECOND, accuracy_decimals=1),
    "pre_infusion_L2": dict(unit_of_measurement=UNIT_SECOND, accuracy_decimals=1),
    # The XL slots stay read-only - unlike S1/S2/L1/L2 they have never been
    # shown to accept a write, and they read 0 either way.
    "pre_infusion_soak_XL": dict(unit_of_measurement=UNIT_SECOND, accuracy_decimals=1),
    "pre_infusion_XL": dict(unit_of_measurement=UNIT_SECOND, accuracy_decimals=1),
    "counter_S1": _COUNTER,
    "counter_S2": _COUNTER,
    "counter_L1": _COUNTER,
    "counter_L2": _COUNTER,
    "counter_flush": _COUNTER,
    # The machine's own resettable total (offset 206), cleared by Reset Counters.
    "counter_total": _COUNTER,
    # Lifetime total (offset 210), not affected by a counter reset.
    "counter_lifetime": _COUNTER,
    # Mirrors the lifetime counter in every dump taken so far - exposed to
    # see whether it is a true alias or a separate accumulator.
    "counter_water": _COUNTER,
    # Model 5+ / tea-equipped machines; read zero on a Baby T Plus.
    "counter_tea_1": _COUNTER,
    "counter_tea_2": _COUNTER,
    "boiler_fill_timeout": dict(accuracy_decimals=0),
    "parameter_ce": dict(accuracy_decimals=0),
}

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_GICAR_ID): cv.use_id(GicarBridge),
        **{
            cv.Optional(key): sensor.sensor_schema(GicarSensor, **opts)
            for key, opts in NUMERIC_FIELDS.items()
        },
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_GICAR_ID])
    for key in NUMERIC_FIELDS:
        if key not in config:
            continue
        sens = await sensor.new_sensor(config[key])
        cg.add(sens.set_key(key))
        cg.add(sens.set_gicar_parent(parent))
