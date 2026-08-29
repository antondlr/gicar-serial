#pragma once

#include "esphome/components/text/text.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

// Classic-BT pairing PIN, editable from HA / the web UI. Stored in flash by
// the bridge and marked verified once a connection succeeds with it.
class GicarPinText : public text::Text {
 public:
  void set_gicar_parent(GicarBridge *parent) {
    parent_ = parent;
    parent->register_pin_text(this);
  }

 protected:
  void control(const std::string &value) override { parent_->set_pin_runtime(value); }

  GicarBridge *parent_;
};

}  // namespace gicar
}  // namespace esphome
