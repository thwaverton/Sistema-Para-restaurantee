import cv2
import mediapipe as mp
import numpy as np
import sqlite3
from datetime import datetime
import face_recognition
import os
import time
import uuid

# Banco de dados
conn = sqlite3.connect("pedidos.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pessoa_id TEXT,
        item TEXT,
        horario TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS pessoas (
        id TEXT PRIMARY KEY,
        nome TEXT,
        encoding TEXT
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

# Diretório para armazenar fotos de rostos
ROSTOS_DIR = "rostos"
os.makedirs(ROSTOS_DIR, exist_ok=True)

# Lista de rostos cadastrados
rostos_cadastrados = []
nomes_cadastrados = []

# Função para registrar a face no banco de dados
def registrar_face(nome, face_encoding):
    pessoa_id = str(uuid.uuid4())  # Gerar um ID único para cada pessoa
    cursor.execute("INSERT INTO pessoas (id, nome, encoding) VALUES (?, ?, ?)",
                   (pessoa_id, nome, face_encoding.tobytes()))
    conn.commit()
    rostos_cadastrados.append(face_encoding)
    nomes_cadastrados.append(nome)
    return pessoa_id

# Função para verificar se a pessoa já foi cadastrada
def verificar_pessoa(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, faces)

    for encoding, face in zip(encodings, faces):
        matches = face_recognition.compare_faces(rostos_cadastrados, encoding)
        if True in matches:
            first_match_index = matches.index(True)
            pessoa_id = nomes_cadastrados[first_match_index]
            cv2.rectangle(frame, (face[3], face[0]), (face[1], face[2]), (0, 255, 0), 2)
            cv2.putText(frame, f"Pessoa: {pessoa_id}", (face[3], face[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            return pessoa_id, face
    return None, None

# Função para capturar as duas fotos de uma pessoa
def capturar_fotos_para_cadastro(nome, pessoa_id):
    print("Capturando fotos...")
    for i in range(2):  # Tirar 2 fotos
        foto_path = os.path.join(ROSTOS_DIR, f"{pessoa_id}_{i+1}.jpg")
        ret, frame = cap.read()
        if not ret:
            break

        # Captura a face
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, faces)

        if encodings:
            # Usar o primeiro rosto detectado para o registro
            cv2.imwrite(foto_path, frame)  # Salvar foto
            print(f"Foto {i+1} capturada e salva em {foto_path}")

# Função para registrar uma nova pessoa
def registrar_nova_pessoa(frame):
    nome = "Pessoa_" + str(uuid.uuid4())  # Gerar um nome único
    print("Novo rosto detectado! Cadastrando nova pessoa...")
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, faces)

    if encodings:
        # Usar o primeiro rosto detectado para o registro
        encoding = encodings[0]
        pessoa_id = registrar_face(nome, encoding)
        capturar_fotos_para_cadastro(nome, pessoa_id)
        return pessoa_id
    return None

# Contador de dedos
def contar_dedos(hand_landmarks, hand_label):
    dedos = []
    tips_ids = [4, 8, 12, 16, 20]
    if hand_label == "Right":
        dedos.append(int(hand_landmarks.landmark[tips_ids[0]].x < hand_landmarks.landmark[tips_ids[0] - 1].x))
    else:
        dedos.append(int(hand_landmarks.landmark[tips_ids[0]].x > hand_landmarks.landmark[tips_ids[0] - 1].x))
    for i in range(1, 5):
        dedos.append(int(hand_landmarks.landmark[tips_ids[i]].y < hand_landmarks.landmark[tips_ids[i] - 2].y))
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
confirmacao_frames = 30
pessoa_id_atual = None
ultimo_tempo_pessoa = time.time()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Verificar e registrar nova pessoa se necessário
    pessoa_id, face = verificar_pessoa(frame)
    if not pessoa_id:
        pessoa_id = registrar_nova_pessoa(frame)
        if pessoa_id:
            pessoa_id_atual = pessoa_id

    # Expira ID após 1 hora de inatividade
    if pessoa_id_atual and time.time() - ultimo_tempo_pessoa > 3600:
        pessoa_id_atual = None

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

                    if pedido and pessoa_id_atual:
                        if ultimo_pedido == pedido:
                            contador_confirmacao += 1
                        else:
                            contador_confirmacao = 1
                            ultimo_pedido = pedido

                        if contador_confirmacao >= confirmacao_frames:
                            texto = f"{pedido} confirmado!"
                            cursor.execute("INSERT INTO pedidos (pessoa_id, item, horario) VALUES (?, ?, ?)",
                                           (pessoa_id_atual, pedido, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                            conn.commit()
                            contador_confirmacao = 0
                            ultimo_pedido = None
                    else:
                        texto = "Gesto não reconhecido ou pessoa não identificada."

                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

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
