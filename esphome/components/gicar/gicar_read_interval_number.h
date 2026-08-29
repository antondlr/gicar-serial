#pragma once

#include "esphome/components/number/number.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

// Not a machine field - adjusts GicarBridge's own PollingComponent
// update_interval live, in seconds. The value is persisted to flash by the
// bridge so it survives reboots.
class GicarReadIntervalNumber : public number::Number {
 public:
  void set_gicar_parent(GicarBridge *parent) {
    parent_ = parent;
    parent->register_read_interval_number(this);
  }

 protected:
  void control(float value) override { parent_->set_read_interval_seconds(value); }

  GicarBridge *parent_;
};

}  // namespace gicar
}  // namespace esphome
