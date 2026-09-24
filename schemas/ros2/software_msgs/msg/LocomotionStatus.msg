# Locomotion Status Message
# Published by the locomotion module on /locomotion/status

# Standard ROS2 header
std_msgs/Header header

# Posture State Constants
uint8 POSTURE_UNKNOWN = 0
uint8 POSTURE_STANDING = 1
uint8 POSTURE_LYING = 2
uint8 POSTURE_TRANSITIONING = 3

# Motion State Constants
uint8 MOTION_IDLE = 0
uint8 MOTION_RECOVERING = 1
uint8 MOTION_EMERGENCY = 2

# Status fields
uint8 posture             # Current posture of the robot (POSTURE_* constant)
uint8 motion              # Current motion state (MOTION_* constant)
string current_action     # The name of the FSM's current action (e.g., "FIXED_STAND")
string source             # Source of the status inference (e.g., "fsm", "sensor")
uint64 stamp_ns           # Timestamp in nanoseconds of the original state snapshot
