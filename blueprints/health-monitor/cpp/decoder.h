#pragma once

#include "blueprints/health-monitor/cpp/model.h"
#include "bms_state_generated.h"
#include "locomotion_status_generated.h"
#include "recipes/cpp_common.h"
#include "sm_status_generated.h"

namespace health {
struct ReceivedSample {
  Stream stream;
  recipe::Bytes bytes;
  double received_at;
};
inline Sample Decode(Stream stream, const recipe::Bytes &bytes) {
  Sample result;
  if (stream == Stream::State) {
    const auto *value = recipe::Decode<locomotion::LocomotionStatus>(bytes);
    result.stamp_ns = value->stamp_ns();
    result.heartbeat_seq = value->heartbeat_seq();
    result.posture = static_cast<int>(value->posture());
    result.motion = static_cast<int>(value->motion());
  } else if (stream == Stream::Battery) {
    const auto *value = recipe::Decode<bms::BmsState>(bytes);
    result.stamp_ns = value->sensor_timestamp_ns();
    result.soc_percent = value->soc_percent();
    result.voltage_v = value->voltage_mv() / 1000.0;
  } else if (stream == Stream::System) {
    const auto *value = recipe::Decode<sm::SmStatus>(bytes);
    result.stamp_ns = value->sensor_timestamp_ns();
    result.heartbeat_seq = value->heartbeat_seq();
    result.state_id = value->state_id();
    result.severity = static_cast<int>(value->severity());
  } else {
    throw std::invalid_argument("unknown telemetry stream");
  }
  return result;
}
inline void Consume(Monitor &monitor, const ReceivedSample &event) {
  Sample sample;
  try {
    sample = Decode(event.stream, event.bytes);
  } catch (const std::runtime_error &) {
    sample.valid = false;
  }
  monitor.Update(event.stream, sample, event.received_at);
}
} // namespace health
