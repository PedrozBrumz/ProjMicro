// BIBLIOTECAS

// Servos (câmera):
#include <Servo.h>
#include <GFButton.h>
#include <Ultrasonic.h>

// Motores (movimento):
#include <AFMotor_R4.h>
#include <PID_v1.h>

// PARTE 1: SERVOS, LANTERNA, DIST, BOTOES

Servo servo1;
Servo servo2;
Ultrasonic ultrassom(A4,A3);
int pinoDoServo1 = 9;
int pinoDoServo2 = 8;
int rele = 46;

GFButton cima(2);
GFButton direita(39);
GFButton baixo(4);        // ← MUDADO de 3 para 4 (conflito com Motor Shield)
GFButton esquerda(38);
GFButton lanterna(37);
GFButton medida(36);
int pos1 = 90;
int pos2 = 90;
bool estado = false;

long distancia;

// PARTE 2: MOTORES

AF_DCMotor motorDir(1);
AF_DCMotor motorEsq(2);

const int velocidadeBase = 100;
const int PIDtempoAmostra = 50;
unsigned long PIDultimoTempo = 0;

double velInEsq, pwmOutEsq, velSetEsq;
PID PIDesq(&velInEsq, &pwmOutEsq, &velSetEsq, 1.5, 0.0, 0.0, DIRECT);

double velInDir, pwmOutDir, velSetDir;
PID PIDdir(&velInDir, &pwmOutDir, &velSetDir, 1.5, 0.0, 0.0, DIRECT);

// SETUP

void setup() {
  Serial.begin(9600);
  Serial.println("Arduino Mega pronto!");
  Serial.println("Sistema integrado: Servos + Motores");
  
  // SETUP PARTE 1: SERVOS, LANTERNA, DIST
  
  servo1.attach(pinoDoServo1);
  servo2.attach(pinoDoServo2);
  servo1.write(pos1);
  servo2.write(pos2);
  
  pinMode(rele, OUTPUT);
  digitalWrite(rele, HIGH);
  lanterna.setPressHandler(lanternaLigada);
  medida.setPressHandler(distanciaMedida);
  
  Serial.println("Servos inicializados!");
  
  // SETUP PARTE 2: MOTORES
  
  PIDesq.SetMode(AUTOMATIC);
  PIDdir.SetMode(AUTOMATIC);

  PIDesq.SetOutputLimits(-255, 255); 
  PIDdir.SetOutputLimits(-255, 255);
  
  PIDesq.SetSampleTime(PIDtempoAmostra);
  PIDdir.SetSampleTime(PIDtempoAmostra);

  PIDultimoTempo = millis();
  
  Serial.println("Motores inicializados!");
  Serial.println();
  Serial.println("Comandos disponiveis:");
  Serial.println("  Movimento: f (frente), t (tras), p (parar)");
  Serial.println("  Exemplos: 'f', 'fe30', 'fd45', 't', 'p'");
  Serial.println("  Servos: Usar botoes fisicos");
  Serial.println();
}

// LOOP PRINCIPAL

void loop() {
  
  // LOOP PARTE 1: BOTOES
  
  // Processar botoes fisicos
  cima.process();
  baixo.process();
  direita.process();
  esquerda.process();
  lanterna.process();
  medida.process();

  if (cima.isPressed() && pos1 < 180) {
    pos1++;
    servo1.write(pos1);
    delay(30);
    Serial.println(pos1);
  } else if (baixo.isPressed() && pos1 > 0) {
    pos1--;
    servo1.write(pos1);
    delay(30);
    Serial.println(pos1);
  } else if (esquerda.isPressed() && pos2 < 180){
    pos2++;
    servo2.write(pos2);
    delay(30);
    Serial.println(pos2);
  } else if (direita.isPressed() && pos2 > 0){
    pos2--;
    servo2.write(pos2);
    delay(30);
    Serial.println(pos2);
  }
  
  // LOOP PARTE 2: MOTORES
  
  // Atualizar controle PID dos motores
  atualizarPID();

  // Processar comandos de movimento via Serial
  if (Serial.available() > 0) {
    String texto = Serial.readStringUntil('\n');
    
    if (texto == "p") parar();
    else {
      int angulo;
      if (texto[1] == 'd') angulo = - texto.substring(2).toInt();
      else if (texto[1] == 'e') angulo = texto.substring(2).toInt();
      else angulo = 0;
      
      bool sentido;
      if (texto[0] == 'f'){
        sentido = true;
        mover(angulo,sentido);
      } 
      else if (texto[0] == 't') {
        sentido = false; 
        mover(angulo,sentido);
      }
    }
  }
}

// FUNÇÕES PARTE 1: LANTERNA, DIST

void lanternaLigada(GFButton& lanterna){
  if(!estado){
    digitalWrite(rele, LOW);
    estado = true;
    Serial.println("Lanterna LIGADA");
  }else{
    digitalWrite(rele, HIGH);
    estado = false;
    Serial.println("Lanterna DESLIGADA");
  }
}

void distanciaMedida(GFButton& medida){
  distancia = ultrassom.read(CM);
  Serial.print(distancia);
  Serial.println(" cm");
}

// FUNÇÕES PARTE 2: MOTORES

void setSpeedDirec(AF_DCMotor &motor, double output) {
  int pwm = abs(output);
  pwm = constrain(pwm, 0, 255); 

  motor.setSpeed(pwm);

  if (output > 0) {
    motor.run(FORWARD);
  } else if (output < 0) {
    motor.run(BACKWARD);
  } else {
    motor.run(RELEASE);
  }
}

void atualizarPID() {
  unsigned long agora = millis();
  if (agora - PIDultimoTempo >= PIDtempoAmostra) {
    PIDultimoTempo = agora;

    velInEsq = (double)(1000.0 / PIDtempoAmostra);
    velInDir = (double)(1000.0 / PIDtempoAmostra);

    PIDesq.Compute();
    PIDdir.Compute();

    setSpeedDirec(motorEsq, pwmOutEsq);
    setSpeedDirec(motorDir, pwmOutDir);
  }
}

void mover(int angulo, bool sentido) {
  float fator = constrain((float)angulo / 180.0, -1.0, 1.0); 
  float alvoEsq = velocidadeBase * (1.0 - fator);
  float alvoDir = velocidadeBase * (1.0 + fator);
  
  Serial.print("Robo se movendo para ");
  if (!sentido) {
    alvoEsq = - alvoEsq;
    alvoDir = - alvoDir;
    Serial.print("tras");
  }
  else Serial.print("frente");
  
  if (angulo==0) Serial.println("!");
  else {
    Serial.print(" com angulo de ");
    Serial.print(abs(angulo));
    if (angulo>0) Serial.println(" graus para a esquerda!");
    else Serial.println(" graus para a direita!");
  }
  
  velSetEsq = constrain(alvoEsq, -255.0, 255.0);
  velSetDir = constrain(alvoDir, -255.0, 255.0);
}

void parar(){
  velSetEsq = 0;
  velSetDir = 0;
  Serial.println("Robo parado!");
}
