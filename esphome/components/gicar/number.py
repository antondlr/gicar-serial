import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import number
from esphome.const import (
    DEVICE_CLASS_TEMPERATURE,
    UNIT_CELSIUS,
    UNIT_MINUTE,
    UNIT_SECOND,
)

from . import CONF_GICAR_ID, GicarBridge, gicar_ns

GicarNumber = gicar_ns.class_("GicarNumber", number.Number)
GicarReadIntervalNumber = gicar_ns.class_("GicarReadIntervalNumber", number.Number)

CONF_READ_INTERVAL = "read_interval"
UNIT_MILLILITER = "mL"

# Keys mirror python-poc/lib/ascaso_offsets.py's MEMORY_MAP (same table
# get_numeric() reads from). min/max match the ranges the vendor app accepts
# (Celsius) so HA can't push a value the machine would refuse. The
# temperature setpoints are stored as tenths of a degree, so 0.1 is both the
# machine's actual resolution and the step used here.
WRITABLE_NUMERIC_FIELDS = {
    "coffee_temperature": dict(
        unit_of_measurement=UNIT_CELSIUS,
        device_class=DEVICE_CLASS_TEMPERATURE,
        min_value=80,
        max_value=110,
        step=0.1,
    ),
    "steam_temperature": dict(
        unit_of_measurement=UNIT_CELSIUS,
        device_class=DEVICE_CLASS_TEMPERATURE,
        min_value=110,
        max_value=130,
        step=0.1,
    ),
    # -9.9..9.9 (Celsius). Which register it lands in (77 vs 89) is
    # decided at write time from the current payload - see memory_map.cpp.
    "offset_temperature": dict(
        unit_of_measurement=UNIT_CELSIUS,
        min_value=-9.9,
        max_value=9.9,
        step=0.1,
    ),
    # "Economy" temperature/timer in the machine's temperature menu.
    "standby_temperature": dict(
        unit_of_measurement=UNIT_CELSIUS,
        device_class=DEVICE_CLASS_TEMPERATURE,
        min_value=80,
        max_value=125,
        step=0.1,
    ),
    # Minutes of inactivity before the steam boiler drops to the standby
    # temperature; 0 disables standby entirely. The machine itself accepts up
    # to 999, but 6 h is well past any useful setting, so the entity caps
    # there to keep the slider usable.
    "standby_time": dict(unit_of_measurement=UNIT_MINUTE, min_value=0, max_value=360, step=1),
    # Doses are stored as u16 half-millilitre counts (multiplier 2), so 0.5 is
    # the machine's own resolution. Note the raw value is really flowmeter
    # pulses - 0.5 mL of nominal resolution isn't 0.5 mL of dosing accuracy.
    "dose_S1": dict(unit_of_measurement=UNIT_MILLILITER, min_value=0, max_value=250, step=0.5),
    "dose_S2": dict(unit_of_measurement=UNIT_MILLILITER, min_value=0, max_value=250, step=0.5),
    "dose_L1": dict(unit_of_measurement=UNIT_MILLILITER, min_value=0, max_value=250, step=0.5),
    "dose_L2": dict(unit_of_measurement=UNIT_MILLILITER, min_value=0, max_value=250, step=0.5),
    "pre_infusion_S1": dict(unit_of_measurement=UNIT_SECOND, min_value=0, max_value=5, step=0.1),
    "pre_infusion_S2": dict(unit_of_measurement=UNIT_SECOND, min_value=0, max_value=5, step=0.1),
    "pre_infusion_L1": dict(unit_of_measurement=UNIT_SECOND, min_value=0, max_value=5, step=0.1),
    "pre_infusion_L2": dict(unit_of_measurement=UNIT_SECOND, min_value=0, max_value=5, step=0.1),
    # Pump-OFF soak per selection. Verified on hardware: the machine accepts
    # 0.0-5.0 s (the same range as the pump-ON times) at 0.1 s granularity,
    # and the setting audibly changes the pause. Anything ABOVE 5.0 s is
    # refused, faults the machine and resets all four registers to 3.0 s, so
    # the max here is a real limit, not a guess. Default is 3.0 s.
    **{
        f"pre_infusion_soak_{k}": dict(unit_of_measurement=UNIT_SECOND, min_value=0, max_value=5, step=0.1)
        for k in ("S1", "S2", "L1", "L2")
    },
    # Boiler PID parameters (P/I/d/b per boiler). Nothing documents a valid
    # range or the scaling, so these bounds are a guard rail, not a spec:
    # 200 is 2x the largest factory value seen (steam d = 100), and the
    # minimum is 1 because a zero gain/band is a degenerate setting.
    **{
        f"pid_{boiler}_{term}": dict(min_value=1, max_value=200, step=1)
        for boiler in ("coffee", "steam")
        for term in ("p", "i", "d", "b")
    },
    "boiler_fill_timeout": dict(min_value=0, max_value=240, step=1),
    # Power configuration: how many heating elements may run at once (the
    # coffee group takes priority). The machine's manual documents 1-3 and a
    # standard setting of 2; it caps the machine's total current draw, so the
    # range is deliberately tight.
    "parameter_ce": dict(min_value=1, max_value=3, step=1),
}

READ_INTERVAL_MIN = 15
READ_INTERVAL_MAX = 600
READ_INTERVAL_STEP = 15

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_GICAR_ID): cv.use_id(GicarBridge),
        cv.Optional(CONF_READ_INTERVAL): number.number_schema(
            GicarReadIntervalNumber, unit_of_measurement=UNIT_SECOND
        ),
        **{
            cv.Optional(key): number.number_schema(
                GicarNumber,
                **{k: v for k, v in opts.items() if k in ("unit_of_measurement", "device_class")},
            )
            for key, opts in WRITABLE_NUMERIC_FIELDS.items()
        },
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_GICAR_ID])

    if CONF_READ_INTERVAL in config:
        n = await number.new_number(
            config[CONF_READ_INTERVAL],
            min_value=READ_INTERVAL_MIN,
            max_value=READ_INTERVAL_MAX,
            step=READ_INTERVAL_STEP,
        )
        cg.add(n.set_gicar_parent(parent))

    for key, opts in WRITABLE_NUMERIC_FIELDS.items():
        if key not in config:
            continue
        n = await number.new_number(
            config[key], min_value=opts["min_value"], max_value=opts["max_value"], step=opts["step"]
        )
        cg.add(n.set_key(key))
        cg.add(n.set_gicar_parent(parent))
