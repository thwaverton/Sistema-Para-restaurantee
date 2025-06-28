import cv2
from ultralytics import YOLO
import numpy as np

# 1. Carregar o modelo YOLO para detecção de pessoas
# Você pode usar 'yolov8n.pt' para um modelo menor e mais rápido, ou 'yolov8m.pt' para um modelo mais preciso.
# Certifique-se de ter o modelo baixado ou ele será baixado automaticamente na primeira execução.
model = YOLO('yolov8n.pt')

# 2. Definir a área de perigo (exemplo: um retângulo fixo na tela)
# Coordenadas (x_min, y_min, x_max, y_max) da área de perigo
# Adapte estes valores conforme a sua necessidade e resolução da câmera
DANGER_ZONE = (200, 100, 400, 380) # Exemplo: um retângulo no centro da tela

# Função para calcular a distância (neste caso, a distância euclidiana entre o centro da pessoa e o centro da área de perigo)
def calcular_distancia(ponto1, ponto2):
    return np.sqrt((ponto1[0] - ponto2[0])**2 + (ponto1[1] - ponto2[1])**2)

# Captura de vídeo da webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Erro ao abrir a câmera.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Inverter o frame para espelhamento (opcional, dependendo da câmera)
    frame = cv2.flip(frame, 1)
    
    # Desenhar a área de perigo no frame
    cv2.rectangle(frame, (DANGER_ZONE[0], DANGER_ZONE[1]), (DANGER_ZONE[2], DANGER_ZONE[3]), (0, 0, 255), 2)
    cv2.putText(frame, "Area de Perigo", (DANGER_ZONE[0], DANGER_ZONE[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)

    # 1. Identificar pessoas
    # Rodar a inferência YOLOv8 no frame
    results = model(frame, stream=True, classes=[0]) # classes=[0] para detectar apenas 'person'

    pessoa_detectada = False
    for r in results:
        boxes = r.boxes
        for box in boxes:
            # Coordenadas da bounding box da pessoa
            x1, y1, x2, y2 = box.xyxy[0].int().tolist()
            
            # Centro da bounding box da pessoa
            centro_pessoa_x = (x1 + x2) // 2
            centro_pessoa_y = (y1 + y2) // 2
            centro_pessoa = (centro_pessoa_x, centro_pessoa_y)

            # Desenhar a bounding box e o centro da pessoa
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, centro_pessoa, 5, (0, 255, 0), -1)
            cv2.putText(frame, "Pessoa", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
            
            # 3. Calcular a distância da pessoa até a área de perigo
            # Centro da área de perigo
            centro_zona_perigo_x = (DANGER_ZONE[0] + DANGER_ZONE[2]) // 2
            centro_zona_perigo_y = (DANGER_ZONE[1] + DANGER_ZONE[3]) // 2
            centro_zona_perigo = (centro_zona_perigo_x, centro_zona_perigo_y)
            
            cv2.circle(frame, centro_zona_perigo, 5, (0, 0, 255), -1) # Desenha o centro da zona de perigo

            dist = calcular_distancia(centro_pessoa, centro_zona_perigo)
            
            # Definir um limite de segurança (ajuste conforme necessário)
            limite_seguranca = 150 # pixels
            
            status_perigo = ""
            cor_status = (255, 255, 255) # Branco
            
            if dist < limite_seguranca:
                status_perigo = "PERIGO: MUITO PROXIMO!"
                cor_status = (0, 0, 255) # Vermelho
            else:
                status_perigo = "Distancia Segura"
                cor_status = (0, 255, 0) # Verde
                
            cv2.putText(frame, f"Distancia: {dist:.2f} px", (centro_pessoa_x, centro_pessoa_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, status_perigo, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, cor_status, 2, cv2.LINE_AA)
            
            pessoa_detectada = True
            
    if not pessoa_detectada:
        cv2.putText(frame, "Nenhuma pessoa detectada", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)


    # Exibir o frame
    cv2.imshow('Sistema de Deteccao de Perigo', frame)

    # Pressione 'q' para sair
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()