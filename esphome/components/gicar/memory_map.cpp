#include "memory_map.h"
#include <cmath>
#include <cstring>

namespace esphome {
namespace gicar {

const char *const GICAR_MODEL_NAMES[GICAR_MODEL_COUNT] = {
    "Baby T One 230V",  "Baby T Plus 230V",  "Baby T One 120V",    "Baby T Plus 120V",
    "Barista T 2 Groups", "Barista T 3 Groups", "Big Dream 2 Groups", "Big Dream 3 Groups",
};

// Offsets/types verified on a Baby T Plus against the values the machine's
// own menus and the vendor app display - see docs/memory_map.md for the
// per-field notes.
const NumericFieldDef NUMERIC_FIELDS[] = {
    {"coffee_temperature", 53, 2, 10},
    {"steam_temperature", 63, 2, 10},
    // PID control parameters, one block of four u16s immediately after each
    // boiler's setpoint - the machine's programming menu exposes exactly
    // these four (P/I/d/b) under its temperature-control sub-menu. The
    // scaling of each is not documented anywhere; the values below read
    // 30/15/40/10 (coffee) and 80/15/100/5 (steam) on a Baby T Plus.
    // Writing these changes boiler regulation - unverified, hidden by default.
    {"pid_coffee_p", 55, 2, 1},
    {"pid_coffee_i", 57, 2, 1},
    {"pid_coffee_d", 59, 2, 1},
    {"pid_coffee_b", 61, 2, 1},
    {"pid_steam_p", 65, 2, 1},
    {"pid_steam_i", 67, 2, 1},
    {"pid_steam_d", 69, 2, 1},
    {"pid_steam_b", 71, 2, 1},
    {"standby_temperature", 82, 2, 10},
    // u16, raw minutes. A prior version had it as u8 and dropped the high byte.
    {"standby_time", 84, 2, 1},
    {"dose_S1", 91, 2, 2},
    {"dose_S2", 93, 2, 2},
    {"dose_L1", 95, 2, 2},
    {"dose_L2", 97, 2, 2},
    // Pump-OFF (soak) time per selection, same tenths-of-a-second encoding
    // as the pump-ON times below and sitting directly in front of them.
    // Default is 3.0 s on all four. Writable: the machine accepts 0.0-5.0 s
    // and the setting audibly changes the pause. Above 5.0 s it faults and
    // resets all four to 3.0 s - see docs/memory_map.md.
    {"pre_infusion_soak_S1", 41, 1, 10},
    {"pre_infusion_soak_S2", 42, 1, 10},
    {"pre_infusion_soak_L1", 43, 1, 10},
    {"pre_infusion_soak_L2", 44, 1, 10},
    // 45 and 50 are the fifth slots of the soak / pump-ON arrays, which would
    // make them the XL (continuous) selection's. Both read 0, which is also
    // what "XL has no pre-infusion" would produce, so this is unconfirmed -
    // and read-only, for the same reason as the soak registers above.
    {"pre_infusion_soak_XL", 45, 1, 10},
    {"pre_infusion_S1", 46, 1, 10},
    {"pre_infusion_S2", 47, 1, 10},
    {"pre_infusion_L1", 48, 1, 10},
    {"pre_infusion_L2", 49, 1, 10},
    {"pre_infusion_XL", 50, 1, 10},
    // Counters live in 4-byte slots (the reset writes u32 zeros). The 5th
    // slot (150) is the flush / continuous ("XL") button counter.
    {"counter_S1", 134, 4, 1},
    {"counter_S2", 138, 4, 1},
    {"counter_L1", 142, 4, 1},
    {"counter_L2", 146, 4, 1},
    {"counter_flush", 150, 4, 1},
    // Tea counters: 4-byte slots like the button counters above (the upper
    // two bytes read zero in every dump). Zero on a Baby T Plus.
    {"counter_tea_1", 194, 4, 1},
    {"counter_tea_2", 198, 4, 1},
    // The machine's own resettable total - read straight from 206 rather
    // than summing 134..150 ourselves, so it always shows what the machine
    // itself has stored.
    {"counter_total", 206, 4, 1},
    {"counter_lifetime", 210, 4, 1},
    // Has mirrored counter_lifetime exactly in every dump taken so far.
    {"counter_water", 214, 4, 1},
    // Both are Barista/Big Dream (model>=5) settings that the vendor app
    // never shows for a Baby T. They read back plausibly on a Baby T
    // (120 / 1) so they're exposed, but flagged as unverified there.
    // Parameter CE: integer 0-6, meaning unknown.
    {"boiler_fill_timeout", 73, 1, 1},
    {"parameter_ce", 81, 1, 1},
};
const size_t NUMERIC_FIELDS_COUNT = sizeof(NUMERIC_FIELDS) / sizeof(NUMERIC_FIELDS[0]);

static bool in_payload(int rel_offset, size_t size) {
  return rel_offset >= 0 && (size_t) rel_offset + size <= GICAR_PAYLOAD_LEN;
}

static uint32_t read_le(const uint8_t *payload, uint16_t abs_offset, uint8_t size) {
  int rel = abs_offset - GICAR_READ_OFFSET;
  uint32_t raw = 0;
  for (uint8_t i = 0; i < size; i++)
    raw |= ((uint32_t) payload[rel + i]) << (8 * i);
  return raw;
}

float extract_numeric(const uint8_t *payload, const std::string &key) {
  if (key == "offset_temperature")
    return extract_offset_temperature(payload);
  for (size_t i = 0; i < NUMERIC_FIELDS_COUNT; i++) {
    const auto &field = NUMERIC_FIELDS[i];
    if (key != field.key)
      continue;
    if (!in_payload(field.offset - GICAR_READ_OFFSET, field.size))
      return NAN;
    return read_le(payload, field.offset, field.size) / field.multiplier;
  }
  return NAN;
}

static void encode_le(uint32_t raw, uint8_t size, uint8_t *out) {
  for (uint8_t i = 0; i < size; i++)
    out[i] = (raw >> (8 * i)) & 0xFF;
}

bool encode_numeric(const std::string &key, float display_value, uint8_t *out, uint8_t *len, uint16_t *offset) {
  for (size_t i = 0; i < NUMERIC_FIELDS_COUNT; i++) {
    const auto &field = NUMERIC_FIELDS[i];
    if (key != field.key)
      continue;
    int64_t raw = (int64_t) lroundf(display_value * field.multiplier);
    int64_t max = field.size == 1 ? 0xFF : field.size == 2 ? 0xFFFF : 0xFFFFFFFF;
    if (raw < 0)
      raw = 0;
    if (raw > max)
      raw = max;
    encode_le((uint32_t) raw, field.size, out);
    *len = field.size;
    *offset = field.offset;
    return true;
  }
  return false;
}

// Which register holds the offset temperature: byte 79 == 0 (or model >= 5)
// -> u16 @89 / 10, otherwise (u16 @77 - 99) / 10.
static bool offset_temperature_uses_89(const uint8_t *payload) {
  int mode = extract_raw_byte(payload, 79);
  int model = extract_raw_byte(payload, 76);
  return mode == 0 || model >= 5;
}

float extract_offset_temperature(const uint8_t *payload) {
  if (!in_payload(77 - GICAR_READ_OFFSET, 2) || !in_payload(89 - GICAR_READ_OFFSET, 2))
    return NAN;
  if (offset_temperature_uses_89(payload))
    return (int16_t) read_le(payload, 89, 2) / 10.0f;
  return ((int32_t) read_le(payload, 77, 2) - 99) / 10.0f;
}

bool encode_offset_temperature(const uint8_t *payload, float display_value, uint8_t *out, uint8_t *len,
                               uint16_t *offset) {
  *len = 2;
  if (offset_temperature_uses_89(payload)) {
    // raw = value * 10
    *offset = 89;
    encode_le((uint16_t) (int16_t) lroundf(display_value * 10), 2, out);
  } else {
    // raw = value * 10 + 99
    *offset = 77;
    encode_le((uint16_t) (int16_t) lroundf(display_value * 10 + 99), 2, out);
  }
  return true;
}

int extract_raw_byte(const uint8_t *payload, uint16_t abs_offset) {
  int rel = abs_offset - GICAR_READ_OFFSET;
  if (rel < 0 || (size_t) rel >= GICAR_PAYLOAD_LEN)
    return -1;
  return payload[rel];
}

std::string extract_text(const uint8_t *payload, const std::string &key) {
  auto byte_at = [payload](uint16_t abs_offset) -> int { return extract_raw_byte(payload, abs_offset); };

  if (key == "model") {
    int v = byte_at(76);
    if (v >= 1 && v <= GICAR_MODEL_COUNT)
      return GICAR_MODEL_NAMES[v - 1];
    return "unknown";
  }
  // Documented as the serial number. It does not match the machine number on
  // the rating plate, so it is presumably an internal serial. Kept as text so
  // it renders as a plain integer and never lands in long-term statistics.
  if (key == "serial_number") {
    int lo = byte_at(34), hi = byte_at(35);
    if (lo < 0 || hi < 0)
      return "";
    return std::to_string(lo | (hi << 8));
  }
  if (key == "power_state")
    return byte_at(132) == 6 ? "on" : "off";
  if (key == "steam_state")
    return byte_at(86) == 1 ? "on" : "off";
  if (key == "coffee_group_state")
    return byte_at(124) > 0 ? "on" : "off";
  if (key == "temperature_unit")
    return byte_at(52) == 1 ? "fahrenheit" : "celsius";
  // Offset 80 comes from the original project notes; the vendor app never
  // exposes it. Reads consistently with the machine's menu, write unverified.
  if (key == "shot_timer_enabled")
    return byte_at(80) == 1 ? "enabled" : "disabled";
  // 38/40 verified on hardware (earlier notes had these at 43/45). On
  // model>=5 machines the flush flag is stored as value+1.
  if (key == "flush_enabled")
    return byte_at(38) == 1 ? "enabled" : "disabled";
  if (key == "pre_infusion_enabled")
    return byte_at(40) == 1 ? "enabled" : "disabled";
  // 0 = direct (plumbed) connection, 1 = tank.
  if (key == "water_connection")
    return byte_at(87) == 1 ? "tank" : "direct";
  // Barista/Big Dream setting (see NUMERIC_FIELDS note on 73/81).
  if (key == "exposition_mode")
    return byte_at(133) == 1 ? "enabled" : "disabled";
  return "";
}

}  // namespace gicar
}  // namespace esphome
