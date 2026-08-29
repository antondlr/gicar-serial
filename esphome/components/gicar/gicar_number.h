#pragma once

#include "esphome/components/number/number.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

// Read/write number backed by a MEMORY_MAP key - same key space get_numeric()
// reads from, so writing just reuses that table's offset/size/multiplier.
class GicarNumber : public number::Number {
 public:
  void set_gicar_parent(GicarBridge *parent) {
    parent_ = parent;
    parent->register_number(this);
  }
  void set_key(const std::string &key) { key_ = key; }
  const std::string &get_key() const { return key_; }

 protected:
  void control(float value) override {
    parent_->write_numeric_field(key_, value, [this, value]() { this->publish_state(value); });
  }

  GicarBridge *parent_;
  std::string key_;
};

}  // namespace gicar
}  // namespace esphome
