# 基本元信息（非版本字段保持类型便于过滤）
firmware_version_msgs/DeviceType device_type
uint16 device_id
string name
string vendor
string sn

# 版本字符串；可留空
string sw_version
string hw_version
string protocol_version
string sdk_version
string build_meta
string commit

# 厂商/设备自定义扩展；等长并行数组
string[] extra_keys
string[] extra_values
