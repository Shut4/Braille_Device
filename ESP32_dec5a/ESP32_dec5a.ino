#include <ESP32Servo.h>
#include <string.h>

// =======================================================
// 1. 定数とピン定義
// =======================================================

// ESP32の安全なGPIOピンに割り当てます。
const int Braille_Pins[][6] = {
    // 1文字目 (6ピン)
    {33, 25, 26, 27, 14, 12}
};

const int NUM_CHARS = 1;    // 一度に表示する文字数
const int PINS_PER_CHAR = 6;
const int TOTAL_PINS = NUM_CHARS * PINS_PER_CHAR; // 常に 6 です

// サーボ角度
const int ANGLE_OFF = 0;
const int ANGLE_ON = 45;

// タクトスイッチピン (シリアルキー入力の制御ロジックに流用)
// 物理ピンの定義は維持しますが、ロジックでは使用しません
const int NEXT_PAGE_PIN = 34;
const int PREV_PAGE_PIN = 35;

// =======================================================
// 2. グローバル変数とテストデータ
// =======================================================

Servo servos[TOTAL_PINS];

// テスト用バイナリ信号の定義 (10文字分のデータ)
const char* const TEST_DATA_RAW = "100000110000100100110100010100100001110001100101110101010101";

// receivedBrailleData は String 型で初期化
String receivedBrailleData = "";
int currentStartIndex = 0;
const int BAUD_RATE = 115200;

// --------------------------------------------------------
// 3. 初期設定 setup()
// --------------------------------------------------------

void setup() {
    Serial.begin(BAUD_RATE);

    // receivedBrailleData にテストデータを代入
    receivedBrailleData = String(TEST_DATA_RAW);

    for (int c = 0; c < NUM_CHARS; c++) {
        for (int p = 0; p < PINS_PER_CHAR; p++) {
            int servoIndex = c * PINS_PER_CHAR + p;
            servos[servoIndex].attach(Braille_Pins[c][p]);
            servos[servoIndex].write(ANGLE_OFF);
        }
    }

    // 物理タクトスイッチの pinMode は不要 (キー入力に置き換え)

    Serial.println("ESP32 Braille Device TEST MODE (Keyboard Control).");
    Serial.print("Total Test Chars: ");
    Serial.println(receivedBrailleData.length() / PINS_PER_CHAR);
    Serial.println("Enter 'n' for NEXT, 'p' for PREVIOUS.");
}

// --------------------------------------------------------
// 4. 点字ピン表示関数 (変更なし)
// --------------------------------------------------------

void displayBrailleChar(int charIndex, String signal) {
    for (int p = 0; p < PINS_PER_CHAR; p++) {
        int servoIndex = charIndex * PINS_PER_CHAR + p;

        int targetAngle = (signal.charAt(p) == '1') ? ANGLE_ON : ANGLE_OFF;
        servos[servoIndex].write(targetAngle);
        delay(1);
    }
}

// --------------------------------------------------------
// 5. メインループ loop()
// --------------------------------------------------------

void loop() {

    // 5.1. シリアルデータ受信処理 (キーボード入力によるページング)
    if (Serial.available() > 0) {
        char incomingChar = Serial.read(); // 1文字読み込み
        int totalChars = receivedBrailleData.length() / PINS_PER_CHAR;

        if (receivedBrailleData.length() > 0) {

             // 'n' または 'N' キーで次のページへ
            if (incomingChar == 'n' || incomingChar == 'N') {
                if (currentStartIndex + NUM_CHARS < totalChars) {
                    currentStartIndex += NUM_CHARS;
                    Serial.println("Page Forward (N).");
                }
            }
            // 'p' または 'P' キーで前のページへ
            else if (incomingChar == 'p' || incomingChar == 'P') {
                if (currentStartIndex > 0) {
                    currentStartIndex -= NUM_CHARS;
                    Serial.println("Page Backward (P).");
                }
            }
        }
    }

    // 5.3. 点字の表示処理
    if (receivedBrailleData.length() > 0) {
        int dataLength = receivedBrailleData.length();

        for (int c = 0; c < NUM_CHARS; c++) {
            int globalCharIndex = currentStartIndex + c;

            // データ範囲外の場合は、空点(全てOFF)を表示
            if (globalCharIndex * PINS_PER_CHAR >= dataLength) {
                 displayBrailleChar(c, "000000");
            } else {
                // 6桁のバイナリ信号を抽出
                String signal = receivedBrailleData.substring(globalCharIndex * PINS_PER_CHAR,
                                                            (globalCharIndex + 1) * PINS_PER_CHAR);
                displayBrailleChar(c, signal);
            }
        }
    } else {
        // データがない場合は全消灯
        for (int i = 0; i < TOTAL_PINS; i++) {
            servos[i].write(ANGLE_OFF);
        }
    }
}