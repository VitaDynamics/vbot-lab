# BMS Battery Status - 完全匹配BatteryStatus.h结构

# System control
bool request_shutdown       # 是否请求关机

# Device information
uint8[3] protocol_version   # 协议版本 [major, minor, patch]
string vendor               # 厂商名称 (最大16字符)
uint8[3] hw_version         # 硬件版本 [major, minor, patch]
uint8[3] sw_version         # 软件版本 [major, minor, patch]
uint32 last_alarm          # 最后告警
uint32 nominal_capacity_mah # 标称容量 (mAh)
uint8 count_ntc_cell        # 电芯温度传感器数量
uint8 count_ntc_mos         # MOS温度传感器数量
uint8 count_serial          # 串联电池数量
uint16 manufacturer_year    # 制造年份
uint8 manufacturer_month    # 制造月份
uint8 manufacturer_day      # 制造日期
string serial_number        # 序列号 (最大24字符)

# Battery status
uint32 voltage_mv           # 总电压 (mV)
int32 current_ma            # 电流 (mA)，>150mA视为有效充电电流
float32 soc_percent         # 剩余电量百分比 (0-100)
float32 soh_percent         # 健康状态百分比 (0-100)
uint32 remaining_capacity_mah # 剩余容量 (mAh)

# MOS switch status
uint8 mos_charge_is_open    # 充电MOS开关状态
uint8 mos_discharge_is_open # 放电MOS开关状态
uint8 mos_xt30_is_open      # XT30 MOS开关状态
uint8 mos_pre_discharge_is_open # 预放电MOS开关状态

# Alarm information
uint32 alarm                # 32位异常报警bitmask
uint32 vendor_alarm         # 厂商告警

# Temperature and voltage arrays
float32[16] temperatures_c  # 温度数据 (摄氏度)
uint16[16] voltages_single_mv # 单体电压 (mV)

# Cycle and capacity
uint16 cycles               # 充放电循环次数
uint32 full_charge_capacity_mah # 满充容量 (mAh)

# Charging information
uint8 CHARGE_STATE_UNKNOWN=0
uint8 CHARGE_STATE_IDLE=1
uint8 CHARGE_STATE_CHARGING=2
uint8 CHARGE_STATE_FULL=3

uint32 charging_voltage_xt30_charger_mv # XT30充电器电压 (mV)
uint32 charging_voltage_xt30_bus_mv     # XT30总线电压 (mV)
uint32 equilibrium_state    # 均衡状态
bool is_charger_connected   # 是否连接充电器
uint8 charge_state          # 统一充电状态：0=UNKNOWN, 1=IDLE, 2=CHARGING, 3=FULL

# ADC sampling data
int32 adc_global_current    # ADC全局电流
int32 adc_battery_voltage   # ADC电池电压
int32 adc_motor_voltage     # ADC电机电压
int32 adc_motor_current_1   # ADC电机电流1
int32 adc_motor_current_2   # ADC电机电流2
int32 adc_motor_current_3   # ADC电机电流3
int32 adc_motor_current_4   # ADC电机电流4
int32 adc_back_24v_voltage  # ADC后24V电压
int32 adc_head_24v_voltage  # ADC前24V电压
