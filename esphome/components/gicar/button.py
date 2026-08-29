import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import button

from . import CONF_GICAR_ID, GicarBridge, gicar_ns

GicarReadButton = gicar_ns.class_("GicarReadButton", button.Button)
GicarSyncClockButton = gicar_ns.class_("GicarSyncClockButton", button.Button)
GicarResetCountersButton = gicar_ns.class_("GicarResetCountersButton", button.Button)
GicarReconnectButton = gicar_ns.class_("GicarReconnectButton", button.Button)

CONF_READ = "read"
CONF_SYNC_CLOCK = "sync_clock"
CONF_RESET_COUNTERS = "reset_counters"
CONF_RECONNECT = "reconnect"

BUTTONS = {
    CONF_READ: GicarReadButton,
    CONF_SYNC_CLOCK: GicarSyncClockButton,
    CONF_RESET_COUNTERS: GicarResetCountersButton,
    CONF_RECONNECT: GicarReconnectButton,
}

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_GICAR_ID): cv.use_id(GicarBridge),
        **{cv.Optional(key): button.button_schema(cls) for key, cls in BUTTONS.items()},
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_GICAR_ID])
    for key in BUTTONS:
        if key not in config:
            continue
        var = await button.new_button(config[key])
        cg.add(var.set_gicar_parent(parent))
