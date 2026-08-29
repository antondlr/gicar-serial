#pragma once

#include "esphome/components/sensor/sensor.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

class GicarSensor : public sensor::Sensor {
 public:
  void set_gicar_parent(GicarBridge *parent) { parent->register_sensor(this); }
  void set_key(const std::string &key) { key_ = key; }
  const std::string &get_key() const { return key_; }

 protected:
  std::string key_;
};

}  // namespace gicar
}  // namespace esphome
