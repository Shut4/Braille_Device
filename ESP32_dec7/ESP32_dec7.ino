//arduinoIDEでESP32ボードで点字ピンを出力したい場合に使用するコード。
//Githubで管理しやすいように、arduinoIDEのファイルをVSCodeにもってきたやつ。
//これをESP32でarduinoIDEを用いて動作検証する場合、ファイル名と同じ名前のディレクトリの中に配置しないとファイルが正しく動作しない。

#include <ESP32Servo.h>
#include <string.h>

// =======================================================
// 1. 定数とピン定義
// =======================================================

// このESP32コードは、PC3のProcessingコード（`tennji_serverBa.pde`）から送られてくる**シリアルデータ（長文の点字バイナリ文字列またはコマンド）に**対応しています。

// ### ✅ 修正によって実現されたシリアルデータへの対応

// 元のESP32コードの大きな問題であった「シリアルポートから長文データを受け取って保存する機能がない」点が、以下のロジック追加によって解消されています。

// #### 1. 長文バイナリデータの受信と更新

// * **受信方法の変更**: `loop()` 関数内で、`Serial.readStringUntil('\n')` を使用しています。これは、PC3の`tennji_serverBa.pde`がデータ送信の終端として付加している**改行コード (`\n`)** を検出するまで、シリアルポートからのデータをすべて読み込むことを意味します。これにより、長文の点字バイナリ文字列（例: `"100000110000..."`）を一度にまとめて受信できるようになりました。
// * **データ格納**: 受信したデータが長文である場合、`receivedBrailleData` 変数が新しいバイナリ文字列で上書きされます。
// * **初期化**: 新しいデータを受信した際、表示開始位置 (`currentStartIndex`) が `0` にリセットされるため、必ず文章の**最初から点字が表示**されます。

// #### 2. ページングコマンド（制御信号）の分離

// * **コマンド識別**: 受信したデータの長さが1文字である場合 (`incomingData.length() == 1`) は、それを**ページングコマンド**（'n' または 'p'）として識別しています。
// * **動作**: コマンドが 'n' または 'p' であった場合、`receivedBrailleData` の内容は更新されず、`currentStartIndex` の値のみが変更され、**次または前の点字ブロックを表示**するロジックが実行されます。

// この修正により、ESP32はPC3からのシリアル通信に対して、**新しい点字データ**と**ページ送りコマンド**の両方に正しく応答できる「シリアルデータ対応」のファームウェアになりました。

// ESP32の安全なGPIOピンに割り当てます。
const int Braille_Pins[][6] = {
    // 1文字目 (6ピン)
    {33, 25, 26, 27, 14, 12} // 設定ピンは環境に合わせて修正してください
};

const int NUM_CHARS = 1;    // 一度に表示する文字数 (1文字分)
const int PINS_PER_CHAR = 6;
const int TOTAL_PINS = NUM_CHARS * PINS_PER_CHAR;

// サーボ角度
const int ANGLE_OFF = 0;  // ピンが下がっている状態
const int ANGLE_ON = 45; // ピンが上がっている状態

// =======================================================
// 2. グローバル変数
// =======================================================

Servo servos[TOTAL_PINS];

// PC3から受信する長文バイナリデータ (例: "100000110000...") を格納
String receivedBrailleData = "";
int currentStartIndex = 0; // 現在表示中のデータの開始位置
const int BAUD_RATE = 115200; // PC3のtennji_serverBa.pde と一致させる

// --------------------------------------------------------
// 3. 初期設定 setup()
// --------------------------------------------------------

void setup() {
    Serial.begin(BAUD_RATE);

    // サーボピンの初期化
    for (int c = 0; c < NUM_CHARS; c++) {
        for (int p = 0; p < PINS_PER_CHAR; p++) {
            int servoIndex = c * PINS_PER_CHAR + p;
            servos[servoIndex].attach(Braille_Pins[c][p]);
            servos[servoIndex].write(ANGLE_OFF); // 初期状態はピンを下げる
        }
    }

    // 互換性のため、元のテストデータを初期値として設定
    const char* const TEST_DATA_RAW = "100000110000100100110100010100100001110001100101110101010101";
    receivedBrailleData = String(TEST_DATA_RAW);
    Serial.println("ESP32 Braille Device Initialized.");
}

// --------------------------------------------------------
// 4. 点字ピン表示関数
// --------------------------------------------------------

void displayBrailleChar(int charIndex, String signal) {
    // サーボを制御し、信号に基づいてピンを上下させる
    for (int p = 0; p < PINS_PER_CHAR; p++) {
        int servoIndex = charIndex * PINS_PER_CHAR + p;

        int targetAngle = (signal.charAt(p) == '1') ? ANGLE_ON : ANGLE_OFF;
        servos[servoIndex].write(targetAngle);
        delay(1); // サーボ動作のための短いディレイ
    }
}

// --------------------------------------------------------
// 5. メインループ loop()
// --------------------------------------------------------

void loop() {
    
    // 5.1. シリアルデータ受信処理 (PC3からの新規データ受信/ページングコマンド)
    if (Serial.available() > 0) {
        // PC3のProcessing Serverが改行コード('\n')を付けてデータまたはコマンドを送信することを想定
        String incomingData = Serial.readStringUntil('\n'); 

        if (incomingData.length() > 0) {
            incomingData.trim(); // 前後の空白文字を削除

            if (incomingData.length() == 1) {
                // データの長さが1文字の場合はページングコマンドと見なす
                char command = incomingData.charAt(0);
                int totalChars = receivedBrailleData.length() / PINS_PER_CHAR;

                if (command == 'n' || command == 'N') {
                    // 次のページへ
                    if (currentStartIndex + NUM_CHARS < totalChars) {
                        currentStartIndex += NUM_CHARS;
                        Serial.println("Page Forward (N).");
                    }
                }
                else if (command == 'p' || command == 'P') {
                    // 前のページへ
                    if (currentStartIndex > 0) {
                        currentStartIndex -= NUM_CHARS;
                        Serial.println("Page Backward (P).");
                    }
                }
            } else {
                // 長文の場合は新しい点字データと見なす
                // 6の倍数の長さか確認
                if (incomingData.length() % PINS_PER_CHAR == 0) { 
                    receivedBrailleData = incomingData;
                    currentStartIndex = 0; // 新しいデータを受信したら必ず先頭から表示
                    Serial.print("New Data Received. Total Chars: ");
                    Serial.println(receivedBrailleData.length() / PINS_PER_CHAR);
                } else {
                    Serial.print("ERROR: Invalid data length received. Length: ");
                    Serial.println(incomingData.length());
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