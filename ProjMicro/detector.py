import cv2
import numpy
import paho.mqtt.client as mqtt
import ssl
from datetime import datetime

# CONFIGURACOES MQTT

BROKER = "mqtt.janks.dev.br"
PORTA = 8883
USUARIO = "aula"
SENHA = "zowmad-tavQez"

TOPICO_FOTO = "topico/foto"
TOPICO_STATUS = "controle/status"

# VARIAVEIS GLOBAIS

frame_atual = None
contador_imagens = 0


# FUNCOES

def slider(x):
    pass

def ao_receber_mensagem(client, userdata, message):
    """Recebe mensagens MQTT"""
    global frame_atual, contador_imagens
    
    topico = message.topic
    
    # Recebe FOTO
    if topico == TOPICO_FOTO:
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Imagem recebida via MQTT")
            
            # Decodifica JPEG direto
            imagem_bytes = message.payload
            nparr = numpy.frombuffer(imagem_bytes, numpy.uint8)
            frame_atual = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame_atual is not None:
                contador_imagens += 1
                h, w = frame_atual.shape[:2]
                print(f"    Imagem #{contador_imagens} processada ({w}x{h})")
            else:
                print(f"    Erro ao decodificar imagem")
                
        except Exception as e:
            print(f"    Erro ao receber imagem: {e}")
    
    # Recebe STATUS
    elif topico == TOPICO_STATUS:
        status = message.payload.decode()
        print(f"[STATUS] {status}")

def ao_conectar(client, userdata, flags, rc):
    if rc == 0:
        print("\n" + "="*60)
        print(" DETECTOR PYTHON CONECTADO")
        print("="*60)
        print(f"Broker: {BROKER}")
        print(f"Escutando fotos em: {TOPICO_FOTO}")
        print("="*60 + "\n")
        
        # Inscreve nos tOpicos
        client.subscribe(TOPICO_FOTO)
        client.subscribe(TOPICO_STATUS)
    else:
        print(f" Falha na conexao. Código: {rc}")


# INTERFACE

cv2.namedWindow('Detector de Ferrugem')

cv2.createTrackbar('H Min', 'Detector de Ferrugem', 0, 179, slider)
cv2.createTrackbar('H Max', 'Detector de Ferrugem', 25, 179, slider)
cv2.createTrackbar('S Min', 'Detector de Ferrugem', 100, 255, slider)
cv2.createTrackbar('S Max', 'Detector de Ferrugem', 255, 255, slider)
cv2.createTrackbar('V Min', 'Detector de Ferrugem', 50, 255, slider)
cv2.createTrackbar('V Max', 'Detector de Ferrugem', 255, 255, slider)

# CONEXAO MQTT

cliente_mqtt = mqtt.Client()
cliente_mqtt.on_connect = ao_conectar
cliente_mqtt.on_message = ao_receber_mensagem

# SSL

cliente_mqtt.tls_set(cert_reqs=ssl.CERT_NONE)
cliente_mqtt.tls_insecure_set(True)
cliente_mqtt.username_pw_set(USUARIO, SENHA)

print(f"Conectando ao broker {BROKER}:{PORTA}...")

try:
    cliente_mqtt.connect(BROKER, PORTA, 60)
    cliente_mqtt.loop_start()
    
    # LOOP PRINCIPAL
    
    while True:
        # Processa e mostra frame se existir
        if frame_atual is not None:
            frame = frame_atual.copy()
            
            # Converte para HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Valores dos sliders
            h_min = cv2.getTrackbarPos('H Min', 'Detector de Ferrugem')
            h_max = cv2.getTrackbarPos('H Max', 'Detector de Ferrugem')
            s_min = cv2.getTrackbarPos('S Min', 'Detector de Ferrugem')
            s_max = cv2.getTrackbarPos('S Max', 'Detector de Ferrugem')
            v_min = cv2.getTrackbarPos('V Min', 'Detector de Ferrugem')
            v_max = cv2.getTrackbarPos('V Max', 'Detector de Ferrugem')
            
            # Range cores
            cor_baixo = numpy.array([h_min, s_min, v_min])
            cor_alto = numpy.array([h_max, s_max, v_max])
            
            # Mascara
            mask = cv2.inRange(hsv, cor_baixo, cor_alto)
            
            # Contornos
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Desenha
            resultado = frame.copy()
            cv2.drawContours(resultado, contours, -1, (0, 255, 0), 3)
            
            # Calcula area
            area_total = sum(cv2.contourArea(c) for c in contours)
            detectou = (len(contours) > 0 and area_total > 500)
            
            # Junta imagens
            lado_a_lado = numpy.hstack((frame, resultado))
            
            # Textos
            texto_info = f"Imagens recebidas: {contador_imagens}"
            cv2.putText(lado_a_lado, texto_info, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if detectou:
                texto_alerta = f"FERRUGEM DETECTADA!"
                cv2.putText(lado_a_lado, texto_alerta, (10, lado_a_lado.shape[0] - 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Mostra
            cv2.imshow('Detector de Ferrugem', lado_a_lado)
        
        # Aguarda teclas
        tecla = cv2.waitKey(30) & 0xFF
        
        if tecla == ord('q') or tecla == ord('Q'):
            break
        
        # Salvar imagem
        elif tecla == ord('s') or tecla == ord('S'):
            if frame_atual is not None:
                filename = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame_atual)
                print(f"\n Imagem salva: {filename}")

finally:
    cliente_mqtt.loop_stop()
    cliente_mqtt.disconnect()
    cv2.destroyAllWindows()
