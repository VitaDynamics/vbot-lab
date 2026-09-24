#include "PointCloud_generated.h"
#include "bms_state_generated.h"
#include "imu_generated.h"
#include "recipes/observe.h"

using namespace recipe;
int main(int argc, char **argv) {
  return Observe(
      argc, argv, "sensors",
      {{"battery", "/bms_state"},
       {"imu", "/imu_raw"},
       {"lidar-imu", "/lidar_imu"},
       {"points", "/lidar_points"}},
      "battery", [](const std::string &stream, const auto &bytes) {
        if (stream == "battery") {
          const auto *m = Decode<bms::BmsState>(bytes);
          return Object(
              {{"timestamp_ns", std::to_string(m->sensor_timestamp_ns())},
               {"voltage_v", N(m->voltage_mv() / 1000.0)},
               {"current_a", N(m->current_ma() / 1000.0)},
               {"soc_percent", N(m->soc_percent())},
               {"alarm", N(m->alarm())},
               {"charger_connected", B(m->is_charger_connected())}});
        }
        if (stream == "imu" || stream == "lidar-imu") {
          const auto *m = Decode<aorta::topic::sensor::Imu>(bytes);
          const auto *q = m->orientation();
          const double norm = q ? std::sqrt(q->x() * q->x() + q->y() * q->y() +
                                            q->z() * q->z() + q->w() * q->w())
                                : 0;
          auto number = [](double value) { return N(value); };
          return Object(
              {{"timestamp_ns", Stamp(m->timestamp())},
               {"frame_id", Json(Text(m->frame_id()))},
               {"orientation_raw_xyzw", Q(q)},
               {"orientation_norm", q ? N(norm) : "null"},
               {"orientation_unit_length",
                B(q && std::isfinite(norm) && std::abs(norm - 1) <= 0.01)},
               {"angular_velocity_raw", V(m->angular_velocity())},
               {"linear_acceleration_raw", V(m->linear_acceleration())},
               {"orientation_covariance",
                Array(m->orientation_covariance(), number)},
               {"angular_velocity_covariance",
                Array(m->angular_velocity_covariance(), number)},
               {"linear_acceleration_covariance",
                Array(m->linear_acceleration_covariance(), number)}});
        }
        const auto *m = Decode<foxglove::PointCloud>(bytes);
        const auto stride = m->point_stride(),
                   size = m->data() ? m->data()->size() : 0;
        if (!stride || size % stride)
          throw std::runtime_error("invalid point-cloud stride/data length");
        return Object({{"timestamp_ns", Stamp(m->timestamp())},
                       {"frame_id", Json(Text(m->frame_id()))},
                       {"point_stride", N(stride)},
                       {"data_bytes", N(size)},
                       {"point_count", N(size / stride)},
                       {"fields", Array(m->fields(), [](const auto *field) {
                          return Object({{"name", Json(Text(field->name()))},
                                         {"offset", N(field->offset())},
                                         {"type", N(int(field->type()))}});
                        })}});
      });
}
