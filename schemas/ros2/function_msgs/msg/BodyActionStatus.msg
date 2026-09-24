# BodyActionStatus.msg
# Module-specific status for body action functionality

# Status constants - encapsulated in message
uint8 STATUS_IDLE = 0
uint8 STATUS_RUNNING = 1

# Current execution status
uint8 status

uint8 MODE_PASSIVE=0
uint8 MODE_FIXED_STAND=1
uint8 MODE_FIXED_LAYDOWN=2
uint8 MODE_SAFE_STOP_SEQUENCE=3
uint8 MODE_SAFE_LAYDOWN_SEQUENCE=4  

# RL
uint8 MODE_RL=5
uint8 MODE_RL_TROT=6

# MPC
uint8 MODE_MPC = 7

# STREAM
uint8 MODE_STREAM = 8

# RL Pilot / Recovery
uint8 MODE_RL_PILOT = 9
uint8 MODE_RL_RECOVERY = 10

uint8 MODE_LAYDOWN = 11
uint8 MODE_EXTERNAL = 12
uint8 MODE_OPENTRACK = 13
uint8 MODE_RECOVERY_ACTION = 14
uint8 MODE_DAMPER = 15

uint8 MODE_RL_ACTION_POLICY1 = 100
uint8 MODE_RL_ACTION_POLICY2 = 101
uint8 MODE_RL_ACTION_POLICY3 = 102
uint8 MODE_HIMLOCO_ACTION = 103


# Current execution mode (numeric for backward compatibility)
uint8 mode

# Current execution mode (string for modern usage)
string mode_str

# Source that last modified this status
string modify_source

