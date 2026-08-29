import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import time as time_
from esphome.const import CONF_ID, CONF_TIME_ID

CODEOWNERS = ["@antondlr"]

gicar_ns = cg.esphome_ns.namespace("gicar")
GicarBridge = gicar_ns.class_("GicarBridge", cg.PollingComponent)

CONF_DEVICE_NAME = "device_name"
CONF_MAC_ADDRESS = "mac_address"
CONF_PIN = "pin"
CONF_GICAR_ID = "gicar_id"

# update_interval defaults to never (0) - reads only happen on connect and on
# explicit button/HA-triggered requests unless the user opts into periodic
# polling, e.g. `update_interval: 60s`.
CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(GicarBridge),
        # Matched as a substring of the advertised classic-BT name, so a prefix
        # like "ASCASO" finds any unit; the first match wins.
        cv.Optional(CONF_DEVICE_NAME, default="ASCASO"): cv.string,
        cv.Optional(CONF_MAC_ADDRESS): cv.mac_address,
        # Classic-BT pairing PIN. Optional: without one here (or one entered
        # later via the `text:` pin entity and stored in flash) the bridge
        # won't attempt to pair - there is no known universal default.
        cv.Optional(CONF_PIN): cv.string,
        # Optional - only needed if you use the sync_clock button.
        cv.Optional(CONF_TIME_ID): cv.use_id(time_.RealTimeClock),
    }
).extend(cv.polling_component_schema("never"))


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    cg.add(var.set_device_name(config[CONF_DEVICE_NAME]))
    if CONF_PIN in config:
        cg.add(var.set_pin(config[CONF_PIN]))
    if CONF_MAC_ADDRESS in config:
        cg.add(var.set_mac_address(*config[CONF_MAC_ADDRESS].parts))
    if CONF_TIME_ID in config:
        time_source = await cg.get_variable(config[CONF_TIME_ID])
        cg.add(var.set_time_source(time_source))
    cg.add_library("BluetoothSerial", None)
