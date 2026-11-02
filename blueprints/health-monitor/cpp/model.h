#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <map>
#include <optional>
#include <regex>
#include <set>
#include <stdexcept>
#include <string>

namespace health {
struct Config {
  double stale_after_seconds = 3;
  double low_battery_percent = 20;
};
inline void Validate(Config config) {
  if (!std::isfinite(config.stale_after_seconds) ||
      config.stale_after_seconds <= 0 || config.stale_after_seconds > 120 ||
      !std::isfinite(config.low_battery_percent) ||
      config.low_battery_percent < 0 || config.low_battery_percent > 100)
    throw std::invalid_argument("invalid freshness or battery threshold");
}

// Only the two numeric configuration properties are supported. No JSON library
// or runtime dependency is needed; reject unknown/duplicate keys and trailing
// data.
inline Config ParseConfig(const std::string &text) {
  if (text.size() > 4096)
    throw std::invalid_argument("configuration exceeds 4096 bytes");
  size_t position = 0;
  auto space = [&] {
    while (position < text.size() &&
           std::string(" \t\r\n").find(text[position]) != std::string::npos)
      ++position;
  };
  auto expect = [&](char value) {
    space();
    if (position >= text.size() || text[position++] != value)
      throw std::invalid_argument("invalid configuration object");
  };
  expect('{');
  std::map<std::string, double> fields;
  const std::regex number("-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?");
  for (int i = 0; i < 2; ++i) {
    if (i)
      expect(',');
    expect('"');
    const size_t begin = position;
    while (position < text.size() && text[position] != '"')
      ++position;
    if (position == text.size())
      throw std::invalid_argument("unterminated configuration key");
    const auto key = text.substr(begin, position++ - begin);
    if ((key != "stale_after_seconds" && key != "low_battery_percent") ||
        fields.count(key))
      throw std::invalid_argument("unknown or duplicate configuration key");
    expect(':');
    space();
    const size_t start = position;
    while (position < text.size() &&
           std::string(" \t\r\n,}").find(text[position]) == std::string::npos)
      ++position;
    const auto token = text.substr(start, position - start);
    if (!std::regex_match(token, number))
      throw std::invalid_argument("configuration values must be JSON numbers");
    try {
      fields[key] = std::stod(token);
    } catch (const std::exception &) {
      throw std::invalid_argument("configuration number out of range");
    }
  }
  expect('}');
  space();
  if (position != text.size())
    throw std::invalid_argument("trailing configuration data");
  Config config{fields.at("stale_after_seconds"),
                fields.at("low_battery_percent")};
  Validate(config);
  return config;
}
inline Config LoadConfig(const std::string &path) {
  std::ifstream input(path, std::ios::binary);
  if (!input)
    throw std::runtime_error("cannot read configuration file");
  std::string content;
  char value;
  while (input.get(value)) {
    content.push_back(value);
    if (content.size() > 4096)
      throw std::runtime_error("configuration exceeds 4096 bytes");
  }
  if (!input.eof())
    throw std::runtime_error("cannot read complete configuration");
  try {
    return ParseConfig(content);
  } catch (const std::invalid_argument &error) {
    throw std::runtime_error(error.what());
  }
}

enum class Stream { State, Battery, System };
constexpr std::array<const char *, 3> kNames = {"state", "battery", "system"};
constexpr std::array<const char *, 3> kRoutes = {
    "/locomotion/status", "/bms_state", "/system/sm_status"};
inline size_t Index(Stream stream) {
  const size_t index = static_cast<size_t>(stream);
  if (index >= kNames.size())
    throw std::invalid_argument("unknown telemetry stream");
  return index;
}
struct Sample {
  uint64_t stamp_ns = 0, heartbeat_seq = 0;
  int posture = 0, motion = 0, state_id = 0, severity = 0;
  double soc_percent = 0, voltage_v = 0;
  bool valid = true;
};
struct State {
  std::optional<double> received_at;
  uint64_t stamp_ns = 0, samples = 0, invalid = 0, out_of_order = 0;
  Sample data;
};
struct StreamSnapshot {
  const char *status;
  std::optional<double> age_seconds;
  State state;
};
struct Snapshot {
  bool all_streams_receiving = true, low_battery = false;
  std::array<StreamSnapshot, 3> streams;
};
class Monitor {
public:
  explicit Monitor(Config config) : config_(config) { Validate(config); }
  bool Update(Stream stream, const Sample &sample, double now) {
    if (!std::isfinite(now))
      throw std::invalid_argument("invalid local clock");
    auto &state = streams_.at(Index(stream));
    if (!sample.valid ||
        (stream == Stream::Battery &&
         (!std::isfinite(sample.soc_percent) || sample.soc_percent < 0 ||
          sample.soc_percent > 100))) {
      ++state.invalid;
      return false;
    }
    if (sample.stamp_ns && state.stamp_ns &&
        sample.stamp_ns <= state.stamp_ns) {
      ++state.out_of_order;
      return false;
    }
    state.received_at = now;
    state.stamp_ns = sample.stamp_ns;
    state.data = sample;
    ++state.samples;
    return true;
  }
  Snapshot Get(double now) const {
    if (!std::isfinite(now))
      throw std::invalid_argument("invalid local clock");
    Snapshot result;
    for (size_t i = 0; i < streams_.size(); ++i) {
      const auto &state = streams_[i];
      const auto age =
          state.received_at
              ? std::optional<double>(std::max(0.0, now - *state.received_at))
              : std::nullopt;
      const char *status = !age                                 ? "waiting_data"
                           : *age > config_.stale_after_seconds ? "stale"
                                                                : "receiving";
      result.streams[i] = {status, age, state};
      const bool receiving = age && *age <= config_.stale_after_seconds;
      result.all_streams_receiving &= receiving;
      if (i == Index(Stream::Battery))
        result.low_battery =
            receiving && state.data.soc_percent < config_.low_battery_percent;
    }
    return result;
  }

private:
  Config config_;
  std::array<State, 3> streams_{};
};
} // namespace health
