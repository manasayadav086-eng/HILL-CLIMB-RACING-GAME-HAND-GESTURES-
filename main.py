import cv2
import mediapipe as mp
import time
from pathlib import Path
from urllib.request import urlopen

from directkeys import PressKey, ReleaseKey, left_pressed, right_pressed


MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = Path(__file__).with_name("hand_landmarker.task")
HAND_CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)
FINGER_TIPS = (8, 12, 16, 20)
FINGER_PIPS = (6, 10, 14, 18)


def ensure_model():
    if MODEL_PATH.exists():
        return

    print("Downloading MediaPipe hand model...")
    with urlopen(MODEL_URL, timeout=30) as response:
        MODEL_PATH.write_bytes(response.read())


def draw_hand(image, landmarks):
    height, width = image.shape[:2]
    points = []
    for landmark in landmarks:
        point = (int(landmark.x * width), int(landmark.y * height))
        points.append(point)
        cv2.circle(image, point, 6, (0, 255, 0), cv2.FILLED)

    for start, end in HAND_CONNECTIONS:
        cv2.line(image, points[start], points[end], (255, 0, 0), 3)


def count_extended_fingers(landmarks):
    return sum(
        landmarks[tip].y < landmarks[pip].y
        for tip, pip in zip(FINGER_TIPS, FINGER_PIPS)
    )


def release_keys(pressed_keys):
    for key in pressed_keys:
        ReleaseKey(key)
    pressed_keys.clear()


def main():
    ensure_model()
    time.sleep(2)
    hand_options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.3,
        min_hand_presence_confidence=0.3,
        min_tracking_confidence=0.25,
    )
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not camera.isOpened():
        raise RuntimeError("Unable to open the webcam.")
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Frame", 320, 240)
    cv2.moveWindow("Frame", 10, 10)
    cv2.setWindowProperty("Frame", cv2.WND_PROP_TOPMOST, 1)

    pressed_keys = set()
    last_status = None
    frame_timestamp_ms = 0
    candidate_status = "NO HAND"
    candidate_count = 0
    stable_status = "NO HAND"
    try:
        with mp.tasks.vision.HandLandmarker.create_from_options(hand_options) as landmarker:
            while True:
                success, frame = camera.read()
                if not success:
                    print("Unable to read a frame from the webcam.")
                    break

                frame = cv2.flip(frame, 1)
                frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=5)
                detection_frame = cv2.resize(frame, None, fx=1.5, fy=1.5)
                rgb_frame = cv2.cvtColor(detection_frame, cv2.COLOR_BGR2RGB)
                frame_timestamp_ms += 33
                result = landmarker.detect_for_video(
                    mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame),
                    frame_timestamp_ms,
                )
                detected_keys = set()
                status = "NO HAND"
                status_color = (0, 0, 255)

                if result.hand_landmarks:
                    landmarks = result.hand_landmarks[0]
                    draw_hand(frame, landmarks)
                    extended_fingers = count_extended_fingers(landmarks)
                    if extended_fingers <= 1:
                        status = "BRAKE"
                        detected_keys.add(left_pressed)
                    elif extended_fingers >= 3:
                        status = "GAS"
                        detected_keys.add(right_pressed)
                    else:
                        status = "HAND DETECTED"
                    status_color = (0, 255, 0)
                else:
                    height, width = frame.shape[:2]
                    cv2.rectangle(
                        frame, (width // 4, height // 5),
                        (width * 3 // 4, height * 4 // 5), (0, 255, 255), 2
                    )
                    cv2.putText(
                        frame, "PLACE HAND INSIDE BOX", (width // 4, height - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2,
                        cv2.LINE_AA
                    )

                if status == candidate_status:
                    candidate_count += 1
                else:
                    candidate_status = status
                    candidate_count = 1
                if candidate_count >= 3:
                    stable_status = candidate_status
                status = stable_status
                detected_keys = set()
                if status == "BRAKE":
                    detected_keys.add(left_pressed)
                elif status == "GAS":
                    detected_keys.add(right_pressed)

                for key in pressed_keys - detected_keys:
                    ReleaseKey(key)
                for key in detected_keys - pressed_keys:
                    PressKey(key)
                pressed_keys = detected_keys

                if status != last_status:
                    print(f"Gesture: {status}", flush=True)
                    last_status = status

                cv2.putText(
                    frame, status, (20, 45), cv2.FONT_HERSHEY_SIMPLEX,
                    1, status_color, 2, cv2.LINE_AA
                )
                if status in ("BRAKE", "GAS"):
                    cv2.rectangle(frame, (20, 70), (260, 140), (0, 180, 0), cv2.FILLED)
                    cv2.putText(
                        frame, status, (40, 120), cv2.FONT_HERSHEY_SIMPLEX,
                        1.5, (255, 255, 255), 3, cv2.LINE_AA
                    )
                cv2.imshow("Frame", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        release_keys(pressed_keys)
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

