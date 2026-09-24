std_msgs/Header header

# 系统运行模式
uint8 MODE_UNKNOWN=0      # 未知/未初始化
uint8 MODE_ODOMETRY=1     # 纯里程计模式(不用地图)
uint8 MODE_MAPPING=2      # 建图模式(含定位)
uint8 MODE_LOCALIZATION=3 # 纯定位模式(基于地图)
uint8 operation_mode      # 当前运行模式

# 定位状态
uint8 LOC_STATUS_UNKNOWN=0     # 未知/未初始化
uint8 LOC_STATUS_INIT=1        # 正在初始化
uint8 LOC_STATUS_WAITING=2     # 等待定位
uint8 LOC_STATUS_TRACKING=3    # 跟踪正常
uint8 LOC_STATUS_LOST=4        # 跟踪丢失
uint8 LOC_STATUS_RELOC=5       # 重定位中
uint8 LOC_STATUS_RELOC_FAILED=6 # 重定位超时/失败
uint8 loc_status               # 当前定位状态

# 里程计状态
uint8 ODOM_STATUS_UNKNOWN=0    # 未知/未初始化
uint8 ODOM_STATUS_INIT=1       # 初始化中
uint8 ODOM_STATUS_TRACKING=2   # 正常输出
uint8 ODOM_STATUS_DEGRADED=3   # 降级输出，质量变差但仍可用
uint8 ODOM_STATUS_LOST=4       # 跟踪失败/不可用
uint8 ODOM_STATUS_RESETTING=5  # 已触发 reset，等待重新产出有效 odom
uint8 odom_status              # 当前里程计状态
uint32 odom_status_seq         # reset/恢复等里程计关键边沿序号

# 本地地图状态
uint8 MAP_STATUS_IDLE=0        # 无地图/无有效地图任务
uint8 MAP_STATUS_MAPPING=1     # 正在建图
uint8 MAP_STATUS_LOOP=2        # 回环检测/优化中
uint8 MAP_STATUS_SAVING=3      # 本地地图保存中
uint8 MAP_STATUS_READY=4       # 本地地图可用，已保存或已加载
uint8 MAP_STATUS_SAVE_FAILED=5 # 本地地图保存失败
uint8 map_status               # 当前本地地图状态

# 地图云端回传状态，地图包和mcap任意一个未完成都视为回传中
uint8 CLOUD_SYNC_IDLE=0        # 无回传任务
uint8 CLOUD_SYNC_UPLOADING=1   # 地图包或mcap回传中
uint8 CLOUD_SYNC_DONE=2        # 地图包和mcap均回传完成
uint8 CLOUD_SYNC_FAILED=3      # 地图包或mcap任意一个回传失败
uint8 cloud_sync_status        # 当前地图云端回传状态
string cloud_sync_map_name     # 当前/最近一次回传对应的地图名

# 运行时信息
float32 tracking_quality     # 跟踪质量 [0,1]
string context               # 状态描述/错误信息
uint32 map_id                # 当前地图ID
float32 mileage              # 本次上电周期里程
float32 accumulated_mileage  # 累积总里程（含历史）
string current_map_name      # 当前加载或最近保存成功的地图名

# 统计信息
uint32 num_keyframes       # 关键帧数量
uint32 num_landmarks       # 路标点数量
float32 process_time       # 处理耗时(ms)
float32 cpu_usage          # CPU使用率(%)
float32 mem_usage          # 内存使用(MB)

# GPS 融合状态
uint8 GPS_ALIGN_DISABLED=0    # GPS 融合未启用
uint8 GPS_ALIGN_ALIGNING=1    # GPS 融合启用但未对齐
uint8 GPS_ALIGN_ALIGNED=2     # GPS 融合启用且已对齐
uint8 gps_align_status        # GPS 对齐状态