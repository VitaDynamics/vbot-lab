"""Read object detections and human keypoints; never trigger speech or motion."""
import math
from recipes.common import run, text
from recipes.observe import observe, vector

ROUTES = {
    "detections": ("/perception/detections2d", "perception.Detection2DArray"),
    "poses": ("/perception/poses", "perception.PoseDetection"),
}


def probability(logit):
    if not math.isfinite(logit):
        return None
    if logit >= 0:
        return 1 / (1 + math.exp(-logit))
    value = math.exp(logit)
    return value / (1 + value)


def summarize(stream, m):
    result = dict(timestamp_ns=m.TimestampNs(), frame_id=text(m.FrameId()))
    if stream == "detections":
        detections = []
        for i in range(m.DetectionsLength()):
            item = m.Detections(i)
            box = item.Bbox()
            detections.append(dict(class_id=text(item.ClassId()), score=item.Score(),
                bbox_center_size_px=None if box is None else
                [box.CenterX(), box.CenterY(), box.Width(), box.Height()]))
        result.update(frame_width=m.FrameWidth(), frame_height=m.FrameHeight(), detections=detections,
                      person_boxes=sum(item["class_id"] == "person" for item in detections))
    else:
        result.update(class_id=m.ClassId(), score=m.Score(), bbox_min_px=vector(m.BboxMin()),
                      bbox_max_px=vector(m.BboxMax()), keypoints=[
                          dict(index=i, x_px=m.Keypoints(i).X(), y_px=m.Keypoints(i).Y(),
                               confidence_logit=m.Keypoints(i).Confidence(),
                               confidence_probability=probability(m.Keypoints(i).Confidence()))
                          for i in range(m.KeypointsLength())])
    return result


def main(argv=None):
    return observe("perception", ROUTES, summarize, argv)


if __name__ == "__main__":
    raise SystemExit(run(main))
