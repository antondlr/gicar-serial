import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import switch

from . import CONF_GICAR_ID, GicarBridge, gicar_ns

GicarSwitch = gicar_ns.class_("GicarSwitch", switch.Switch)
GicarAutotimerEnableSwitch = gicar_ns.class_("GicarAutotimerEnableSwitch", switch.Switch)

# (offset, on_value, off_value) - offset/on/off match the "values" mapping of
# the same field in python-poc/lib/ascaso_offsets.py's MEMORY_MAP. Provenance
# per field is documented in memory_map.cpp's extract_text().
WRITABLE_SWITCH_FIELDS = {
    "power_state": dict(offset=132, on_value=6, off_value=4),
    "steam_state": dict(offset=86, on_value=1, off_value=0),
    # Group 1 enable. Turning it off leaves the steam boiler heating while the
    # coffee group stays cold - the machine's own "coffee group" setting.
    "coffee_group_state": dict(offset=124, on_value=1, off_value=0),
    "flush_enabled": dict(offset=38, on_value=1, off_value=0),
    "pre_infusion_enabled": dict(offset=40, on_value=1, off_value=0),
    # From the original project notes - reads back consistently with the
    # machine's menu, write unverified.
    "shot_timer_enabled": dict(offset=80, on_value=1, off_value=0),
    # Showroom/demo mode (a Barista/Big Dream setting).
    "exposition_mode": dict(offset=133, on_value=1, off_value=0),
}

# (hour_offset, minute_offset, default hour when enabling with no remembered
# time). Same offsets as datetime.py's AUTOTIMER_TIME_FIELDS.
AUTOTIMER_SWITCH_FIELDS = {
    "autotimer_on_enabled": (127, 128, 7),
    "autotimer_off_enabled": (129, 130, 11),
}

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_GICAR_ID): cv.use_id(GicarBridge),
        **{cv.Optional(key): switch.switch_schema(GicarSwitch) for key in WRITABLE_SWITCH_FIELDS},
        **{
            cv.Optional(key): switch.switch_schema(GicarAutotimerEnableSwitch)
            for key in AUTOTIMER_SWITCH_FIELDS
        },
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_GICAR_ID])
    for key, params in WRITABLE_SWITCH_FIELDS.items():
        if key not in config:
            continue
        sw = await switch.new_switch(config[key])
        cg.add(sw.set_write_params(params["offset"], params["on_value"], params["off_value"]))
        cg.add(sw.set_gicar_parent(parent))
    for key, (hour_offset, minute_offset, default_hour) in AUTOTIMER_SWITCH_FIELDS.items():
        if key not in config:
            continue
        sw = await switch.new_switch(config[key])
        cg.add(sw.set_offsets(hour_offset, minute_offset, default_hour))
        cg.add(sw.set_gicar_parent(parent))
