#include <WiFi.h>
#include <WiFiClientSecure.h>
#include "certificados.h"
#include <MQTT.h>
#include <esp_camera.h>

// ------------ SERIAL (ESP -> Arduino) -----------------
#define RX_ESP 1   // Pino RX da UART2
#define TX_ESP 2  // Pino TX da UART2
HardwareSerial SerialESP(2);

// ------------ MQTT ------------------------------------
WiFiClientSecure conexaoSegura;
MQTTClient mqtt(200000);

// ------------ CAMERA CONFIG ---------------------------
// CAMERA CONFIG
camera_config_t config = {
  .pin_pwdn = -1, .pin_reset = -1, .pin_xclk = 15, .pin_sscb_sda = 4, .pin_sscb_scl = 5,
  .pin_d7 = 16, .pin_d6 = 17, .pin_d5 = 18, .pin_d4 = 12, .pin_d3 = 10, .pin_d2 = 8,
  .pin_d1 = 9, .pin_d0 = 11, .pin_vsync = 6, .pin_href = 7, .pin_pclk = 13,
  .xclk_freq_hz = 20000000,
  .ledc_timer = LEDC_TIMER_0, .ledc_channel = LEDC_CHANNEL_0,
  .pixel_format = PIXFORMAT_JPEG,
  .frame_size = FRAMESIZE_SVGA,
  .jpeg_quality = 10,
  .fb_count = 2,
  .grab_mode = CAMERA_GRAB_LATEST
};

// -------------------------------------------------------
//  FUNÇÃO: Tirar foto e enviar via MQTT
// -------------------------------------------------------
void tirarFotoEEnviarParaMQTT() {
  camera_fb_t* foto = esp_camera_fb_get();
  if (!foto) {
    Serial.println("Falha ao capturar foto");
    mqtt.publish("controle/status", "ERRO_CAMERA");
    return;
  }

  bool ok = mqtt.publish("topico/foto", (const char*)foto->buf, foto->len);

  if (ok) {
    Serial.println("Foto enviada com sucesso!");
    mqtt.publish("controle/status", "OK_FOTO");
  } else {
    Serial.println("Falha ao enviar foto!");
    mqtt.publish("controle/status", "ERRO_ENVIO_MQTT");
  }

  esp_camera_fb_return(foto);
}

// -------------------------------------------------------
//  Reconexão WiFi
// -------------------------------------------------------
void reconectarWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Reconectando WiFi...");
    WiFi.begin("Projeto", "2022-11-07");
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }
    Serial.println("\nWiFi conectado!");
  }
}

// -------------------------------------------------------
//  Reconexão MQTT
// -------------------------------------------------------
void reconectarMQTT() {
  while (!mqtt.connected()) {
    Serial.println("Reconectando MQTT...");
    mqtt.connect("espcam_roberto", "aula", "zowmad-tavQez");
    delay(500);
  }
  Serial.println("MQTT conectado!");
}

// -------------------------------------------------------
//  CALLBACK: Mensagens MQTT recebidas
// -------------------------------------------------------
void recebeMensagemMQTT(String &topic, String &payload) {
  payload.trim();
  Serial.println("MQTT CMD: " + payload);

  if (payload == "FOTO") {
    tirarFotoEEnviarParaMQTT();
  }

  else if (payload == "LED_ON") {
    SerialESP.println("LED_ON");
    mqtt.publish("controle/status", "LED_ON enviado ao Arduino");
  }

  else if (payload == "LED_OFF") {
    SerialESP.println("LED_OFF");
    mqtt.publish("controle/status", "LED_OFF enviado ao Arduino");
  }

  else {
    mqtt.publish("controle/status", "CMD_DESCONHECIDO");
  }
}

// -------------------------------------------------------
//  SETUP
// -------------------------------------------------------
unsigned long ultimoEnvio = 0;

void setup() {
  Serial.begin(115200);

  // Serial com Arduino
  SerialESP.begin(9600, SERIAL_8N1, RX_ESP, TX_ESP);
  SerialESP.println("ESP32 pronto para comunicar!");

  // Inicializar câmera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Erro camera: 0x%x\n", err);
    while (true);
  }

  // WiFi
  reconectarWiFi();

  // MQTT
  conexaoSegura.setCACert(certificado1);
  mqtt.begin("mqtt.janks.dev.br", 8883, conexaoSegura);
  mqtt.onMessage(recebeMensagemMQTT);
  reconectarMQTT();

  // Inscrever em comandos
  mqtt.subscribe("controle/cmd");

  mqtt.publish("controle/status", "ESP32_ONLINE");
}

// -------------------------------------------------------
//  LOOP PRINCIPAL
// -------------------------------------------------------
void loop() {
  // Verificar mensagens recebidas pelo ARDUINO
  if (SerialESP.available()) {
    String resp = SerialESP.readStringUntil('\n');
    resp.trim();
    mqtt.publish("controle/arduino_resp", resp);
  }

  if(Serial.available()) {
    String inti = Serial.readStringUntil('\n');
    SerialESP.println(inti);
  }

  // Manter MQTT e WiFi vivos
  reconectarWiFi();
  reconectarMQTT();
  mqtt.loop();

  // FOTO a cada 10 segundos (se quiser manter)
  if (millis() - ultimoEnvio > 10000) {
    tirarFotoEEnviarParaMQTT();
    ultimoEnvio = millis();
  }
}
