uint16 servo_id
string joint_name
float32 joint_target_angle    # 目标角度（度）- 来自最后一次命令
float32 joint_current_angle   # 当前角度（度）- 来自最新状态反馈

# 0x400 硬件状态 (RPDO3协议)
bool hw_is_valid
bool hw_voltage_fault      # bit0: 电压保护（统一低/高电压）
bool hw_current_fault      # bit1: 电流保护
bool hw_temp_fault         # bit2: 温度保护
bool hw_stall_fault        # bit3: 堵转保护
bool hw_hardware_fault     # bit4: 硬件异常保护
bool hw_position_protection_fault          # bit5: 位置保护
bool hw_thermal_integral_protection_fault  # bit6: 热积分保护
float32 hw_voltage_v       # Byte2-3: 当前电压 (int16, 分辨率0.001, 单位V)
float32 hw_temperature_c   # Byte4-5: 当前温度 (int16, 分辨率0.1, 单位°C)
float32 hw_current_ma      # Byte6-7: 当前电流 (int16, 分辨率1, 单位mA)

# 0x300 热积分状态（仅透传）
bool thermal_integral_is_valid
uint16 thermal_integral_error_bits
uint8 thermal_integral_reserved_bits
uint8 thermal_integral_servo_state
int32 thermal_integral_current_1_ma
int32 thermal_integral_current_2_ma

# 0x500 运动状态
bool motion_is_valid
float32 motion_position
float32 motion_speed_dps
float32 motion_torque
uint16 motion_run_times_cnt
