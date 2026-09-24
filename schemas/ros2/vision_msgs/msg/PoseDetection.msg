# Complete pose detection result for a single person
std_msgs/Header header

# Detection metadata
int32 class_id        # Object class ID (0 for person)
float32 score         # Detection confidence score
geometry_msgs/Point32 bbox_min  # Bounding box minimum point (x1, y1)
geometry_msgs/Point32 bbox_max  # Bounding box maximum point (x2, y2)

# Pose keypoints (17 points in COCO format)
vision_msgs/PoseKeypoint[17] keypoints

# Keypoint indices:
# 0: nose, 1: left eye, 2: right eye, 3: left ear, 4: right ear
# 5: left shoulder, 6: right shoulder, 7: left elbow, 8: right elbow
# 9: left wrist, 10: right wrist, 11: left hip, 12: right hip
# 13: left knee, 14: right knee, 15: left ankle, 16: right ankle