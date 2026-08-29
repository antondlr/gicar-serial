#include "gicar.h"
#include "gicar_sensor.h"
#include "gicar_text_sensor.h"
#include "gicar_switch.h"
#include "gicar_select.h"
#include "gicar_autotimer_switch.h"
#include "gicar_number.h"
#include "gicar_read_interval_number.h"
#include "gicar_autotimer_time.h"
#include "gicar_pin_text.h"
#include "esphome/core/application.h"
#include "esphome/core/log.h"
#include "esphome/core/helpers.h"
#include "esphome/components/time/real_time_clock.h"
#include <cstring>
#include <cstdlib>
#include <cmath>
#include <esp_gap_bt_api.h>

namespace esphome {
namespace gicar {

static const char *const TAG = "gicar";
static const uint32_t READ_SETTLE_MS = 1500;   // matches the settle delay proven to work
// The machine acknowledges a write before it has finished acting on it - the
// power state in particular takes a moment to transition - so a re-read sent
// straight after the OK can still return the old value and make an entity
// snap back. Give it time to land before confirming.
static const uint32_t WRITE_SETTLE_MS = 2000;
static const uint32_t REQUEST_TIMEOUT_MS = 8000;
// A raw command's reply has no predictable length, so it is considered
// complete once this long passes with no further bytes arriving.
static const uint32_t RAW_QUIET_MS = 400;
static const uint32_t SCAN_DURATION_MS = 15000;
static const uint32_t SCAN_IDLE_MS = 30000;  // gap between scan cycles while the device isn't found
static const uint8_t MAX_CONNECT_ATTEMPTS = 5;
// How long to go without a connection before assuming the BT stack has
// wedged and rebooting to clear it. Comfortably longer than a machine
// power-cycle plus a scan/connect cycle.
static const uint32_t BT_RECOVERY_TIMEOUT_MS = 10 * 60 * 1000;
// Give up rebooting after this many attempts with no successful connect in
// between - otherwise the ESP would reboot all night while the machine is
// simply switched off. Reset to zero on every successful connect.
static const uint8_t MAX_RECOVERY_REBOOTS = 3;

void GicarBridge::start_scan_() {
  // Empirically, address-based connect() reliably fails with a page timeout
  // unless a discovery scan ran first. We also use the scan to find the
  // device's *current* address live, rather than trusting a hardcoded one
  // that may go stale (this module's address doesn't seem to change, but
  // scanning fresh each boot is cheap insurance and doubles as the required
  // pre-connect scan anyway).
  serial_bt_.discoverAsync([this](BTAdvertisedDevice *device) {
    std::string name = device->haveName() ? device->getName() : "(no name)";
    ESP_LOGV(TAG, "  scan saw: %s @ %s", name.c_str(), device->getAddress().toString().c_str());
    if (!found_via_scan_ && device->haveName() && name.find(device_name_) != std::string::npos) {
      memcpy(scanned_mac_, *device->getAddress().getNative(), 6);
      found_via_scan_ = true;
      bt_device_ = name + " (" + device->getAddress().toString().c_str() + ")";
      // The machine's own number is not in the memory map anywhere - the only
      // place it appears is the trailing digits of the advertised name, and
      // it matches the number on the machine's rating plate.
      bt_machine_number_.clear();
      for (char c : name)
        if (c >= '0' && c <= '9')
          bt_machine_number_ += c;
      ESP_LOGI(TAG, "Found '%s' via scan @ %s", name.c_str(), device->getAddress().toString().c_str());
      // Force a fresh pairing here too - drop any stale/mismatched cached
      // link key from earlier sessions rather than trying to reuse it.
      esp_err_t err = esp_bt_gap_remove_bond_device(scanned_mac_);
      ESP_LOGI(TAG, "Cleared cached bond for scanned address (err=%d)", err);
      serial_bt_.discoverAsyncStop();
    }
  });
  last_scan_restart_ = millis();
}

struct PinPref {
  char pin[17];
  bool verified;
};

void GicarBridge::start_bluetooth_() {
  if (pin_.empty())
    ESP_LOGW(TAG, "No Bluetooth PIN configured - set one via the Bluetooth PIN entity before pairing can start");
  else
    serial_bt_.setPin(pin_.c_str(), pin_.length());
  serial_bt_.begin("esphome-gicar", true);  // true = master (client) mode
}

// The module's classic-BT stack can end up in a state where scans simply
// never see the machine again (typically after it has been power-cycled a
// few times), and no amount of waiting recovers it. Dropping bluedroid and
// bringing it back up clears that without losing WiFi/HA - try this first;
// the Restart Bridge button is the bigger hammer if it doesn't help.
void GicarBridge::reconnect_bluetooth() {
  ESP_LOGI(TAG, "Reconnect requested - reinitialising the Bluetooth stack");
  if (scanning_active_)
    serial_bt_.discoverAsyncStop();
  serial_bt_.disconnect();
  serial_bt_.end();
  start_bluetooth_();

  connected_ = false;
  state_ = State::IDLE;
  rx_buffer_.clear();
  read_requested_ = true;
  scanning_active_ = false;
  found_via_scan_ = false;
  connect_attempts_ = 0;
  last_connect_attempt_ = 0;
  conn_phase_ = ConnPhase::SCANNING;
  last_ok_at_ = millis();
  set_status_("reconnecting");
}

void GicarBridge::setup() {
  // A PIN entered at runtime (see set_pin_runtime) wins over the YAML default.
  pin_pref_ = global_preferences->make_preference<PinPref>(fnv1_hash("gicar_bt_pin"));
  PinPref saved_pin{};
  if (pin_pref_.load(&saved_pin) && saved_pin.pin[0] != 0) {
    saved_pin.pin[16] = 0;
    pin_ = saved_pin.pin;
    pin_verified_ = saved_pin.verified;
    ESP_LOGI(TAG, "Using stored Bluetooth PIN (%s)", pin_verified_ ? "verified" : "not yet verified");
  }
  if (pin_text_ != nullptr)
    pin_text_->publish_state(pin_);
  start_bluetooth_();

  if (has_mac_address_) {
    // Force a fresh pairing: drop any stale/mismatched cached link key from
    // earlier sessions rather than trying (and failing) to reuse it.
    esp_err_t err = esp_bt_gap_remove_bond_device(mac_address_);
    ESP_LOGI(TAG, "Cleared cached bond for configured address (err=%d)", err);
  }

  last_ok_at_ = millis();
  recovery_pref_ = global_preferences->make_preference<uint8_t>(fnv1_hash("gicar_recovery_reboots"));
  if (!recovery_pref_.load(&recovery_reboots_))
    recovery_reboots_ = 0;
  if (recovery_reboots_ != 0)
    ESP_LOGW(TAG, "%u Bluetooth recovery reboot(s) so far with no successful connect", recovery_reboots_);

  // Restore the last live-set read interval (see set_read_interval_seconds)
  // - the YAML update_interval only acts as the default before one is set.
  read_interval_pref_ = global_preferences->make_preference<float>(fnv1_hash("gicar_read_interval"));
  float saved = 0;
  if (read_interval_pref_.load(&saved) && saved >= 1.0f) {
    ESP_LOGI(TAG, "Restored read interval %.0fs from flash", saved);
    set_read_interval_seconds(saved, false);
  } else if (read_interval_number_ != nullptr) {
    read_interval_number_->publish_state(this->get_update_interval() / 1000.0f);
  }
}

static void save_pin_pref(ESPPreferenceObject &pref, const std::string &pin, bool verified) {
  PinPref p{};
  strncpy(p.pin, pin.c_str(), sizeof(p.pin) - 1);
  p.verified = verified;
  pref.save(&p);
}

void GicarBridge::set_pin_runtime(const std::string &pin) {
  if (pin == pin_) {
    if (pin_text_ != nullptr)
      pin_text_->publish_state(pin_);
    return;
  }
  if (pin.empty()) {
    ESP_LOGW(TAG, "Ignoring empty Bluetooth PIN");
    return;
  }
  ESP_LOGI(TAG, "Bluetooth PIN changed (%u digits)", (unsigned) pin.size());
  pin_ = pin;
  pin_verified_ = false;
  save_pin_pref(pin_pref_, pin_, false);
  serial_bt_.setPin(pin_.c_str(), pin_.length());
  if (pin_text_ != nullptr)
    pin_text_->publish_state(pin_);
  if (!connected_) {
    // Drop whatever bond the old PIN produced and start over right away.
    if (found_via_scan_)
      esp_bt_gap_remove_bond_device(scanned_mac_);
    serial_bt_.discoverAsyncStop();
    scanning_active_ = false;
    conn_phase_ = ConnPhase::SCANNING;
  }
  publish_status_();
}

void GicarBridge::set_status_(const char *status) {
  if (bt_status_ == status)
    return;
  bt_status_ = status;
  publish_status_();
}

void GicarBridge::publish_status_() {
  std::string status = bt_status_;
  if (connected_)
    status += pin_verified_ ? " (PIN verified)" : "";
  for (auto *ts : text_sensors_) {
    if (ts->get_key() == "bluetooth_status")
      ts->publish_state(status);
    else if (ts->get_key() == "machine_number")
      ts->publish_state(bt_machine_number_);
    else if (ts->get_key() == "bluetooth_device")
      ts->publish_state(bt_device_.empty() ? "not found yet" : bt_device_);
  }
}

void GicarBridge::set_read_interval_seconds(float seconds, bool persist) {
  // set_update_interval() alone only updates the stored interval - the
  // scheduler's already-running periodic timer keeps firing at the old
  // interval until the poller is explicitly restarted.
  this->set_update_interval((uint32_t) (seconds * 1000));
  this->stop_poller();
  this->start_poller();
  if (persist)
    read_interval_pref_.save(&seconds);
  if (read_interval_number_ != nullptr)
    read_interval_number_->publish_state(seconds);
}

void GicarBridge::try_connect_() {
  uint32_t now = millis();
  if (now - last_connect_attempt_ < 5000)
    return;
  last_connect_attempt_ = now;
  connect_attempts_++;

  ESP_LOGI(TAG, "Attempting SPP connection to %02X:%02X:%02X:%02X:%02X:%02X (attempt %d/%d)...", scanned_mac_[0],
           scanned_mac_[1], scanned_mac_[2], scanned_mac_[3], scanned_mac_[4], scanned_mac_[5], connect_attempts_,
           MAX_CONNECT_ATTEMPTS);
  if (serial_bt_.connect(scanned_mac_)) {
    connected_ = true;
    connected_at_ = millis();
    note_connected_();
    state_ = State::IDLE;
    rx_buffer_.clear();
    ESP_LOGI(TAG, "Connected");
    if (!pin_verified_) {
      pin_verified_ = true;
      save_pin_pref(pin_pref_, pin_, true);
    }
    set_status_("connected");
  } else {
    set_status_("connect failed, retrying");
    ESP_LOGW(TAG, "Connect failed (%d/%d)", connect_attempts_, MAX_CONNECT_ATTEMPTS);
  }
}

static std::string build_checksummed(const std::string &base) {
  uint32_t sum = 0;
  for (char c : base)
    sum += (uint8_t) c;
  char checksum[3];
  snprintf(checksum, sizeof(checksum), "%02X", (uint8_t) (sum % 256));
  return base + checksum;
}

// Drain any bytes still sitting in the underlying socket buffer from a prior
// timed-out/aborted request before starting a new one - otherwise stale
// bytes can prepend themselves onto the next response and corrupt it.
static void flush_stale_input(BluetoothSerial &serial_bt) {
  int flushed = 0;
  while (serial_bt.available()) {
    serial_bt.read();
    flushed++;
  }
  if (flushed > 0)
    ESP_LOGW("gicar", "Flushed %d stale byte(s) before new request", flushed);
}

void GicarBridge::send_read_request_() {
  // Everything we care about fits under the 250-byte single-request response
  // cap (see memory_map.h) - one request covers the whole field set.
  current_chunk_len_ = GICAR_PAYLOAD_LEN;

  char base[16];
  snprintf(base, sizeof(base), "r%04X%04X", GICAR_READ_OFFSET, current_chunk_len_);
  std::string request = build_checksummed(base);
  ESP_LOGD(TAG, "Sending read request (offset %u, %u bytes): %s", GICAR_READ_OFFSET, current_chunk_len_,
           request.c_str());
  flush_stale_input(serial_bt_);
  serial_bt_.write(reinterpret_cast<const uint8_t *>(request.data()), request.size());
  state_ = State::READING;
  rx_buffer_.clear();
  request_started_at_ = millis();
}

// The raw command hatch is an API action with no entity behind it, so the
// log is the only channel back - everything it has to say goes through here
// with a "Raw:" prefix (see python-poc/raw_cmd.py, which greps for it).
void GicarBridge::publish_raw_(const std::string &text) {
  raw_response_ = text;
  ESP_LOGI(TAG, "Raw: %s", text.c_str());
}

void GicarBridge::send_raw_command(const std::string &command) {
  std::string cmd;
  for (char c : command)
    if (!isspace((unsigned char) c))
      cmd += toupper((unsigned char) c);
  if (cmd.empty())
    return;
  if (cmd[0] != 'R' && cmd[0] != 'W') {
    publish_raw_("error: must start with r or w");
    return;
  }
  cmd[0] = (char) tolower((unsigned char) cmd[0]);
  for (size_t i = 1; i < cmd.size(); i++) {
    if (!isxdigit((unsigned char) cmd[i])) {
      publish_raw_("error: non-hex character after the command letter");
      return;
    }
  }
  if (cmd.size() < 9) {
    publish_raw_("error: too short, expected <r|w> + 4-digit offset + 4-digit length");
    return;
  }
  if (!connected_) {
    publish_raw_("error: not connected");
    return;
  }
  if (state_ != State::IDLE) {
    publish_raw_("error: busy, a request is already in flight");
    return;
  }

  std::string request = build_checksummed(cmd);
  publish_raw_("sending " + request);
  flush_stale_input(serial_bt_);
  serial_bt_.write(reinterpret_cast<const uint8_t *>(request.data()), request.size());
  state_ = State::RAW;
  rx_buffer_.clear();
  request_started_at_ = millis();
  last_rx_at_ = millis();
}

void GicarBridge::send_write_request_(uint16_t offset, const uint8_t *data, uint8_t len) {
  char header[16];
  snprintf(header, sizeof(header), "w%04X%04X", offset, len);
  std::string base(header);
  for (uint8_t i = 0; i < len; i++) {
    char byte_hex[3];
    snprintf(byte_hex, sizeof(byte_hex), "%02X", data[i]);
    base += byte_hex;
  }
  std::string request = build_checksummed(base);
  ESP_LOGI(TAG, "Sending write request: %s", request.c_str());
  flush_stale_input(serial_bt_);
  serial_bt_.write(reinterpret_cast<const uint8_t *>(request.data()), request.size());
  state_ = State::WRITING;
  rx_buffer_.clear();
  request_started_at_ = millis();
}

// Writes re-enabled 2026-09-01 after the memory-map audit (see
// memory_map.h/.cpp) and a full-payload backup saved to
// python-poc/states/pre_write_enable_20260901.txt (restore reference in case
// a write goes wrong - re-set the affected field's number/switch entity back
// to the value recorded there). This is the single choke point every write
// (switch/number) goes through.
static const bool WRITES_DISABLED = false;

void GicarBridge::request_write_(uint16_t offset, const uint8_t *data, uint8_t len, std::function<void()> on_success) {
  if (WRITES_DISABLED) {
    ESP_LOGW(TAG, "Writes are disabled (memory map not yet fully verified) - NOT sending write to offset %u", offset);
    return;
  }
  if (!connected_) {
    ESP_LOGW(TAG, "Write requested but not connected yet");
    return;
  }
  if (state_ != State::IDLE) {
    ESP_LOGW(TAG, "Write requested but a request is already in flight, ignoring");
    return;
  }
  pending_write_confirm_ = std::move(on_success);
  send_write_request_(offset, data, len);
}

void GicarBridge::update() {
  // Called every update_interval by PollingComponent. start_read() already
  // no-ops safely if we're not connected yet or a request is in flight.
  start_read();
}

void GicarBridge::start_read() {
  if (!connected_) {
    ESP_LOGW(TAG, "Read requested but not connected yet");
    return;
  }
  if (state_ != State::IDLE) {
    ESP_LOGW(TAG, "Read requested but a request is already in flight, ignoring");
    return;
  }
  read_requested_ = true;
}

void GicarBridge::write_byte_field(uint16_t offset, uint8_t raw_value, std::function<void()> on_success) {
  request_write_(offset, &raw_value, 1, std::move(on_success));
}

void GicarBridge::write_numeric_field(const std::string &key, float display_value, std::function<void()> on_success) {
  uint8_t data[4];
  uint8_t len;
  uint16_t offset;
  if (key == "offset_temperature") {
    // Which register is live depends on bytes 76/79 of the current payload.
    if (!has_payload_) {
      ESP_LOGW(TAG, "write offset_temperature: no read yet, can't pick register");
      return;
    }
    encode_offset_temperature(payload_, display_value, data, &len, &offset);
  } else if (!encode_numeric(key, display_value, data, &len, &offset)) {
    ESP_LOGW(TAG, "write_numeric_field: unknown key '%s'", key.c_str());
    return;
  }
  request_write_(offset, data, len, std::move(on_success));
}

void GicarBridge::write_ops(std::vector<WriteOp> ops, std::function<void()> on_success) {
  if (ops.empty()) {
    if (on_success)
      on_success();
    return;
  }
  write_ops_step_(std::move(ops), 0, std::move(on_success));
}

void GicarBridge::write_ops_step_(std::vector<WriteOp> ops, size_t index, std::function<void()> on_success) {
  const WriteOp &op = ops[index];
  bool last = index + 1 >= ops.size();
  // Each step is only queued once the previous one's "OK" came back, so the
  // single-request-in-flight rule in request_write_() is respected.
  request_write_(op.offset, op.data, op.len, [this, ops, index, last, on_success]() mutable {
    if (last) {
      if (on_success)
        on_success();
    } else {
      write_ops_step_(std::move(ops), index + 1, std::move(on_success));
    }
  });
}

void GicarBridge::reset_counters() {
  std::vector<WriteOp> ops;
  for (uint16_t off : GICAR_COUNTER_OFFSETS)
    ops.push_back(WriteOp{off, 4, {0, 0, 0, 0}});
  // The machine never clears its own total, so do it here - otherwise it
  // would carry on incrementing from the pre-reset value.
  ops.push_back(WriteOp{GICAR_COUNTER_TOTAL_OFFSET, 4, {0, 0, 0, 0}});
  ESP_LOGI(TAG, "Resetting the %u button counters + total (lifetime at %u left untouched)",
           (unsigned) (ops.size() - 1), GICAR_COUNTER_LIFETIME_OFFSET);
  write_ops(std::move(ops), []() { ESP_LOGI(TAG, "Counters reset"); });
}

void GicarBridge::sync_clock() {
  if (time_source_ == nullptr) {
    ESP_LOGW(TAG, "sync_clock: no time source configured");
    return;
  }
  auto t = time_source_->now();
  if (!t.is_valid()) {
    ESP_LOGW(TAG, "sync_clock: time not valid yet (no NTP sync?)");
    return;
  }
  // ESPTime day_of_week is 1=Sunday..7=Saturday; the machine wants
  // 1=Monday..7=Sunday.
  uint8_t weekday = t.day_of_week == 1 ? 7 : t.day_of_week - 1;
  // The vendor app clamps a leap second to 0 before sending; match it so the
  // bytes on the wire are identical to what the machine normally receives.
  uint8_t second = t.second > 59 ? 0 : (uint8_t) t.second;
  uint8_t data[7] = {
      second, (uint8_t) t.minute, (uint8_t) t.hour, weekday, (uint8_t) t.day_of_month, (uint8_t) t.month,
      (uint8_t) (t.year % 100),
  };
  ESP_LOGI(TAG, "Syncing machine clock to %04d-%02d-%02d %02d:%02d:%02d (weekday=%d)", t.year, t.month,
           t.day_of_month, t.hour, t.minute, t.second, weekday);
  // Not a normal MEMORY_MAP field - 0xA000 is a reserved command offset for
  // setting the clock.
  request_write_(0xA000, data, 7, []() { ESP_LOGI(TAG, "Clock sync OK"); });
}

void GicarBridge::handle_incoming_() {
  bool got_bytes = false;
  while (serial_bt_.available()) {
    rx_buffer_ += static_cast<char>(serial_bt_.read());
    got_bytes = true;
  }

  if (state_ == State::RAW) {
    if (got_bytes)
      last_rx_at_ = millis();
    // No length to expect, so treat a gap in the stream as the end of it.
    if (rx_buffer_.empty() || millis() - last_rx_at_ < RAW_QUIET_MS)
      return;
    publish_raw_(rx_buffer_);
    rx_buffer_.clear();
    state_ = State::IDLE;
    // A raw command may well have changed something - resync every entity.
    read_requested_ = true;
    return;
  }

  if (state_ == State::READING) {
    size_t expected_response_len = 9 + (size_t) current_chunk_len_ * 2 + 2;
    if (rx_buffer_.size() < expected_response_len)
      return;

    ESP_LOGV(TAG, "Full read response (%d chars): %s", (int) rx_buffer_.size(), rx_buffer_.c_str());
    uint32_t sum = 0;
    for (size_t i = 0; i < rx_buffer_.size() - 2; i++)
      sum += (uint8_t) rx_buffer_[i];
    uint8_t calculated = sum % 256;
    uint8_t expected = strtol(rx_buffer_.substr(rx_buffer_.size() - 2).c_str(), nullptr, 16);

    if (calculated != expected) {
      ESP_LOGW(TAG, "Checksum mismatch: expected 0x%02X, got 0x%02X", expected, calculated);
      state_ = State::IDLE;
      return;
    }

    for (size_t i = 0; i < current_chunk_len_; i++) {
      std::string byte_hex = rx_buffer_.substr(9 + i * 2, 2);
      payload_[i] = strtol(byte_hex.c_str(), nullptr, 16);
    }

    has_payload_ = true;
    ESP_LOGD(TAG, "Read OK");
    publish_all_();
    state_ = State::IDLE;
  } else if (state_ == State::WRITING) {
    if (rx_buffer_.size() < GICAR_WRITE_RESPONSE_LEN)
      return;

    ESP_LOGV(TAG, "Full write response (%d chars): %s", (int) rx_buffer_.size(), rx_buffer_.c_str());
    std::string answer = rx_buffer_.substr(9, 2);
    state_ = State::IDLE;
    if (answer == "OK") {
      ESP_LOGI(TAG, "Write OK");
      auto confirm = std::move(pending_write_confirm_);
      pending_write_confirm_ = nullptr;
      if (confirm)
        confirm();
      // Re-sync every entity from the machine after the write (unless the
      // callback already queued a follow-up write, in which case the last
      // write of that sequence will trigger it).
      if (state_ == State::IDLE) {
        read_requested_ = true;
        read_not_before_ = millis() + WRITE_SETTLE_MS;
      }
    } else {
      ESP_LOGW(TAG, "Write failed, answer: %s", answer.c_str());
      pending_write_confirm_ = nullptr;
    }
  }
}

// Called whenever a connection is established: clears the watchdog and the
// persisted reboot counter, so a later wedge gets a fresh set of attempts.
void GicarBridge::note_connected_() {
  last_ok_at_ = millis();
  if (recovery_reboots_ != 0) {
    recovery_reboots_ = 0;
    recovery_pref_.save(&recovery_reboots_);
  }
}

void GicarBridge::check_recovery_() {
  if (millis() - last_ok_at_ < BT_RECOVERY_TIMEOUT_MS)
    return;
  if (recovery_reboots_ >= MAX_RECOVERY_REBOOTS) {
    // Almost certainly just a machine that is switched off - stop rebooting
    // and keep scanning. A successful connect re-arms this.
    last_ok_at_ = millis();
    ESP_LOGW(TAG, "Still no connection after %u recovery reboots - assuming the machine is off, will keep scanning",
             recovery_reboots_);
    return;
  }
  recovery_reboots_++;
  recovery_pref_.save(&recovery_reboots_);
  global_preferences->sync();
  ESP_LOGW(TAG, "No Bluetooth connection for %u minutes - rebooting to clear the stack (attempt %u/%u)",
           BT_RECOVERY_TIMEOUT_MS / 60000, recovery_reboots_, MAX_RECOVERY_REBOOTS);
  App.safe_reboot();
}

void GicarBridge::loop() {
  if (!connected_) {
    if (serial_bt_.connected()) {
      connected_ = true;
      connected_at_ = millis();
      note_connected_();
      set_status_("connected");
      return;
    }

    if (pin_.empty()) {
      // Nothing to pair with yet - wait for a PIN (set_pin_runtime restarts
      // the scan phase once one arrives). Not a wedge, so hold the watchdog off.
      set_status_("PIN required - set Bluetooth PIN");
      last_ok_at_ = millis();
      return;
    }

    check_recovery_();

    switch (conn_phase_) {
      case ConnPhase::SCANNING: {
        if (!scanning_active_) {
          ESP_LOGI(TAG, "Scanning for '%s'...", device_name_.c_str());
          set_status_("scanning");
          found_via_scan_ = false;
          start_scan_();
          scanning_active_ = true;
          scan_start_ = millis();
        }
        if (found_via_scan_) {
          serial_bt_.discoverAsyncStop();
          scanning_active_ = false;
          conn_phase_ = ConnPhase::CONNECTING;
          connect_attempts_ = 0;
          last_connect_attempt_ = 0;  // allow an immediate first attempt
          set_status_("connecting");
          publish_status_();  // device just got discovered
        } else if (millis() - scan_start_ >= SCAN_DURATION_MS) {
          ESP_LOGI(TAG, "Not found this scan, backing off %u ms before retrying", SCAN_IDLE_MS);
          serial_bt_.discoverAsyncStop();
          scanning_active_ = false;
          conn_phase_ = ConnPhase::IDLE_WAIT;
          phase_started_at_ = millis();
          set_status_("not found, waiting");
        } else if (millis() - last_scan_restart_ > 50000) {
          // A single discoverAsync() call caps out ~61s internally; restart
          // if the scan window needs to be longer than that.
          serial_bt_.discoverAsyncStop();
          start_scan_();
        }
        return;
      }
      case ConnPhase::IDLE_WAIT: {
        // Device not currently visible (e.g. machine powered off) - back off
        // instead of hammering connect()/scan continuously.
        if (millis() - phase_started_at_ >= SCAN_IDLE_MS)
          conn_phase_ = ConnPhase::SCANNING;
        return;
      }
      case ConnPhase::CONNECTING: {
        try_connect_();
        if (connected_)
          return;
        if (connect_attempts_ >= MAX_CONNECT_ATTEMPTS) {
          ESP_LOGW(TAG, "Giving up after %d attempts, back to scanning", connect_attempts_);
          conn_phase_ = ConnPhase::SCANNING;
          set_status_(pin_verified_ ? "connect failed, rescanning" : "connect failed - wrong PIN?");
        }
        return;
      }
    }
    return;
  }

  if (!serial_bt_.connected()) {
    ESP_LOGW(TAG, "Lost connection");
    connected_ = false;
    set_status_("disconnected");
    state_ = State::IDLE;
    conn_phase_ = ConnPhase::SCANNING;  // re-confirm presence before reconnecting
    return;
  }

  if (state_ == State::IDLE) {
    // int32_t comparison so this still works across a millis() wrap.
    bool settled = (int32_t) (millis() - read_not_before_) >= 0;
    if (read_requested_ && settled && millis() - connected_at_ >= READ_SETTLE_MS) {
      read_requested_ = false;
      send_read_request_();
    }
    return;
  }

  if (millis() - request_started_at_ > REQUEST_TIMEOUT_MS) {
    if (state_ == State::RAW)
      publish_raw_("no response (timed out)");
    ESP_LOGW(TAG, "Request timed out, got %d bytes", (int) rx_buffer_.size());
    state_ = State::IDLE;
    rx_buffer_.clear();
    return;
  }

  handle_incoming_();
}

float GicarBridge::get_numeric(const std::string &key) const {
  if (!has_payload_)
    return NAN;
  return extract_numeric(payload_, key);
}

std::string GicarBridge::get_text(const std::string &key) const {
  if (!has_payload_)
    return "";
  return extract_text(payload_, key);
}

int GicarBridge::get_raw_byte(uint16_t abs_offset) const {
  if (!has_payload_)
    return -1;
  return extract_raw_byte(payload_, abs_offset);
}

void GicarBridge::publish_all_() {
  // Only publish values that actually changed - every read returns the full
  // snapshot, and republishing ~50 unchanged entities each time floods the
  // log and Home Assistant with no-op updates.
  for (auto *sensor : sensors_) {
    float v = this->get_numeric(sensor->get_key());
    if (!sensor->has_state() || sensor->state != v)
      sensor->publish_state(v);
  }
  for (auto *text_sensor : text_sensors_) {
    const auto &key = text_sensor->get_key();
    if (key == "bluetooth_status" || key == "bluetooth_device" || key == "machine_number" ||
        key == "raw_response")
      continue;  // bridge-side, published by publish_status_()
    std::string v = this->get_text(key);
    if (!text_sensor->has_state() || text_sensor->state != v)
      text_sensor->publish_state(v);
  }
  // Switches first so their remembered time is fresh for the time entities.
  for (auto *sw : autotimer_switches_) {
    sw->update_from_raw(extract_raw_byte(payload_, sw->get_hour_offset()),
                        extract_raw_byte(payload_, sw->get_minute_offset()));
  }
  for (auto *at : autotimer_times_) {
    int hour = extract_raw_byte(payload_, at->get_hour_offset());
    int minute = extract_raw_byte(payload_, at->get_minute_offset());
    if (hour < 0 || minute < 0)
      continue;
    if (hour >= 24 || minute >= 60) {
      // Timer disabled (100/100 sentinel): show the time that re-enabling
      // would restore, so the entity isn't blank/00:00 after a reboot.
      for (auto *sw : autotimer_switches_) {
        if (sw->get_hour_offset() == at->get_hour_offset()) {
          uint8_t h, m;
          sw->get_remembered(&h, &m);
          hour = h;
          minute = m;
          break;
        }
      }
    }
    at->publish_from_raw((uint8_t) hour, (uint8_t) minute);
  }
  for (auto *sw : switches_) {
    // Switch::publish_state dedups on its own.
    sw->publish_state(extract_raw_byte(payload_, sw->get_offset()) == sw->get_on_value());
  }
  for (auto *sel : selects_) {
    sel->publish_from_raw(extract_raw_byte(payload_, sel->get_offset()));
  }
  for (auto *number : numbers_) {
    float v = this->get_numeric(number->get_key());
    if (!number->has_state() || number->state != v)
      number->publish_state(v);
  }
}

}  // namespace gicar
}  // namespace esphome
