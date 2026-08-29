#pragma once

#include "esphome/components/text_sensor/text_sensor.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

class GicarTextSensor : public text_sensor::TextSensor {
 public:
  void set_gicar_parent(GicarBridge *parent) { parent->register_text_sensor(this); }
  void set_key(const std::string &key) { key_ = key; }
  const std::string &get_key() const { return key_; }

 protected:
  std::string key_;
};

}  // namespace gicar
}  // namespace esphome
