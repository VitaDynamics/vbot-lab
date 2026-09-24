# StereoTagDetection.msg
# 双目AprilTag检测结果 - 由X5端检测后发布到S100端进行PnP解算和控制
# 每帧包含左右相机的检测结果和相机内参，S100端不再订阅原始图像

std_msgs/Header header

# 左相机检测结果
bool left_valid                    # 左相机是否检测到目标Tag
int32 left_tag_id                  # 左相机检测到的Tag ID
float64 left_decision_margin       # 左相机检测置信度
float64[8] left_corners            # 左相机Tag四角像素坐标 [x0,y0, x1,y1, x2,y2, x3,y3]

# 右相机检测结果
bool right_valid                   # 右相机是否检测到目标Tag
int32 right_tag_id                 # 右相机检测到的Tag ID
float64 right_decision_margin      # 右相机检测置信度
float64[8] right_corners           # 右相机Tag四角像素坐标 [x0,y0, x1,y1, x2,y2, x3,y3]

# 左相机内参 (从CameraInfo提取)
float64[9] left_k                  # 3x3相机矩阵 [fx,0,cx, 0,fy,cy, 0,0,1]
float64[] left_d                   # 畸变系数
string left_frame_id               # 左相机TF frame ID

# 右相机内参 (从CameraInfo提取)
float64[9] right_k                 # 3x3相机矩阵
float64[] right_d                  # 畸变系数
string right_frame_id              # 右相机TF frame ID
