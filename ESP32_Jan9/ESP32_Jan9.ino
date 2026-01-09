#include <ESP32Servo.h>
#include <string.h>

#define RXD2 16
#define TXD2 17

// =======================================================
// ピン定義と定数
// =======================================================
const int Braille_Pins[][6] = {
  { 33, 25, 26, 27, 14, 13 },
  { 32, 12, 15, 2, 4, 5}
};

const int NUM_CHARS = 2;
const int PINS_PER_CHAR = 6;
const int TOTAL_PINS = NUM_CHARS * PINS_PER_CHAR;

const int ANGLE_OFF = 20;
const int ANGLE_ON = 60;

// タクトスイッチのピン
const int SW_NEXT = 22;    // 進む
const int SW_PREV = 23;    // 戻る

Servo servos[TOTAL_PINS];

// =======================================================
// グローバル変数
// =======================================================
const int BAUD_RATE = 9600;

String receivedBrailleData = "";  // 点字用データ全体
String lastRawData = "";          // 受信生データ
int currentStartIndex = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  Serial2.begin(BAUD_RATE, SERIAL_8N1, RXD2, TXD2);

  // サーボ初期化
  for (int p = 0; p < PINS_PER_CHAR; p++) {
    servos[p].attach(Braille_Pins[0][p]);
    servos[p].write(ANGLE_OFF);
  }

  // スイッチピンの初期化（プルアップ）
  pinMode(SW_NEXT, INPUT_PULLUP);
  pinMode(SW_PREV, INPUT_PULLUP);

  Serial.println("========================================");
  Serial.println("ESP32 Braille Device READY (Switch Mode)");
  Serial.println("Waiting for data...");
  Serial.println("========================================");
}

// 点字1文字を表示する関数
void displayBrailleChar(String signal) {
  for (int p = 0; p < PINS_PER_CHAR; p++) {
    int angle = (signal.charAt(p) == '1') ? ANGLE_ON : ANGLE_OFF;
    servos[p].write(angle);
  }
}

void loop() {
  // ---------- 1. シリアル受信処理 ----------
  if (Serial2.available() > 0) {
    lastRawData = Serial2.readStringUntil('\n');
    lastRawData.trim();

    if (lastRawData.length() > 0 && lastRawData.length() % PINS_PER_CHAR == 0) {
      receivedBrailleData = lastRawData;
      currentStartIndex = 0;
      Serial.println(">> Status: NEW DATA STORED: " + receivedBrailleData);
    } else {
      Serial.println(">> Status: ERROR (Invalid Data Length)");
    }
  }

  // ---------- 2. タクトスイッチ入力処理 ----------
  int totalChars = receivedBrailleData.length() / PINS_PER_CHAR;

  // 「次へ」ボタンが押された（LOW）とき
  if (digitalRead(SW_NEXT) == LOW) {
    if (currentStartIndex + NUM_CHARS < totalChars) {
      currentStartIndex += NUM_CHARS;
      Serial.print(">> SW: NEXT. Index: ");
      Serial.println(currentStartIndex);
      delay(300); // 簡易的なチャタリング防止＆連続送り防止
    }
  }
  // 「戻る」ボタンが押された（LOW）とき
  else if (digitalRead(SW_PREV) == LOW) {
    if (currentStartIndex > 0) {
      currentStartIndex -= NUM_CHARS;
      Serial.print(">> SW: PREV. Index: ");
      Serial.println(currentStartIndex);
      delay(300); // 簡易的なチャタリング防止＆連続送り防止
    }
  }

  // ---------- 3. 表示反映処理 ----------
  int len = receivedBrailleData.length();
  if (len >= 6) {
    int start = currentStartIndex * PINS_PER_CHAR;
    if (start + PINS_PER_CHAR <= len) {
      String signal = receivedBrailleData.substring(start, start + PINS_PER_CHAR);
      displayBrailleChar(signal);
    }
  } else {
    // データがない場合は全下げ
    for (int i = 0; i < TOTAL_PINS; i++) servos[i].write(ANGLE_OFF);
  }

  delay(20);
}