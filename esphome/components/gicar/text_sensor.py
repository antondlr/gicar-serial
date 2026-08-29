import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import text_sensor

from . import CONF_GICAR_ID, GicarBridge, gicar_ns

GicarTextSensor = gicar_ns.class_("GicarTextSensor", text_sensor.TextSensor)

# Read-only categorical fields (see memory_map.cpp's extract_text for the
# byte->string mapping). Most have a writable switch/select twin - the default
# config only uses the ones that don't.
TEXT_FIELDS = [
    "serial_number",
    "machine_number",
    "model",
    "power_state",
    "steam_state",
    "temperature_unit",
    "shot_timer_enabled",
    "flush_enabled",
    "pre_infusion_enabled",
    "water_connection",
    "exposition_mode",
    # Bridge-side (not from the memory map): connection state and the unit
    # the scan found, e.g. "ASCASO0000 (00:00:00:00:00:00)".
    "bluetooth_status",
    "bluetooth_device",
]

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_GICAR_ID): cv.use_id(GicarBridge),
        **{
            cv.Optional(key): text_sensor.text_sensor_schema(GicarTextSensor)
            for key in TEXT_FIELDS
        },
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_GICAR_ID])
    for key in TEXT_FIELDS:
        if key not in config:
            continue
        sens = await text_sensor.new_text_sensor(config[key])
        cg.add(sens.set_key(key))
        cg.add(sens.set_gicar_parent(parent))
