#pragma once

// Offset/value-mapping reference for the Gicar serial protocol's memory map.
// Mirrors python-poc/lib/ascaso_offsets.py's MEMORY_MAP 1:1 - keep both in
// sync when adding/changing fields. See docs/memory_map.md and
// docs/protocol.md for the human-readable protocol description.
//
// All offsets below are *absolute* offsets as documented in
// python-poc/lib/ascaso_offsets.py / docs/memory_map.md. The read request
// starts at GICAR_READ_OFFSET, so payload-relative offset = absolute -
// GICAR_READ_OFFSET.

#include <cstddef>
#include <cstdint>
#include <string>

namespace esphome {
namespace gicar {

// Read window: the lowest offset any implemented field uses is 33 (level
// probe) and the highest is 217 (last byte of the u32 water counter at 214),
// so one request covers everything. Offsets 0-32 are Model 5+ weekly-timer
// bytes plus a few constants; 218-219 read zero and 220+ is all-FF, so
// there is nothing above the window worth fetching.
static const uint16_t GICAR_READ_OFFSET = 33;
static const uint16_t GICAR_READ_END = 218;  // exclusive
// A single read request maxes out at 250 payload bytes per response (511
// total chars) - almost certainly a ~512-byte response buffer in the
// Bluetooth module's firmware rather than a real memory-size limit.
static const size_t GICAR_PAYLOAD_LEN = GICAR_READ_END - GICAR_READ_OFFSET;
static_assert(GICAR_PAYLOAD_LEN <= 250, "would need to re-introduce chunked reads above the 250-byte response cap");

// "Not set" sentinel for the autotimer hour/minute bytes (127-130): a timer
// is disabled when both hold 100, and disabling writes 100/100 back. Byte
// 126 is NOT the autotimer flag on a Baby T (it's "Group 3 enable" on the
// multi-group models).
static const uint8_t GICAR_AUTOTIMER_UNSET = 100;

// Model byte (offset 76) -> display name, index = raw value (1-8).
static const uint8_t GICAR_MODEL_COUNT = 8;
extern const char *const GICAR_MODEL_NAMES[GICAR_MODEL_COUNT];

// Absolute offsets of the per-button coffee counters (u32 slots, 4 bytes
// apart).
static const uint16_t GICAR_COUNTER_OFFSETS[5] = {134, 138, 142, 146, 150};
// The machine's own resettable total. Measured on hardware: it is its own
// accumulator, not a live sum of the per-button counters - zeroing 134..150
// leaves it untouched and it keeps incrementing from its old value on the
// next brew, so a reset has to clear it explicitly.
static const uint16_t GICAR_COUNTER_TOTAL_OFFSET = 206;
// Lifetime total - deliberately left alone by a reset.
static const uint16_t GICAR_COUNTER_LIFETIME_OFFSET = 210;

// Plain numeric fields: raw u8/u16le/u32le value divided by `multiplier`
// gives the displayed value. Used for both reading (sensors) and writing
// (numbers).
struct NumericFieldDef {
  const char *key;
  uint16_t offset;  // absolute offset - see GICAR_READ_OFFSET above
  uint8_t size;     // bytes: 1 (u8), 2 (u16le) or 4 (u32le)
  float multiplier;
};

extern const NumericFieldDef NUMERIC_FIELDS[];
extern const size_t NUMERIC_FIELDS_COUNT;

// Extract a numeric value from a GICAR_PAYLOAD_LEN-byte payload. Covers the
// NUMERIC_FIELDS table plus one derived key, "offset_temperature" (see
// extract_offset_temperature).
// Returns NAN if the key is unknown or its offset falls outside the payload.
float extract_numeric(const uint8_t *payload, const std::string &key);

// Encode a display value back into raw bytes for a NUMERIC_FIELDS key, for
// writing. Returns false if the key is unknown. `out` must have room for 4
// bytes; `len`/`offset` are set to the field's actual size/absolute offset.
bool encode_numeric(const std::string &key, float display_value, uint8_t *out, uint8_t *len, uint16_t *offset);

// "Offset temperature" as the machine displays it: for
// model<5 with byte 79 == 0, or any model>=5, it's u16 @89 / 10; otherwise
// (model<5 and byte 79 != 0) it's (u16 @77 - 99) / 10. Byte 79 is therefore
// a mode flag selecting which register is live - it is NOT "standby time"
// as older docs claimed (that's the u16 at 84). Celsius assumed throughout;
// Fahrenheit is a display-side conversion only (not implemented here).
float extract_offset_temperature(const uint8_t *payload);
// Inverse of the above for writing - picks the live register based on the
// current payload.
bool encode_offset_temperature(const uint8_t *payload, float display_value, uint8_t *out, uint8_t *len,
                               uint16_t *offset);

// Categorical/text fields (model, power_state, steam_state, ...). Each has
// bespoke byte->string logic (see docs/memory_map.md for the exact mapping),
// so unlike NUMERIC_FIELDS this isn't a single flat table.
std::string extract_text(const uint8_t *payload, const std::string &key);

// Raw byte at an absolute offset, or -1 if out of range. Used by switches/
// selects to compare against their own raw values directly, rather than
// assuming a field's extract_text() mapping happens to use "on"/"off".
int extract_raw_byte(const uint8_t *payload, uint16_t abs_offset);

}  // namespace gicar
}  // namespace esphome
