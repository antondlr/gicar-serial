#pragma once

#include "esphome/components/switch/switch.h"
#include "esphome/core/preferences.h"
#include "gicar.h"

namespace esphome {
namespace gicar {

// "Auto start" / "Auto shutdown" enable, the way the Baby T app models it:
// there is no flag byte - the timer is "off" when its hour+minute bytes hold
// the sentinel value 100, and disabling it writes 100/100 back. Turning it back on restores the last real time we saw
// (remembered in flash), defaulting to 07:00 / 11:00 if we never saw one.
class GicarAutotimerEnableSwitch : public switch_::Switch {
 public:
  struct Remembered {
    uint8_t hour;
    uint8_t minute;
  };
  void set_gicar_parent(GicarBridge *parent) {
    parent_ = parent;
    parent->register_autotimer_enable_switch(this);
  }
  void set_offsets(uint16_t hour_offset, uint16_t minute_offset, uint8_t default_hour) {
    hour_offset_ = hour_offset;
    minute_offset_ = minute_offset;
    default_hour_ = default_hour;
  }
  uint16_t get_hour_offset() const { return hour_offset_; }
  uint16_t get_minute_offset() const { return minute_offset_; }
  // Last real (non-sentinel) time seen for this timer, or the default - what
  // enabling the switch would write, and what the time entity shows while
  // the timer is disabled.
  void get_remembered(uint8_t *hour, uint8_t *minute) {
    Remembered r = recall_();
    *hour = r.hour;
    *minute = r.minute;
  }

  void update_from_raw(int hour, int minute) {
    bool enabled = hour != GICAR_AUTOTIMER_UNSET && minute != GICAR_AUTOTIMER_UNSET;
    if (enabled && hour >= 0 && hour < 24 && minute >= 0 && minute < 60)
      remember_((uint8_t) hour, (uint8_t) minute);
    this->publish_state(enabled);
  }

 protected:

  ESPPreferenceObject &pref_() {
    if (!pref_made_) {
      pref_obj_ = global_preferences->make_preference<Remembered>(this->get_object_id_hash());
      pref_made_ = true;
    }
    return pref_obj_;
  }
  void remember_(uint8_t hour, uint8_t minute) {
    Remembered cur{};
    if (pref_().load(&cur) && cur.hour == hour && cur.minute == minute)
      return;
    Remembered r{hour, minute};
    pref_().save(&r);
  }
  Remembered recall_() {
    Remembered r{default_hour_, 0};
    if (pref_().load(&r) && (r.hour >= 24 || r.minute >= 60))
      r = Remembered{default_hour_, 0};
    return r;
  }

  void write_state(bool state) override {
    uint8_t hour = GICAR_AUTOTIMER_UNSET, minute = GICAR_AUTOTIMER_UNSET;
    if (state) {
      Remembered r = recall_();
      hour = r.hour;
      minute = r.minute;
    }
    parent_->write_ops({{hour_offset_, 1, {hour}}, {minute_offset_, 1, {minute}}},
                       [this, state]() { this->publish_state(state); });
  }

  GicarBridge *parent_;
  uint16_t hour_offset_{0};
  uint16_t minute_offset_{0};
  uint8_t default_hour_{7};
  ESPPreferenceObject pref_obj_;
  bool pref_made_{false};
};

}  // namespace gicar
}  // namespace esphome
