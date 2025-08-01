import cv2
import mediapipe as mp
import numpy as np
import math

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Utilidad para calcular ángulo entre 3 puntos (en grados)
def calculate_angle(p1, p2, p3):
    v1 = np.array([p1.x - p2.x, p1.y - p2.y, p1.z - p2.z])
    v2 = np.array([p3.x - p2.x, p3.y - p2.y, p3.z - p2.z])
    angle_rad = math.atan2(np.linalg.norm(np.cross(v1, v2)), np.dot(v1, v2))
    return np.degrees(angle_rad)

# Función para obtener Pitch, Roll, Yaw de la mano
def hand_orientation(landmarks):
    # Tomamos landmarks clave: Wrist(0), Index MCP(5), Pinky MCP(17), Middle MCP(9)
    wrist = landmarks[0]
    index_mcp = landmarks[5]
    pinky_mcp = landmarks[17]
    middle_mcp = landmarks[9]

    # Vector base de la mano (del wrist al middle_mcp)
    hand_vector = np.array([middle_mcp.x - wrist.x, middle_mcp.y - wrist.y, middle_mcp.z - wrist.z])

    # Vector lateral (index_mcp a pinky_mcp)
    lateral_vector = np.array([pinky_mcp.x - index_mcp.x, pinky_mcp.y - index_mcp.y, pinky_mcp.z - index_mcp.z])

    # Normal de la palma (producto cruz)
    normal_vector = np.cross(hand_vector, lateral_vector)

    # Normalizamos los vectores
    normal_vector /= np.linalg.norm(normal_vector)
    hand_vector /= np.linalg.norm(hand_vector)
    lateral_vector /= np.linalg.norm(lateral_vector)

    # Cálculo de Pitch, Roll, Yaw
    pitch = math.asin(-normal_vector[1])  # Rotación sobre eje X
    roll = math.atan2(normal_vector[0], normal_vector[2])  # Rotación sobre eje Z
    yaw = math.atan2(lateral_vector[1], lateral_vector[0])  # Giro lateral (eje Y)

    return np.degrees(pitch), np.degrees(roll), np.degrees(yaw)

# Inicializamos cámara y MediaPipe Hands
cap = cv2.VideoCapture(0)
with mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.7) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                pitch, roll, yaw = hand_orientation(hand_landmarks.landmark)

                # Dibujar Landmarks
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Mostrar valores en pantalla
                label = f"{handedness.classification[0].label} Hand"
                cv2.putText(frame, f"{label} Pitch: {pitch:.1f} Roll: {roll:.1f} Yaw: {yaw:.1f}",
                            (10, 30 if handedness.classification[0].label == 'Left' else 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('Hand Orientation - MediaPipe', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
