#include "odometry_generated.h"
#include "recipes/observe.h"
#include "slam_status_generated.h"
#include "transform_array_generated.h"

using namespace recipe;
int main(int argc, char **argv) {
  return Observe(
      argc, argv, "slam",
      {{"status", "/slam/status"},
       {"odometry", "/odometry"},
       {"transforms", "/slam/static_transforms"}},
      "status", [](const std::string &stream, const auto &bytes) {
        if (stream == "status") {
          const auto *m = Decode<aorta::topic::slam::SlamStatus>(bytes);
          return Object(
              {{"timestamp_ns", std::to_string(m->sensor_timestamp_ns())},
               {"operation_mode", N(m->operation_mode())},
               {"odom_status", N(m->odom_status())},
               {"loc_status", N(m->loc_status())},
               {"map_status", N(m->map_status())},
               {"current_map_name", Json(Text(m->current_map_name()))},
               {"num_keyframes", N(m->num_keyframes())}});
        }
        if (stream == "odometry") {
          const auto *m = Decode<aorta::topic::navigation::Odometry>(bytes);
          return Object(
              {{"timestamp_ns", std::to_string(m->sensor_timestamp_ns())},
               {"frame_id", Json(Text(m->frame_id()))},
               {"child_frame_id", Json(Text(m->child_frame_id()))},
               {"pose", Pose(m->pose_position(), m->pose_orientation())},
               {"body_in_map",
                Pose(m->body_position_in_map(), m->body_orientation_in_map())},
               {"head_in_body", Pose(m->head_position_in_body(),
                                     m->head_orientation_in_body())}});
        }
        if (stream == "transforms") {
          const auto *m = Decode<aorta::topic::slam::TransformArray>(bytes);
          return Object(
              {{"timestamp_ns", std::to_string(m->sensor_timestamp_ns())},
               {"is_static", B(m->is_static())},
               {"transforms", Array(m->transforms(), [](const auto *t) {
                  return Object(
                      {{"frame_id", Json(Text(t->frame_id()))},
                       {"child_frame_id", Json(Text(t->child_frame_id()))},
                       {"pose", Pose(t->translation(), t->rotation())}});
                })}});
        }
        throw std::invalid_argument("unsupported SLAM stream: " + stream);
      });
}
