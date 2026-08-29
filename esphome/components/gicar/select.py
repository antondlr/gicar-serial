import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import select

from . import CONF_GICAR_ID, GicarBridge, gicar_ns

GicarSelect = gicar_ns.class_("GicarSelect", select.Select)

# Dropdown (list-type) settings. Each entry is
# (offset, [(option label, raw byte), ...]).
SELECT_FIELDS = {
    # Raw model byte (76). Changing it changes how the machine
    # interpret other fields (endianness for u16/u32 on model>=5, group
    # count, temperature layout) - only for repurposing a board to a
    # different machine. Exposed as diagnostic for that reason.
    "model": (
        76,
        [
            ("Baby T One 230V", 1),
            ("Baby T Plus 230V", 2),
            ("Baby T One 120V", 3),
            ("Baby T Plus 120V", 4),
            ("Barista T 2 Groups", 5),
            ("Barista T 3 Groups", 6),
            ("Big Dream 2 Groups", 7),
            ("Big Dream 3 Groups", 8),
        ],
    ),
    # Display unit only - the machine always stores Celsius*10. Our entities
    # always report Celsius (Fahrenheit display is not implemented here).
    "temperature_unit": (52, [("Celsius", 0), ("Fahrenheit", 1)]),
    # Baby T One (models 1/3) is tank-only; Plus (2/4) can use either.
    "water_connection": (87, [("Direct Connection", 0), ("Tank", 1)]),
    # Barista/Big Dream setting - see memory_map.cpp note.
    "level_probe": (33, [("Low", 0), ("Medium", 1), ("High", 2)]),
}

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_GICAR_ID): cv.use_id(GicarBridge),
        **{cv.Optional(key): select.select_schema(GicarSelect) for key in SELECT_FIELDS},
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_GICAR_ID])
    for key, (offset, options) in SELECT_FIELDS.items():
        if key not in config:
            continue
        sel = await select.new_select(config[key], options=[label for label, _ in options])
        cg.add(sel.set_write_params(offset, [raw for _, raw in options]))
        cg.add(sel.set_gicar_parent(parent))
