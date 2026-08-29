import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components import text

from . import CONF_GICAR_ID, GicarBridge, gicar_ns

GicarPinText = gicar_ns.class_("GicarPinText", text.Text)

CONF_PIN = "pin"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_GICAR_ID): cv.use_id(GicarBridge),
        # Bluetooth pairing PIN - persisted to flash, overrides the `pin:` in
        # the gicar: block once set.
        cv.Optional(CONF_PIN): text.text_schema(GicarPinText, mode="PASSWORD"),
    }
)


async def to_code(config):
    parent = await cg.get_variable(config[CONF_GICAR_ID])
    if CONF_PIN in config:
        var = await text.new_text(config[CONF_PIN], min_length=4, max_length=16, pattern="[0-9]+")
        cg.add(var.set_gicar_parent(parent))
