#pragma once

#include "esphome/components/datetime/time_entity.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

// Combines two separate MEMORY_MAP byte offsets (hour + minute) into a
// single HH:MM datetime.time entity (offsets 127/128 for auto-on
// hour/minute, 129/130 for auto-off hour/minute).
// Seconds are always 0 - the protocol has no seconds field here. When the
// timer is disabled (bytes hold the 100 sentinel) the last real time is
// kept on display rather than publishing a bogus "100:100"; setting a time
// while disabled writes it and therefore enables the timer, see
// GicarAutotimerEnableSwitch.
class GicarAutotimerTime : public datetime::TimeEntity {
 public:
  void set_gicar_parent(GicarBridge *parent) {
    parent_ = parent;
    parent->register_autotimer_time(this);
  }
  void set_offsets(uint16_t hour_offset, uint16_t minute_offset) {
    hour_offset_ = hour_offset;
    minute_offset_ = minute_offset;
  }
  uint16_t get_hour_offset() const { return hour_offset_; }
  uint16_t get_minute_offset() const { return minute_offset_; }
  void publish_from_raw(uint8_t hour, uint8_t minute) {
    if (hour >= 24 || minute >= 60)
      return;  // sentinel / garbage - keep whatever was last shown
    if (this->has_state() && this->hour_ == hour && this->minute_ == minute)
      return;
    this->hour_ = hour;
    this->minute_ = minute;
    this->second_ = 0;
    this->publish_state();
  }

 protected:
  void control(const datetime::TimeCall &call) override {
    uint8_t new_hour = call.get_hour().value_or(this->hour_);
    uint8_t new_minute = call.get_minute().value_or(this->minute_);
    parent_->write_ops({{hour_offset_, 1, {new_hour}}, {minute_offset_, 1, {new_minute}}},
                       [this, new_hour, new_minute]() { this->publish_from_raw(new_hour, new_minute); });
  }

  GicarBridge *parent_;
  uint16_t hour_offset_{0};
  uint16_t minute_offset_{0};
};

}  // namespace gicar
}  // namespace esphome
