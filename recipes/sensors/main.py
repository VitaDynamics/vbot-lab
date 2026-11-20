"""Read battery, inertial data, or LiDAR point-cloud layout."""
import math
from recipes.common import run, text
from recipes.observe import observe, vector, stamp

ROUTES = {
    "battery": ("/bms_state", "bms.BmsState"),
    "imu": ("/imu_raw", "aorta.topic.sensor.Imu"),
    "lidar-imu": ("/lidar_imu", "aorta.topic.sensor.Imu"),
    "points": ("/lidar_points", "foxglove.PointCloud"),
}


def summarize(stream, m):
    if stream == "battery":
        alarm_full = m.AlarmFull()
        return dict(timestamp_ns=m.SensorTimestampNs(), voltage_v=m.VoltageMv() / 1000,
                    current_a=m.CurrentMa() / 1000, soc_percent=m.SocPercent(),
                    alarm=m.Alarm(), alarm_full=alarm_full,
                    effective_alarm=m.Alarm() if alarm_full is None else alarm_full,
                    charger_connected=m.IsChargerConnected(),
                    charge_state=m.ChargeState(), charge_source=m.ChargeSource(),
                    pd_role=m.PdRole(), p_positive_voltage_mv=m.PPositiveVoltageMv(),
                    recharge_thresh_percent=m.RechargeThreshPercent(),
                    record_counts_start=m.RecordCountsStart(), record_counts_end=m.RecordCountsEnd(),
                    smart_charge_soc_limit=m.SmartChargeSocLimit(),
                    smart_charge_enabled=m.SmartChargeEnabled())
    if stream in ("imu", "lidar-imu"):
        orientation = vector(m.Orientation(), True)
        norm = None if orientation is None else math.sqrt(sum(value * value for value in orientation))
        return dict(timestamp_ns=stamp(m.Timestamp()), frame_id=text(m.FrameId()),
                    orientation_raw_xyzw=orientation, orientation_norm=norm,
                    orientation_unit_length=norm is not None and math.isfinite(norm) and abs(norm - 1) <= 0.01,
                    angular_velocity_raw=vector(m.AngularVelocity()),
                    linear_acceleration_raw=vector(m.LinearAcceleration()),
                    orientation_covariance=[m.OrientationCovariance(i) for i in range(m.OrientationCovarianceLength())],
                    angular_velocity_covariance=[m.AngularVelocityCovariance(i) for i in range(m.AngularVelocityCovarianceLength())],
                    linear_acceleration_covariance=[m.LinearAccelerationCovariance(i) for i in range(m.LinearAccelerationCovarianceLength())])
    stride, size = m.PointStride(), m.DataLength()
    if stride == 0 or size % stride:
        raise ValueError("invalid point-cloud stride/data length")
    return dict(timestamp_ns=stamp(m.Timestamp()), frame_id=text(m.FrameId()),
                point_stride=stride, data_bytes=size, point_count=size // stride,
                fields=[dict(name=text(m.Fields(i).Name()), offset=m.Fields(i).Offset(),
                             type=m.Fields(i).Type()) for i in range(m.FieldsLength())])


def main(argv=None):
    return observe("sensors", ROUTES, summarize, argv)


if __name__ == "__main__":
    raise SystemExit(run(main))
