import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import datetime

from . import CONF_GICAR_ID, GicarBridge, gicar_ns

GicarAutotimerTime = gicar_ns.class_("GicarAutotimerTime", datetime.TimeEntity)

# (hour_offset, minute_offset): 127/128 for auto-on, 129/130 for auto-off
# (same offsets as MEMORY_MAP's autotimer_h_on/m_on/h_off/m_off).
AUTOTIMER_TIME_FIELDS = {
    "autotimer_on_time": (127, 128),
    "autotimer_off_time": (129, 130),
}

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_GICAR_ID): cv.use_id(GicarBridge),
        **{
            cv.Optional(key): datetime.time_schema(GicarAutotimerTime)
            for key in AUTOTIMER_TIME_FIELDS
        },
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_GICAR_ID])
    for key, (hour_offset, minute_offset) in AUTOTIMER_TIME_FIELDS.items():
        if key not in config:
            continue
        var = await datetime.new_datetime(config[key])
        cg.add(var.set_offsets(hour_offset, minute_offset))
        cg.add(var.set_gicar_parent(parent))
