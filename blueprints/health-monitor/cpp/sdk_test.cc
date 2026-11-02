#include "blueprints/health-monitor/cpp/decoder.h"

template <class F> recipe::Bytes Pack(F fill) {
  flatbuffers::FlatBufferBuilder builder;
  builder.Finish(fill(builder));
  return {builder.GetBufferPointer(),
          builder.GetBufferPointer() + builder.GetSize()};
}
void Check(bool value, const char *description) {
  if (!value)
    throw std::runtime_error(description);
}
int main() {
  return recipe::Run([] {
    // Generated types and verifier only: no Node, publishers or subscriptions.
    auto value = health::Decode(health::Stream::Battery, Pack([](auto &buffer) {
                                  bms::BmsStateBuilder builder(buffer);
                                  builder.add_sensor_timestamp_ns(123);
                                  builder.add_soc_percent(75);
                                  builder.add_voltage_mv(42000);
                                  return builder.Finish();
                                }));
    Check(value.stamp_ns == 123 && value.soc_percent == 75 &&
              value.voltage_v == 42,
          "battery decode");
    value =
        health::Decode(health::Stream::State, Pack([](auto &buffer) {
                         locomotion::LocomotionStatusBuilder builder(buffer);
                         builder.add_stamp_ns(124);
                         builder.add_heartbeat_seq(7);
                         return builder.Finish();
                       }));
    Check(value.stamp_ns == 124 && value.heartbeat_seq == 7, "state decode");
    value = health::Decode(health::Stream::System, Pack([](auto &buffer) {
                             sm::SmStatusBuilder builder(buffer);
                             builder.add_sensor_timestamp_ns(125);
                             builder.add_heartbeat_seq(8);
                             builder.add_state_id(4);
                             return builder.Finish();
                           }));
    Check(value.stamp_ns == 125 && value.heartbeat_seq == 8 &&
              value.state_id == 4,
          "system decode");
    for (auto stream : {health::Stream::State, health::Stream::Battery,
                        health::Stream::System}) {
      for (const recipe::Bytes &bad : {recipe::Bytes{1, 2, 3}, recipe::Bytes(8, 0)}) {
        bool rejected = false;
        try {
          health::Decode(stream, bad);
        } catch (const std::runtime_error &) {
          rejected = true;
        }
        Check(rejected, "malformed FlatBuffer rejection");
      }
    }
    health::Monitor monitor({3, 20});
    const std::vector<health::ReceivedSample> backlog = {
        {health::Stream::State, Pack([](auto &buffer) {
           locomotion::LocomotionStatusBuilder builder(buffer);
           builder.add_stamp_ns(1);
           builder.add_heartbeat_seq(1);
           return builder.Finish();
         }),
         0},
        {health::Stream::Battery, Pack([](auto &buffer) {
           bms::BmsStateBuilder builder(buffer);
           builder.add_sensor_timestamp_ns(1);
           builder.add_soc_percent(80);
           return builder.Finish();
         }),
         0},
        {health::Stream::System, Pack([](auto &buffer) {
           sm::SmStatusBuilder builder(buffer);
           builder.add_sensor_timestamp_ns(1);
           builder.add_heartbeat_seq(1);
           return builder.Finish();
         }),
         0}};
    // Processing queued data later must not refresh its callback timestamp.
    for (const auto &event : backlog)
      health::Consume(monitor, event);
    const auto result = monitor.Get(6.1);
    Check(!result.all_streams_receiving, "queued input is stale");
    for (const auto &stream : result.streams)
      Check(std::string(stream.status) == "stale" && *stream.age_seconds == 6.1,
            "preserve callback receive time");
    health::Consume(monitor, {health::Stream::Battery, {1, 2, 3}, 5});
    const auto invalid = monitor.Get(6.1).streams[1];
    Check(invalid.state.invalid == 1 && *invalid.age_seconds == 6.1,
          "malformed input cannot refresh the last valid sample");
    return 0;
  });
}
