import cv2
import numpy as np
import paho.mqtt.client as mqtt
import ssl
import time
from datetime import datetime
import os

# CONFIGURACOES MQTT
BROKER = "mqtt.janks.dev.br"
PORTA = 8883
USUARIO = "aula"
SENHA = "zowmad-tavQez"

TOPICO_FOTO = "topico/foto"
TOPICO_STATUS = "controle/status"
TOPICO_COMANDO = "controle/cmd"

# VARIAVEIS GLOBAIS
ultimo_envio = 0
intervalo_envio = 10  # segundos
imagens_enviadas = 0
modo = "webcam"  # "webcam", "arquivo", ou "gerada"
arquivo_imagem = None

# CONECTAR MQTT
def ao_conectar(client, userdata, flags, rc):
    if rc == 0:
        print("\n" + "="*60)
        print(" SIMULADOR DE CAMERA CONECTADO")
        print("="*60)
        print(f"Broker: {BROKER}")
        print(f"Enviando fotos em: {TOPICO_FOTO}")
        print(f"Escutando comandos em: {TOPICO_COMANDO}")
        print("="*60 + "\n")
        
        # Inscrever em comandos
        client.subscribe(TOPICO_COMANDO)
        client.publish(TOPICO_STATUS, "SIMULADOR_ONLINE")
    else:
        print(f"Falha na conexao. Codigo: {rc}")

def ao_receber_comando(client, userdata, message):
    """Processa comandos MQTT recebidos"""
    payload = message.payload.decode().strip()
    print(f"[CMD] Recebido: {payload}")
    
    if payload == "FOTO":
        enviar_foto()
    else:
        print(f"[INFO] Comando '{payload}' recebido (simulador ignora comandos de controle)")

# CAPTURAR IMAGEM
def capturar_imagem():
    """Captura imagem baseado no modo selecionado"""
    global modo, arquivo_imagem
    
    if modo == "webcam":
        # Tenta capturar da webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[ERRO] Webcam nao disponivel, usando imagem gerada")
            return gerar_imagem_teste()
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            return frame
        else:
            print("[ERRO] Falha ao capturar da webcam, usando imagem gerada")
            return gerar_imagem_teste()
    
    elif modo == "arquivo":
        # Carrega de arquivo
        if arquivo_imagem and os.path.exists(arquivo_imagem):
            img = cv2.imread(arquivo_imagem)
            if img is not None:
                return img
            else:
                print(f"[ERRO] Falha ao ler {arquivo_imagem}, usando imagem gerada")
                return gerar_imagem_teste()
        else:
            print(f"[ERRO] Arquivo {arquivo_imagem} nao encontrado, usando imagem gerada")
            return gerar_imagem_teste()
    
    else:  # modo == "gerada"
        return gerar_imagem_teste()

def gerar_imagem_teste():
    """Gera uma imagem de teste com informacoes"""
    global imagens_enviadas
    
    # Criar imagem 800x600
    img = np.zeros((600, 800, 3), dtype=np.uint8)
    
    # Fundo gradiente
    for i in range(600):
        cor = int(50 + (i / 600) * 100)
        img[i, :] = [cor, cor//2, cor//3]
    
    # Adicionar "manchas de ferrugem" aleatorias
    for _ in range(5):
        x = np.random.randint(100, 700)
        y = np.random.randint(100, 500)
        raio = np.random.randint(20, 60)
        cor_ferrugem = (20, 80, 200)  # Laranja-marrom (BGR)
        cv2.circle(img, (x, y), raio, cor_ferrugem, -1)
    
    # Texto com informacoes
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cv2.putText(img, "SIMULADOR DE CAMERA ESP32", (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f"Imagem #{imagens_enviadas + 1}", (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(img, timestamp, (50, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
    cv2.putText(img, "Manchas simulando ferrugem", (50, 550),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
    
    return img

def enviar_foto():
    """Captura e envia foto via MQTT"""
    global imagens_enviadas
    
    try:
        # Capturar imagem
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Capturando imagem...")
        imagem = capturar_imagem()
        
        if imagem is None:
            print("[ERRO] Falha ao capturar imagem")
            cliente_mqtt.publish(TOPICO_STATUS, "ERRO_CAPTURA")
            return
        
        # Redimensionar se muito grande (opcional)
        altura, largura = imagem.shape[:2]
        if largura > 1024:
            fator = 1024 / largura
            nova_largura = 1024
            nova_altura = int(altura * fator)
            imagem = cv2.resize(imagem, (nova_largura, nova_altura))
        
        # Codificar como JPEG
        ret, buffer = cv2.imencode('.jpg', imagem, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        if not ret:
            print("[ERRO] Falha ao codificar imagem")
            cliente_mqtt.publish(TOPICO_STATUS, "ERRO_CODIFICACAO")
            return
        
        # Enviar via MQTT
        jpeg_bytes = buffer.tobytes()
        tamanho_kb = len(jpeg_bytes) / 1024
        
        ok = cliente_mqtt.publish(TOPICO_FOTO, jpeg_bytes)
        
        if ok.rc == mqtt.MQTT_ERR_SUCCESS:
            imagens_enviadas += 1
            print(f"    Foto enviada! Tamanho: {tamanho_kb:.1f} KB")
            print(f"    Total enviado: {imagens_enviadas}")
            cliente_mqtt.publish(TOPICO_STATUS, "OK_FOTO")
        else:
            print(f"    Falha ao enviar foto! Codigo: {ok.rc}")
            cliente_mqtt.publish(TOPICO_STATUS, "ERRO_ENVIO_MQTT")
        
    except Exception as e:
        print(f"[ERRO] Excecao ao enviar foto: {e}")
        cliente_mqtt.publish(TOPICO_STATUS, f"ERRO: {str(e)}")

# MENU DE CONFIGURACAO
def menu_configuracao():
    """Menu para configurar o simulador"""
    global modo, arquivo_imagem, intervalo_envio
    
    print("\n" + "="*60)
    print(" CONFIGURACAO DO SIMULADOR")
    print("="*60)
    print("\nEscolha o modo de operacao:")
    print("  1 - Webcam (captura da sua webcam)")
    print("  2 - Arquivo (usa uma imagem salva)")
    print("  3 - Gerada (cria imagens de teste)")
    print()
    
    while True:
        escolha = input("Digite sua escolha (1/2/3): ").strip()
        
        if escolha == "1":
            modo = "webcam"
            print("[OK] Modo: WEBCAM")
            break
        elif escolha == "2":
            modo = "arquivo"
            arquivo = input("Digite o caminho da imagem: ").strip()
            if os.path.exists(arquivo):
                arquivo_imagem = arquivo
                print(f"[OK] Modo: ARQUIVO ({arquivo})")
                break
            else:
                print(f"[ERRO] Arquivo nao encontrado: {arquivo}")
                print("Tentando novamente...")
        elif escolha == "3":
            modo = "gerada"
            print("[OK] Modo: IMAGEM GERADA")
            break
        else:
            print("[ERRO] Escolha invalida. Digite 1, 2 ou 3.")
    
    # Configurar intervalo
    print()
    while True:
        try:
            intervalo = input(f"Intervalo entre fotos em segundos (atual: {intervalo_envio}): ").strip()
            if intervalo:
                intervalo_envio = int(intervalo)
            print(f"[OK] Intervalo: {intervalo_envio} segundos")
            break
        except ValueError:
            print("[ERRO] Digite um numero inteiro valido")

# MAIN
if __name__ == "__main__":
    print("="*60)
    print(" SIMULADOR DE CAMERA ESP32-CAM via MQTT")
    print("="*60)
    print()
    print("Este simulador substitui o ESP32-CAM para testes")
    print("Envia fotos automaticamente via MQTT")
    print()
    
    # Menu de configuracao
    menu_configuracao()
    
    # Conectar MQTT
    cliente_mqtt = mqtt.Client()
    cliente_mqtt.on_connect = ao_conectar
    cliente_mqtt.on_message = ao_receber_comando
    
    # SSL
    cliente_mqtt.tls_set(cert_reqs=ssl.CERT_NONE)
    cliente_mqtt.tls_insecure_set(True)
    cliente_mqtt.username_pw_set(USUARIO, SENHA)
    
    print(f"\nConectando ao broker {BROKER}:{PORTA}...")
    
    try:
        cliente_mqtt.connect(BROKER, PORTA, 60)
        cliente_mqtt.loop_start()
        
        print("\n[INFO] Simulador iniciado!")
        print(f"[INFO] Modo: {modo.upper()}")
        print(f"[INFO] Intervalo: {intervalo_envio}s")
        print("\n[INFO] Pressione Ctrl+C para parar")
        print("="*60 + "\n")
        
        # Loop principal
        while True:
            tempo_atual = time.time()
            
            # Enviar foto automaticamente
            if tempo_atual - ultimo_envio >= intervalo_envio:
                enviar_foto()
                ultimo_envio = tempo_atual
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Simulador interrompido pelo usuario")
    
    except Exception as e:
        print(f"\n[ERRO] Erro no simulador: {e}")
    
    finally:
        cliente_mqtt.loop_stop()
        cliente_mqtt.disconnect()
        print("[INFO] Simulador encerrado")
        print(f"[INFO] Total de fotos enviadas: {imagens_enviadas}")
