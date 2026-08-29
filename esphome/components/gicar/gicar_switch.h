#pragma once

#include "esphome/components/switch/switch.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

// Generic on/off write (offset + distinct on/off raw byte values), state kept
// in sync with the machine's actual state on every successful read by
// comparing the raw byte at `offset_` against `on_value_` directly (see
// GicarBridge::publish_all_) - not every field's extract_text() mapping uses
// "on"/"off" (e.g. flush_enabled is "enabled"/"disabled", water_connection is
// "tank"/"direct"), so comparing raw bytes avoids assuming otherwise.
class GicarSwitch : public switch_::Switch {
 public:
  void set_gicar_parent(GicarBridge *parent) {
    parent_ = parent;
    parent->register_switch(this);
  }
  void set_write_params(uint16_t offset, uint8_t on_value, uint8_t off_value) {
    offset_ = offset;
    on_value_ = on_value;
    off_value_ = off_value;
  }
  uint16_t get_offset() const { return offset_; }
  uint8_t get_on_value() const { return on_value_; }

 protected:
  void write_state(bool state) override {
    uint8_t value = state ? on_value_ : off_value_;
    parent_->write_byte_field(offset_, value, [this, state]() { this->publish_state(state); });
  }

  GicarBridge *parent_;
  uint16_t offset_{0};
  uint8_t on_value_{1};
  uint8_t off_value_{0};
};

}  // namespace gicar
}  // namespace esphome
