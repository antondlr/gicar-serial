#pragma once

#include "esphome/components/button/button.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

class GicarReadButton : public button::Button {
 public:
  void set_gicar_parent(GicarBridge *parent) { parent_ = parent; }

 protected:
  void press_action() override { parent_->start_read(); }

  GicarBridge *parent_;
};

class GicarResetCountersButton : public button::Button {
 public:
  void set_gicar_parent(GicarBridge *parent) { parent_ = parent; }

 protected:
  void press_action() override { parent_->reset_counters(); }

  GicarBridge *parent_;
};

class GicarReconnectButton : public button::Button {
 public:
  void set_gicar_parent(GicarBridge *parent) { parent_ = parent; }

 protected:
  void press_action() override { parent_->reconnect_bluetooth(); }

  GicarBridge *parent_;
};

}  // namespace gicar
}  // namespace esphome
