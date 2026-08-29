#pragma once

#include "esphome/components/select/select.h"
#include "esphome/core/log.h"
#include "gicar.h"
#include <vector>

namespace esphome {
namespace gicar {

// Dropdown backed by a single raw byte: option index i <-> raw_values_[i].
// Used for the list-type settings (model, measurement unit, water supply,
// level probe sensitivity). State is
// re-synced from the machine on every read (GicarBridge::publish_all_).
class GicarSelect : public select::Select {
 public:
  void set_gicar_parent(GicarBridge *parent) {
    parent_ = parent;
    parent->register_select(this);
  }
  void set_write_params(uint16_t offset, std::vector<uint8_t> raw_values) {
    offset_ = offset;
    raw_values_ = std::move(raw_values);
  }
  uint16_t get_offset() const { return offset_; }

  void publish_from_raw(int raw) {
    for (size_t i = 0; i < raw_values_.size(); i++) {
      if (raw_values_[i] == raw) {
        if (!this->has_state() || this->active_index() != i)
          this->publish_state(i);
        return;
      }
    }
    ESP_LOGW("gicar", "%s: raw value %d has no matching option", this->get_name().c_str(), raw);
  }

 protected:
  void control(const std::string &value) override {
    auto index = this->index_of(value);
    if (!index.has_value() || *index >= raw_values_.size())
      return;
    uint8_t raw = raw_values_[*index];
    parent_->write_byte_field(offset_, raw, [this, value]() { this->publish_state(value); });
  }

  GicarBridge *parent_;
  uint16_t offset_{0};
  std::vector<uint8_t> raw_values_;
};

}  // namespace gicar
}  // namespace esphome
