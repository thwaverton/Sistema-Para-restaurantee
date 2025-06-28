import cv2
import mediapipe as mp
import numpy as np

# Inicializa MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Dicionário de pedidos baseados no número de dedos
pedidos = {
    0: "Nada detectado",
    1: "Pedido: Água 💧",
    2: "Pedido: Refrigerante 🥤",
    3: "Pedido: Hambúrguer 🍔",
    4: "Pedido: Pizza 🍕",
    5: "Pedido: Conta 💸"
}

# Função para contar dedos levantados
def contar_dedos(hand_landmarks):
    dedos = []

    # Pontos das pontas dos dedos
    tips_ids = [4, 8, 12, 16, 20]

    # Polegar: eixo x
    if hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x:
        dedos.append(1)
    else:
        dedos.append(0)

    # Outros dedos: eixo y
    for i in range(1, 5):
        if hand_landmarks.landmark[tips_ids[i]].y < hand_landmarks.landmark[tips_ids[i] - 2].y:
            dedos.append(1)
        else:
            dedos.append(0)

    return sum(dedos)

# Captura da webcam
cap = cv2.VideoCapture(0)

with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Flip da imagem para espelhamento e conversão para RGB
        frame = cv2.flip(frame, 1)
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = hands.process(img_rgb)

        gesture_text = "Levante a mão e faça um gesto..."

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                dedos_levantados = contar_dedos(hand_landmarks)
                gesture_text = pedidos.get(dedos_levantados, "Gesto desconhecido")

                # Desenha os pontos da mão
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Exibe o texto do gesto
        cv2.putText(frame, gesture_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)

        cv2.imshow('Sistema de Pedidos por Gestos', frame)

        # Pressione 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
