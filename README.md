Projeto de robô móvel com câmera ESP32 e sistema de detecção de ferrugem por visão computacional.

Descrição
Este projeto detecta ferrugem em superfícies metálicas usando uma câmera ESP32-CAM que envia imagens via WiFi/MQTT para processamento em Python com OpenCV. O robô se move e permite controle manual da câmera através de servos.

Recursos
- Detecção automática de ferrugem usando análise HSV
- Transmissão de imagens via MQTT com SSL
- Controle de movimento do robô (frente, trás, curvas)
- Controle de posição da câmera com servos
- Interface Python com sliders ajustáveis
- Lanterna e sensor ultrassônico

Arquitetura

O sistema possui três componentes principais:

ESP32-CAM:
- Captura fotos automaticamente a cada 10 segundos
- Transmite via WiFi/MQTT para o PC

Python:
- Recebe imagens via MQTT
- Processa usando OpenCV
- Detecta ferrugem por cor (espaço HSV)
- Interface gráfica com ajuste em tempo real

Arduino:
- Controla 2 servos para posição da câmera
- Controla motores DC para movimento
- PID para movimento suave

Funcionamento
- ESP32 captura foto e envia via MQTT
- Programa recebe e processa imagem
- Algoritmo HSV detecta áreas com cor de ferrugem
- Resultado é exibido em tempo real
- Operador pode mover robô e câmera
