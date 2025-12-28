#include <ESP32Servo.h>
#include <string.h>

#define RXD2 16
#define TXD2 17

// =======================================================
// ピン定義と定数
// =======================================================
const int Braille_Pins[][6] = {
  { 33, 25, 26, 27, 14, 13 }
};

const int NUM_CHARS = 1;
const int PINS_PER_CHAR = 6;
const int TOTAL_PINS = NUM_CHARS * PINS_PER_CHAR;

const int ANGLE_OFF = 0;
const int ANGLE_ON = 45;

Servo servos[TOTAL_PINS];

// =======================================================
// グローバル変数
// =======================================================
const int BAUD_RATE = 9600;

String receivedBrailleData = "";  // 点字用データ全体を保持
String lastRawData = "";          // 直前にシリアル受信した生データを保持（確認用）
int currentStartIndex = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  Serial2.begin(BAUD_RATE, SERIAL_8N1, RXD2, TXD2);

  for (int p = 0; p < PINS_PER_CHAR; p++) {
    servos[p].attach(Braille_Pins[0][p]);
    servos[p].write(ANGLE_OFF);
  }

  Serial.println("========================================");
  Serial.println("ESP32 Braille Device READY");
  Serial.print("Baud Rate: ");
  Serial.println(BAUD_RATE);
  Serial.println("Waiting for data...");
  Serial.println("========================================");
}

void displayBrailleChar(String signal) {
  for (int p = 0; p < PINS_PER_CHAR; p++) {
    int angle = (signal.charAt(p) == '1') ? ANGLE_ON : ANGLE_OFF;
    servos[p].write(angle);
    delay(1);
  }
}

void loop() {
  // Serial.println(Serial2.available());
  // ---------- シリアル受信処理 ----------
  if (Serial2.available() > 0) {
    // 改行コードまで読み込み、変数に格納
    lastRawData = Serial2.readStringUntil('\n');
    lastRawData.trim();  // 空白や不要な改行を削除
    Serial.println("raw data=" + lastRawData);

    if (lastRawData.length() > 0) {
      // 受信した内容を即座にシリアルモニタで確認
      Serial.println("[DEBUG] Received Raw Data:");
      Serial.println(lastRawData);
      Serial.print("[DEBUG] Length: ");
      Serial.println(lastRawData.length());
    }
    // --- 点字データ (6の倍数) の判定 ---
    else if (lastRawData.length() % PINS_PER_CHAR == 0) {
      receivedBrailleData = lastRawData;
      currentStartIndex = 0;
      Serial.println(">> Status: NEW BRAILLE DATA STORED");
    }
    // --- 不正なデータ形式 ---
    else {
      Serial.println(">> Status: ERROR (Invalid Length)");
    }

    // 現在のステータスを表示
    Serial.print("[STATUS] Current Display Char Index: ");
    Serial.println(currentStartIndex);
    Serial.println("----------------------------------------");
  }

  char command = lastRawData.charAt(0);
  int totalChars = receivedBrailleData.length() / PINS_PER_CHAR;

  if (command == 'n' || command == 'N') {
    if (currentStartIndex + NUM_CHARS < totalChars) {
      currentStartIndex += NUM_CHARS;
      Serial.println(">> Command: NEXT PAGE");
    }
  } else if (command == 'p' || command == 'P') {
    if (currentStartIndex > 0) {
      currentStartIndex -= NUM_CHARS;
      Serial.println(">> Command: PREVIOUS PAGE");
    }
  }
  // ---------- 表示処理 ----------
  int len = receivedBrailleData.length();
  if (len >= 6) {
    int start = currentStartIndex * PINS_PER_CHAR;
    if (start + PINS_PER_CHAR <= len) {
      String signal = receivedBrailleData.substring(start, start + PINS_PER_CHAR);
      displayBrailleChar(signal);
    } else {
      for (int i = 0; i < TOTAL_PINS; i++) servos[i].write(ANGLE_OFF);
    }
  } else {
    for (int i = 0; i < TOTAL_PINS; i++) servos[i].write(ANGLE_OFF);
  }

  delay(10);
}