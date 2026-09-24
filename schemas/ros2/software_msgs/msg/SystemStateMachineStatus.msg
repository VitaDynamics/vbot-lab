# 系统状态机统一状态消息（简化且语义清晰）

# 标准ROS2消息头
std_msgs/Header header

# 分类（明确消息语义）
uint8 CATEGORY_STATE = 0   # 状态机当前状态/切换
uint8 CATEGORY_OTA = 1     # OTA阶段与结果
uint8 CATEGORY_ALERT = 2   # 告警/用户提示/Guard失败

uint8 category

# 状态进展（标准化状态流转语义）
uint8 STATUS_UNKNOWN = 0
uint8 STATUS_STARTED = 1
uint8 STATUS_RUNNING = 2
uint8 STATUS_SUCCESS = 3
uint8 STATUS_FAILED = 4
uint8 STATUS_CANCELLED = 5

uint8 status

# 状态机状态（数值+名称，外部可直接消费）
uint16 state_id
string state_name

# 当前激活状态链（从根状态到当前叶子状态）
uint16[] active_state_path_ids
string[] active_state_path_names

# 人类可读消息（简短清晰）
string message

# 结构化附加数据（替代JSON）
software_msgs/KeyValue[] data

# 严重性
uint8 SEVERITY_INFO = 0
uint8 SEVERITY_WARNING = 1
uint8 SEVERITY_ERROR = 2
uint8 SEVERITY_CRITICAL = 3

uint8 severity

# 是否为当前有效的状态
bool is_active
