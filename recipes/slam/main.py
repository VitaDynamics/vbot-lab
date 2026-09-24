"""Observe SLAM status, odometry, or transforms without mode changes."""
from recipes.common import run, text
from recipes.observe import observe, vector

ROUTES = {
    "status": ("/slam/status", "aorta.topic.slam.SlamStatus"),
    "odometry": ("/odometry", "aorta.topic.navigation.Odometry"),
    "transforms": ("/slam/static_transforms", "aorta.topic.slam.TransformArray"),
}


def pose(position, orientation):
    return None if position is None or orientation is None else dict(
        position_m=vector(position), orientation_xyzw=vector(orientation, True))


def summarize(stream, m):
    if stream == "status":
        return dict(timestamp_ns=m.SensorTimestampNs(), operation_mode=m.OperationMode(),
                    odom_status=m.OdomStatus(), loc_status=m.LocStatus(), map_status=m.MapStatus(),
                    current_map_name=text(m.CurrentMapName()), num_keyframes=m.NumKeyframes())
    if stream == "odometry":
        return dict(timestamp_ns=m.SensorTimestampNs(), frame_id=text(m.FrameId()),
                    child_frame_id=text(m.ChildFrameId()), pose=pose(m.PosePosition(), m.PoseOrientation()),
                    body_in_map=pose(m.BodyPositionInMap(), m.BodyOrientationInMap()),
                    head_in_body=pose(m.HeadPositionInBody(), m.HeadOrientationInBody()))
    if stream == "transforms":
        return dict(timestamp_ns=m.SensorTimestampNs(), is_static=m.IsStatic(), transforms=[
            dict(frame_id=text(m.Transforms(i).FrameId()), child_frame_id=text(m.Transforms(i).ChildFrameId()),
                 pose=pose(m.Transforms(i).Translation(), m.Transforms(i).Rotation()))
            for i in range(m.TransformsLength())])
    raise ValueError("unsupported SLAM stream: " + stream)


def main(argv=None):
    return observe("slam", ROUTES, summarize, argv)


if __name__ == "__main__":
    raise SystemExit(run(main))
