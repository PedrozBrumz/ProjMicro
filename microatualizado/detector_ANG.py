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
TOPICO_COMANDO = "controle/cmd"

# VARIAVEIS GLOBAIS

frame_atual = None
contador_imagens = 0
angulo_curva = 0  # Angulo padrao para curvas


# FUNCOES

def slider(x):
    pass

def slider_angulo(x):
    """Atualiza angulo da curva"""
    global angulo_curva
    angulo_curva = x

def enviar_comando(comando):
    """Envia comando MQTT para controlar robo"""
    try:
        cliente_mqtt.publish(TOPICO_COMANDO, comando)
        print(f"[CMD] Enviado: {comando}")
    except Exception as e:
        print(f"[ERRO] Falha ao enviar comando: {e}")

def desenhar_controles(imagem):
    """Desenha instrucoes de controle na imagem"""
    global angulo_curva
    
    controles = [
        "Q: Sair | X: Salvar | F: Foto",
        f"WASD: Camera | I/K: Frente/Tras | U/O: Curva Frente {angulo_curva} graus | J/L Curva Tras {angulo_curva} graus| P: Parar",
        "L: Lanterna | M: Medir"
    ]
    
    y_pos = imagem.shape[0] - 80
    for i, texto in enumerate(controles):
        cv2.putText(imagem, texto, (10, y_pos + i*25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3)
        cv2.putText(imagem, texto, (10, y_pos + i*25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return imagem

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
        print(f"Enviando comandos em: {TOPICO_COMANDO}")
        print("="*60)
        print("\nControles:")
        print("  Q - Sair")
        print("  X - Salvar foto")
        print("  F - Tirar foto (ESP32)")
        print("")
        print("  CAMERA:")
        print("    W - Servo CIMA")
        print("    S - Servo BAIXO")
        print("    A - Servo ESQUERDA")
        print("    D - Servo DIREITA")
        print("")
        print("  MOVIMENTO ROBO:")
        print("    I - Frente")
        print("    K - Tras")
        print("    O - Curva direita")
        print("    O - Curva direita")
        print("    J - Curva tras esquerda")
        print("    O - Curva direita")
        print("    P - Parar")
        print("")
        print("  ACESSORIOS:")
        print("    L - Lanterna")
        print("    M - Medir distancia")
        print("="*60 + "\n")
        
        # Inscreve nos topicos
        client.subscribe(TOPICO_FOTO)
        client.subscribe(TOPICO_STATUS)
    else:
        print(f" Falha na conexao. Codigo: {rc}")


# INTERFACE

cv2.namedWindow('Detector de Ferrugem')

# Sliders HSV
cv2.createTrackbar('H Min', 'Detector de Ferrugem', 0, 179, slider)
cv2.createTrackbar('H Max', 'Detector de Ferrugem', 25, 179, slider)
cv2.createTrackbar('S Min', 'Detector de Ferrugem', 100, 255, slider)
cv2.createTrackbar('S Max', 'Detector de Ferrugem', 255, 255, slider)
cv2.createTrackbar('V Min', 'Detector de Ferrugem', 50, 255, slider)
cv2.createTrackbar('V Max', 'Detector de Ferrugem', 255, 255, slider)

# Slider de angulo de curva
cv2.createTrackbar('Angulo Curva', 'Detector de Ferrugem', 0, 45, slider_angulo)

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
            
            # Desenha controles na tela
            lado_a_lado = desenhar_controles(lado_a_lado)
            
            # Textos
            texto_info = f"Imagens recebidas: {contador_imagens}"
            cv2.putText(lado_a_lado, texto_info, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            if detectou:
                texto_alerta = f"FERRUGEM DETECTADA!"
                cv2.putText(lado_a_lado, texto_alerta, (10, lado_a_lado.shape[0] - 105), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Mostra
            cv2.imshow('Detector de Ferrugem', lado_a_lado)
        
        # Aguarda teclas
        tecla = cv2.waitKey(30) & 0xFF
        
        # SAIR
        if tecla == ord('q') or tecla == ord('Q'):
            break
        
        # SALVAR IMAGEM
        elif tecla == ord('x') or tecla == ord('X'):
            if frame_atual is not None:
                filename = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame_atual)
                print(f"\nImagem salva: {filename}")
        
        # TIRAR FOTO
        elif tecla == ord('f') or tecla == ord('F'):
            enviar_comando("FOTO")
        
        # SERVOS - WASD
        elif tecla == ord('w') or tecla == ord('W'):
            enviar_comando("SERVO_UP")
        
        elif tecla == ord('s') or tecla == ord('S'):
            enviar_comando("SERVO_DOWN")
        
        elif tecla == ord('a') or tecla == ord('A'):
            enviar_comando("SERVO_LEFT")
        
        elif tecla == ord('d') or tecla == ord('D'):
            enviar_comando("SERVO_RIGHT")
        
        # MOVIMENTO ROBO - UIOJKL + P
        elif tecla == ord('i') or tecla == ord('I'):
            enviar_comando("MOVER_FRENTE")
        
        elif tecla == ord('k') or tecla == ord('K'):
            enviar_comando("MOVER_TRAS")
        
        elif tecla == ord('u') or tecla == ord('U'):
            enviar_comando(f"FRENTE_ESQ_{angulo_curva}")
        
        elif tecla == ord('o') or tecla == ord('O'):
            enviar_comando(f"FRENTE_DIR_{angulo_curva}")
        
        elif tecla == ord('j') or tecla == ord('J'):
            enviar_comando(f"TRAS_ESQ_{angulo_curva}")

        elif tecla == ord('l') or tecla == ord('L'):
            enviar_comando(f"TRAS_DIR_{angulo_curva}")

        elif tecla == ord('p') or tecla == ord('P'):
            enviar_comando("PARAR")
        
        # LANTERNA
        elif tecla == ord('l') or tecla == ord('L'):
            enviar_comando("LANTERNA_TOGGLE")
        
        # MEDIR
        elif tecla == ord('m') or tecla == ord('M'):
            enviar_comando("MEDIR")

finally:
    cliente_mqtt.loop_stop()
    cliente_mqtt.disconnect()
    cv2.destroyAllWindows()
