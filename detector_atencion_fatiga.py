
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
import keyboard

# MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

LANDMARKS = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_corner": 33,
    "right_eye_corner": 263,
    "left_mouth_corner": 61,
    "right_mouth_corner": 291,
    "left_eye": [159, 145],
    "right_eye": [386, 374],
}

model_points = np.array([
    [0.0, 0.0, 0.0],
    [0.0, -63.6, -12.5],
    [-43.3, 32.7, -26.0],
    [43.3, 32.7, -26.0],
    [-28.9, -28.9, -24.1],
    [28.9, -28.9, -24.1]
], dtype=np.float64)

def get_head_pose(image, landmarks):
    image_points = np.array([
        landmarks[LANDMARKS["nose_tip"]],
        landmarks[LANDMARKS["chin"]],
        landmarks[LANDMARKS["left_eye_corner"]],
        landmarks[LANDMARKS["right_eye_corner"]],
        landmarks[LANDMARKS["left_mouth_corner"]],
        landmarks[LANDMARKS["right_mouth_corner"]],
    ], dtype=np.float64)

    height, width = image.shape[:2]
    focal_length = width
    center = (width / 2, height / 2)
    camera_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1))
    success, rotation_vector, _ = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs)
    rmat, _ = cv2.Rodrigues(rotation_vector)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
    pitch, yaw, roll = angles
    return pitch, yaw, roll

def compute_ear(eye_landmarks):
    A = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[1]))
    C = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[1]))
    return A / (2.0 * C) if C != 0 else 0

def crear_archivo_csv():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"attention_fatigue_{timestamp}.csv"
    ruta = Path.cwd() / nombre
    df = pd.DataFrame(columns=["timestamp", "datetime", "yaw", "pitch", "roll", "ear", "attention", "fatigue"])
    df.to_csv(ruta, index=False)
    return ruta, timestamp

def guardar_csv(ruta, ts_unix, ts_human, yaw, pitch, roll, ear, attention, fatigue):
    fila = pd.DataFrame([[ts_unix, ts_human, yaw, pitch, roll, ear, attention, fatigue]],
                        columns=["timestamp", "datetime", "yaw", "pitch", "roll", "ear", "attention", "fatigue"])
    fila.to_csv(ruta, mode='a', header=False, index=False)

cap = cv2.VideoCapture(0)
print("Presiona 's' para iniciar guardado, 'q' para detener y salir.")

saving = False
csv_path = None
start_time = None
timestamp = None

total_frames = 0
attention_frames = 0
fatigue_frames = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0]
        h, w = frame.shape[:2]
        coords = [(int(p.x * w), int(p.y * h)) for p in landmarks.landmark]

        try:
            pitch, yaw, roll = get_head_pose(frame, coords)
            left_eye = [coords[i] for i in LANDMARKS["left_eye"]]
            right_eye = [coords[i] for i in LANDMARKS["right_eye"]]
            ear_left = compute_ear(left_eye)
            ear_right = compute_ear(right_eye)
            ear = (ear_left + ear_right) / 2.0

            attention = abs(yaw) < 15 # and abs(pitch) < 15
            fatigue = pitch < -15 or ear < 0.23

            ts_unix = time.time()
            ts_human = datetime.now().isoformat(sep=' ', timespec='milliseconds')

            if saving:
                if start_time is None:
                    start_time = time.time()
                total_frames += 1
                if attention:
                    attention_frames += 1
                if fatigue:
                    fatigue_frames += 1
                guardar_csv(csv_path, ts_unix, ts_human, yaw, pitch, roll, ear, attention, fatigue)

                elapsed = time.time() - start_time
                attn_pct = (attention_frames / total_frames) * 100
                fatigue_pct = (fatigue_frames / total_frames) * 100
                cv2.putText(frame, f"Attn: {attn_pct:.1f}%, Fatigue: {fatigue_pct:.1f}%, Time: {elapsed:.1f}s",
                            (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 255, 180), 2)

            cv2.putText(frame, f"Yaw: {yaw:.1f}°, Pitch: {pitch:.1f}°, Roll: {roll:.1f}°", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if attention else (0, 0, 255), 2)
            cv2.putText(frame, f"EAR: {ear:.2f} | Fatigue: {fatigue}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0) if fatigue else (200, 255, 200), 2)

        except Exception as e:
            print("Error en orientación/parpadeo:", e)

    if keyboard.is_pressed('s') and not saving:
        csv_path, timestamp = crear_archivo_csv()
        saving = True
        print("🟢 Guardando activado.")

    if keyboard.is_pressed('q') and saving:
        print("🔴 Guardando detenido. Generando resumen...")
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        attn_pct = (attention_frames / total_frames) * 100 if total_frames > 0 else 0
        fatigue_pct = (fatigue_frames / total_frames) * 100 if total_frames > 0 else 0

        summary_df = pd.DataFrame([[
            elapsed_seconds, total_frames, attention_frames, fatigue_frames,
            round(attn_pct, 2), round(fatigue_pct, 2)
        ]], columns=[
            "total_time_s", "total_frames", "attention_frames", "fatigue_frames",
            "attention_pct", "fatigue_pct"
        ])
        summary_path = Path.cwd() / f"summary_attention_fatigue_{timestamp}.csv"
        summary_df.to_csv(summary_path, index=False)
        break

    cv2.imshow("Atención y Fatiga", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
