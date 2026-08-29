#pragma once

#include "esphome/core/component.h"
#include "esphome/core/preferences.h"
#include "memory_map.h"
#include <BluetoothSerial.h>
#include <functional>
#include <string>
#include <vector>

namespace esphome {
namespace time {
class RealTimeClock;
}
namespace gicar {

class GicarSensor;
class GicarTextSensor;
class GicarSwitch;
class GicarSelect;
class GicarNumber;
class GicarReadIntervalNumber;
class GicarAutotimerTime;
class GicarAutotimerEnableSwitch;
class GicarPinText;

// w[offset:4][len:4]OK[checksum:2]
static const size_t GICAR_WRITE_RESPONSE_LEN = 13;

// One atomic write request: `len` raw bytes at absolute `offset`.
struct WriteOp {
  uint16_t offset;
  uint8_t len;
  uint8_t data[4];
};

// See memory_map.h for the offset/value-mapping reference this reads from.
class GicarBridge : public PollingComponent {
 public:
  void set_device_name(const std::string &name) { device_name_ = name; }
  void set_pin(const std::string &pin) { pin_ = pin; }
  void set_mac_address(uint8_t b0, uint8_t b1, uint8_t b2, uint8_t b3, uint8_t b4, uint8_t b5) {
    mac_address_[0] = b0;
    mac_address_[1] = b1;
    mac_address_[2] = b2;
    mac_address_[3] = b3;
    mac_address_[4] = b4;
    mac_address_[5] = b5;
    has_mac_address_ = true;
  }

  void register_sensor(GicarSensor *sensor) { sensors_.push_back(sensor); }
  void register_text_sensor(GicarTextSensor *sensor) { text_sensors_.push_back(sensor); }
  void register_switch(GicarSwitch *sw) { switches_.push_back(sw); }
  void register_select(GicarSelect *sel) { selects_.push_back(sel); }
  void register_number(GicarNumber *n) { numbers_.push_back(n); }
  void register_read_interval_number(GicarReadIntervalNumber *n) { read_interval_number_ = n; }
  void register_autotimer_time(GicarAutotimerTime *t) { autotimer_times_.push_back(t); }
  void register_autotimer_enable_switch(GicarAutotimerEnableSwitch *s) { autotimer_switches_.push_back(s); }
  void register_pin_text(GicarPinText *t) { pin_text_ = t; }
  void set_time_source(time::RealTimeClock *time_source) { time_source_ = time_source; }

  // Change the classic-BT pairing PIN at runtime (from the "Bluetooth PIN"
  // text entity). Persisted to flash and used for every later connect; the
  // YAML `pin:` only acts as the default before one has been set. If we're
  // not currently connected, the connect cycle restarts immediately with the
  // new PIN.
  void set_pin_runtime(const std::string &pin);

  // Send an arbitrary protocol command (e.g. "r00050010" to read 16 bytes at
  // offset 5, or "w0029000105" to write one byte). The checksum is appended
  // automatically. The reply is published to the "raw_response" text sensor
  // and logged in full at INFO. Debug tool - it can write anything the
  // protocol can express, including offsets the machine faults on.
  void send_raw_command(const std::string &command);
  const std::string &get_pin() const { return pin_; }

  // Trigger a read of the full memory map. Safe to call repeatedly (e.g. from
  // a button press); ignored if not connected or a request is in flight.
  void start_read();

  // Push the current time (from the configured `time:` source, e.g. NTP) to
  // the machine's clock. Not a normal MEMORY_MAP field - uses a special
  // reserved command offset (0xA000). The clock cannot be read back.
  void sync_clock();

  // Zero the five per-button coffee counters (S1/S2/L1/L2/flush), exactly
  // what the machine's "Reset counter" does (u32 zeros to 134..150). The
  // lifetime total at 210 is deliberately left alone.
  void reset_counters();

  // Tear down and re-initialise the classic-BT stack, then restart the
  // scan/connect cycle from scratch. This module's BT stack occasionally
  // wedges after repeated connect/disconnect cycles (e.g. power-cycling the
  // machine) and stops seeing the device even while it is advertising
  // happily to everything else - this is the softer alternative to
  // rebooting the whole ESP.
  void reconnect_bluetooth();

  // Generic single-byte write, e.g. for on/off switches (offset, raw value).
  // on_success is called with the write confirmed (the "OK" response seen)
  // so the entity can optimistically-but-correctly update its displayed
  // state. Every successful write also schedules a full re-read so all
  // entities re-sync from the machine's real state.
  void write_byte_field(uint16_t offset, uint8_t raw_value, std::function<void()> on_success);
  // Generic write for a MEMORY_MAP numeric key (same table get_numeric() reads
  // from) - handles multiplier + u8/u16le/u32le encoding automatically.
  void write_numeric_field(const std::string &key, float display_value, std::function<void()> on_success);
  // Sequence of atomic writes, sent back to back; on_success only fires once
  // every one of them has been confirmed. Aborts the sequence on the first
  // failure.
  void write_ops(std::vector<WriteOp> ops, std::function<void()> on_success);

  // Live-adjustable polling interval, persisted to flash so it survives
  // reboots (restored in setup()).
  void set_read_interval_seconds(float seconds, bool persist = true);

  void setup() override;
  void loop() override;
  // PollingComponent hook - triggers a read every update_interval (config
  // key `update_interval:`, standard ESPHome duration schema). Also
  // adjustable live via a number entity - see GicarReadIntervalNumber.
  void update() override;

  // Generic accessors for already-parsed data, keyed the same way as
  // python-poc/lib/ascaso_offsets.py's MEMORY_MAP. NAN / "" if no successful
  // read has happened yet or the key is unknown.
  float get_numeric(const std::string &key) const;
  std::string get_text(const std::string &key) const;
  // Raw byte at an absolute offset, or -1 if no payload yet / out of range.
  int get_raw_byte(uint16_t abs_offset) const;

 protected:
  enum class State { IDLE, READING, WRITING, RAW };
  // Never call connect() blindly - only after a scan has freshly confirmed
  // the device is actually present. When it's off/out of range, scans just
  // find nothing and we back off to idle instead of hammering connect().
  enum class ConnPhase { SCANNING, IDLE_WAIT, CONNECTING };

  void start_bluetooth_();
  void start_scan_();
  void try_connect_();
  void send_read_request_();
  void send_write_request_(uint16_t offset, const uint8_t *data, uint8_t len);
  void request_write_(uint16_t offset, const uint8_t *data, uint8_t len, std::function<void()> on_success);
  void write_ops_step_(std::vector<WriteOp> ops, size_t index, std::function<void()> on_success);
  void handle_incoming_();
  void publish_all_();
  // Push connection status / discovered device to the matching text sensors
  // ("bluetooth_status" / "bluetooth_device" keys) - independent of reads.
  void set_status_(const char *status);
  void publish_status_();
  void publish_raw_(const std::string &text);

  BluetoothSerial serial_bt_;
  std::string device_name_;
  std::string pin_;
  uint8_t mac_address_[6]{0};
  bool has_mac_address_{false};

  bool connected_{false};
  State state_{State::IDLE};
  bool read_requested_{true};  // auto-read once right after connecting
  // Earliest millis() at which a pending re-read may be sent - see
  // WRITE_SETTLE_MS. 0 means "no wait", which is what a manual or periodic
  // read wants; only a post-write re-read pushes it forward.
  uint32_t read_not_before_{0};
  std::string rx_buffer_;
  uint8_t payload_[GICAR_PAYLOAD_LEN]{0};
  bool has_payload_{false};
  // Expected payload byte count for the read request currently in flight -
  // used to compute the expected response length.
  uint16_t current_chunk_len_{0};

  // A classic-BT discovery scan before a connect attempt has proven necessary
  // in practice - address-based connect() reliably fails with a page timeout
  // without one. We also use the scan to find the device's current address
  // live instead of relying on a hardcoded one.
  ConnPhase conn_phase_{ConnPhase::SCANNING};
  bool scanning_active_{false};
  bool found_via_scan_{false};
  uint8_t scanned_mac_[6]{0};
  uint32_t scan_start_{0};
  uint32_t last_scan_restart_{0};
  uint32_t phase_started_at_{0};
  uint8_t connect_attempts_{0};

  // Recovery watchdog: the module's BT stack can wedge such that scans never
  // see the machine again, and reinitialising bluedroid in software does not
  // clear it (tried, and it failed against a real wedge) - only a chip reset
  // does. last_ok_at_ is the last time we were connected, or boot.
  uint32_t last_ok_at_{0};
  uint8_t recovery_reboots_{0};
  ESPPreferenceObject recovery_pref_;
  void note_connected_();
  void check_recovery_();

  uint32_t last_connect_attempt_{0};
  uint32_t connected_at_{0};
  uint32_t request_started_at_{0};
  uint32_t last_rx_at_{0};       // last time a raw reply produced bytes
  std::string raw_response_;

  std::function<void()> pending_write_confirm_;
  ESPPreferenceObject read_interval_pref_;
  ESPPreferenceObject pin_pref_;
  bool pin_verified_{false};  // a connect succeeded with the current pin_
  std::string bt_status_{"starting"};
  std::string bt_device_;  // "<name> (<mac>)" of the unit found by the scan
  std::string bt_machine_number_;  // digits of the advertised name, e.g. "0313"

  std::vector<GicarSensor *> sensors_;
  std::vector<GicarTextSensor *> text_sensors_;
  std::vector<GicarSwitch *> switches_;
  std::vector<GicarSelect *> selects_;
  std::vector<GicarNumber *> numbers_;
  GicarReadIntervalNumber *read_interval_number_{nullptr};
  GicarPinText *pin_text_{nullptr};
  std::vector<GicarAutotimerTime *> autotimer_times_;
  std::vector<GicarAutotimerEnableSwitch *> autotimer_switches_;
  time::RealTimeClock *time_source_{nullptr};
};

}  // namespace gicar
}  // namespace esphome
