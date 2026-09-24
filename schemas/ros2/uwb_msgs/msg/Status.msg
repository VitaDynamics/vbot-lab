

uint8 STATE_IDLE = 0
uint8 STATE_CONNECTED = 1
uint8 STATE_RANGING = 2

uint8 state

uint8 MODE_BLE = 0
uint8 MODE_ANCHOR = 1

uint8 mode

uint8 battery_percentage
uint8 preamble_code

# MAC address in bytes, e.g., [0xE2, 0x22, 0xF2, 0x80, 0x18, 0x40]
uint8[6] tag_mac_addr

int16 rssi_dbm
float32 angle_offset
bool is_charging
