import logging
import math

import cv2
import mediapipe as mp
from celery import Celery

from config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, SERVICE_VIDEO_POSES_QUEUE, SERVICE_VIDEO_POSES

celery_worker = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

celery_worker.conf.task_routes = {f"worker.*": {"queue": SERVICE_VIDEO_POSES_QUEUE}, }

# Set up logging
logging.basicConfig(level=logging.INFO)

@celery_worker.task(name=f"worker.{SERVICE_VIDEO_POSES}", bind=True)
def service_video_poses(self, compressed_video_data):
    """
    Analyzes poses in the video and returns statistics.

    :param compressed_video_data: Either the dict output from the compression task or a file path.
    :return: A dictionary with "status" and "result", where result is a dict containing:
             "closed_pose_percentage" and "open_pose_percentage".
    """
    try:
        # Extract file path from dict if necessary.
        if isinstance(compressed_video_data, dict):
            compressed_video_path = compressed_video_data.get("result")
        else:
            compressed_video_path = compressed_video_data

        # Assume calculate_angle is defined elsewhere and imported.
        ARM_ANGLE_THRESHOLD = 15  # Angle threshold in degrees.

        cap = cv2.VideoCapture(compressed_video_path)
        total_frames = 0
        closed_pose_frames = 0
        open_pose_frames = 0
        frame_counter = 0  # Process every 5th frame.

        with mp.solutions.pose.Pose(
                static_image_mode=False,
                model_complexity=0,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
        ) as pose:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_counter += 1
                if frame_counter % 5 != 0:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = pose.process(frame_rgb)

                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark

                    left_wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST]
                    right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]
                    left_hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]
                    right_hip = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_HIP]
                    left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
                    right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]

                    left_arm_vector = [
                        left_wrist.x - left_shoulder.x,
                        left_wrist.y - left_shoulder.y
                    ]
                    left_torso_vector = [
                        left_hip.x - left_shoulder.x,
                        left_hip.y - left_shoulder.y
                    ]
                    right_arm_vector = [
                        right_wrist.x - right_shoulder.x,
                        right_wrist.y - right_shoulder.y
                    ]
                    right_torso_vector = [
                        right_hip.x - right_shoulder.x,
                        right_hip.y - right_shoulder.y
                    ]

                    left_arm_angle = calculate_angle(left_arm_vector, left_torso_vector)
                    right_arm_angle = calculate_angle(right_arm_vector, right_torso_vector)

                    if left_arm_angle < ARM_ANGLE_THRESHOLD and right_arm_angle < ARM_ANGLE_THRESHOLD:
                        closed_pose_frames += 1
                    else:
                        open_pose_frames += 1

                total_frames += 1

        cap.release()

        if total_frames == 0:
            raise ValueError("No frames processed from the video.")

        closed_percentage = closed_pose_frames / total_frames * 100
        open_percentage = open_pose_frames / total_frames * 100

        result_dict = {
            "closed_pose_percentage": closed_percentage,
            "open_pose_percentage": open_percentage
        }
        return {"status": "SUCCESS", "result": result_dict}

    except Exception as e:
        import logging
        logging.error(f"Error in service_video_poses: {e}")
        try:
            service_video_poses.retry(countdown=2)
        except Exception as retry_ex:
            logging.error(f"Max retries exceeded in service_video_poses: {retry_ex}")
            return {"status": "FAIL", "result": "N/A", "error": str(e)}


def calculate_angle(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude_v1 = math.sqrt(sum(a ** 2 for a in v1))
    magnitude_v2 = math.sqrt(sum(a ** 2 for a in v2))
    cos_theta = dot_product / (magnitude_v1 * magnitude_v2)
    angle = math.degrees(math.acos(cos_theta))
    return angle
