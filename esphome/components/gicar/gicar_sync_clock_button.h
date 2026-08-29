#pragma once

#include "esphome/components/button/button.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

class GicarSyncClockButton : public button::Button {
 public:
  void set_gicar_parent(GicarBridge *parent) { parent_ = parent; }

 protected:
  void press_action() override { parent_->sync_clock(); }

  GicarBridge *parent_;
};

}  // namespace gicar
}  // namespace esphome
