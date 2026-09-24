#include "detection_2d_generated.h"
#include "pose_detection_generated.h"
#include "recipes/observe.h"

using namespace recipe;
int main(int argc, char **argv) {
  return Observe(
      argc, argv, "perception",
      {{"detections", "/perception/detections2d"},
       {"poses", "/perception/poses"}},
      "detections", [](const std::string &stream, const auto &bytes) {
        if (stream == "detections") {
          const auto *m = Decode<perception::Detection2DArray>(bytes);
          int people = 0;
          auto detections = Array(m->detections(), [&](const auto *d) {
            if (Text(d->class_id()) == "person")
              ++people;
            const auto *box = d->bbox();
            return Object(
                {{"class_id", Json(Text(d->class_id()))},
                 {"score", N(d->score())},
                 {"bbox_center_size_px",
                  box ? '[' + N(box->center_x()) + ',' + N(box->center_y()) +
                            ',' + N(box->width()) + ',' + N(box->height()) + ']'
                      : "null"}});
          });
          return Object({{"timestamp_ns", std::to_string(m->timestamp_ns())},
                         {"frame_id", Json(Text(m->frame_id()))},
                         {"frame_width", N(m->frame_width())},
                         {"frame_height", N(m->frame_height())},
                         {"detections", detections},
                         {"person_boxes", N(people)}});
        }
        const auto *m = Decode<perception::PoseDetection>(bytes);
        int index = 0;
        auto keypoints = Array(m->keypoints(), [&](const auto *k) {
          double logit = k->confidence();
          double e = std::exp(-std::abs(logit));
          return Object(
              {{"index", N(index++)},
               {"x_px", N(k->x())},
               {"y_px", N(k->y())},
               {"confidence_logit", N(logit)},
               {"confidence_probability",
                std::isfinite(logit) ? N(logit >= 0 ? 1 / (1 + e) : e / (1 + e))
                                     : "null"}});
        });
        return Object({{"timestamp_ns", std::to_string(m->timestamp_ns())},
                       {"frame_id", Json(Text(m->frame_id()))},
                       {"class_id", N(m->class_id())},
                       {"score", N(m->score())},
                       {"bbox_min_px", V(m->bbox_min())},
                       {"bbox_max_px", V(m->bbox_max())},
                       {"keypoints", keypoints}});
      });
}
