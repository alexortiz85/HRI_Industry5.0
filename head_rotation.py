import cv2
import mediapipe as mp
import numpy as np
import math

# Inicializar MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

# Puntos clave del rostro (índices)
LANDMARKS = {
    "nose_tip": 1,
    "chin": 152,
    "left_eye_corner": 33,
    "right_eye_corner": 263,
    "left_mouth_corner": 61,
    "right_mouth_corner": 291
}

# Coordenadas 3D del modelo (aproximadas en mm)
model_points = np.array([
    [0.0, 0.0, 0.0],         # Nose tip
    [0.0, -63.6, -12.5],     # Chin
    [-43.3, 32.7, -26.0],    # Left eye corner
    [43.3, 32.7, -26.0],     # Right eye corner
    [-28.9, -28.9, -24.1],   # Left mouth corner
    [28.9, -28.9, -24.1]     # Right mouth corner
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

    dist_coeffs = np.zeros((4, 1))  # Asumimos sin distorsión

    success, rotation_vector, translation_vector = cv2.solvePnP(
        model_points, image_points, camera_matrix, dist_coeffs)

    rmat, _ = cv2.Rodrigues(rotation_vector)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

    pitch, yaw, roll = angles  # En grados
    return pitch, yaw, roll

# Iniciar cámara
cap = cv2.VideoCapture(0)

print("Presiona 'q' para salir")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:
        face_landmarks = results.multi_face_landmarks[0]
        landmarks = [(int(p.x * frame.shape[1]), int(p.y * frame.shape[0])) for p in face_landmarks.landmark]

        try:
            pitch, yaw, roll = get_head_pose(frame, landmarks)

            text = f"Pitch: {pitch:.1f}°, Yaw: {yaw:.1f}°, Roll: {roll:.1f}°"
            cv2.putText(frame, text, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # Detectar si mira al frente (tolerancia ±10 grados)
            if abs(yaw) < 20:
                estado = "Viendo al frente"
            else:
                estado = "Inclinacion detectada"

            cv2.putText(frame, estado, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        except Exception as e:
            print(f"Error de pose: {e}")

    cv2.imshow("Head Pose Estimation", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
