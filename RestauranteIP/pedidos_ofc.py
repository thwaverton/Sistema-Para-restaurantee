# tem que levantar o braço 
import cv2
import mediapipe as mp
import numpy as np
import sqlite3
from datetime import datetime

# Banco de dados
conn = sqlite3.connect("pedidos.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item TEXT,
        horario TEXT
    )
""")
conn.commit()

# Cardápio
menu = {
    1: "Água 💧",
    2: "Refrigerante 🥤",
    3: "Hambúrguer 🍔",
    4: "Pizza 🍕",
    5: "Conta 💸"
}

# MediaPipe
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

pose = mp_pose.Pose(min_detection_confidence=0.5)
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)

# Contador de dedos com correção de mão
def contar_dedos(hand_landmarks, hand_label):
    dedos = []
    tips_ids = [4, 8, 12, 16, 20]

    # Polegar
    if hand_label == "Right":
        if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
            dedos.append(1)
        else:
            dedos.append(0)
    else:
        if hand_landmarks.landmark[tips_ids[0]].x > hand_landmarks.landmark[tips_ids[0] - 1].x:
            dedos.append(1)
        else:
            dedos.append(0)

    # Outros dedos
    for i in range(1, 5):
        if hand_landmarks.landmark[tips_ids[i]].y < hand_landmarks.landmark[tips_ids[i] - 2].y:
            dedos.append(1)
        else:
            dedos.append(0)

    return sum(dedos)

# Verifica se o braço direito está levantado
def braco_direito_levantado(landmarks):
    ombro = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    cotovelo = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
    punho = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
    return punho.y < ombro.y and cotovelo.y < ombro.y

# Webcam
cap = cv2.VideoCapture(0)
ultimo_pedido = None
contador_confirmacao = 0
confirmacao_frames = 30  # nº de frames para confirmar o gesto

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    pose_results = pose.process(rgb)
    hand_results = hands.process(rgb)

    texto = "Levante o braço direito para fazer um pedido..."

    if pose_results.pose_landmarks:
        landmarks = pose_results.pose_landmarks.landmark
        if braco_direito_levantado(landmarks):
            texto = "Braço levantado! Faça um gesto com a mão..."

            if hand_results.multi_hand_landmarks:
                for idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                    handedness = hand_results.multi_handedness[idx].classification[0].label
                    dedos = contar_dedos(hand_landmarks, handedness)
                    pedido = menu.get(dedos)

                    if pedido:
                        if ultimo_pedido == pedido:
                            contador_confirmacao += 1
                        else:
                            contador_confirmacao = 1
                            ultimo_pedido = pedido

                        if contador_confirmacao >= confirmacao_frames:
                            texto = f"{pedido} confirmado!"
                            # Salvar no banco
                            cursor.execute("INSERT INTO pedidos (item, horario) VALUES (?, ?)",
                                           (pedido, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit()
                            contador_confirmacao = 0
                            ultimo_pedido = None
                    else:
                        texto = "Gesto não reconhecido."

                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Desenha esqueleto
    if pose_results.pose_landmarks:
        mp_drawing.draw_landmarks(frame, pose_results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    cv2.putText(frame, texto, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow("Sistema de Pedidos por Gestos", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
conn.close()
cv2.destroyAllWindows()
