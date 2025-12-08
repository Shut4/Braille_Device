import processing.serial.*;
from

// --- シリアル設定 ---
Serial controlPort;
final String PORT_NAME = "COM5"; // AE-FT234X-ISOが割り当てられたポート名に修正
final int BAUD_RATE = 115200;

String statusMessage = "Initializing...";
String testBrailleData = "100000110000100100110100010100100001110001100101110101010101"; // テストデータ

void setup() {
  size(400, 200);
  PFont font = createFont("BIZ UDゴシック", 16, true);
  textFont(font);

  // シリアルポートの初期化
  try {
    controlPort = new Serial(this, PORT_NAME, BAUD_RATE);
    statusMessage = "Connected to ESP32 via " + PORT_NAME;
  } catch (Exception e) {
    statusMessage = "ERROR: シリアルポート接続失敗。ポートを確認してください。";
    println(e);
  }
}

void draw() {
  background(#4A90E2);
  fill(255);
  text("PC3: AE-FT234X シリアル制御", 20, 30);
  text("Status: " + statusMessage, 20, 60);
  text("Press 'T' to Send Test Data. Use 'N'/'P' for paging.", 20, 90);
}

void keyPressed() {
  if (controlPort == null) {
    statusMessage = "ERROR: Port not open.";
    return;
  }
  
  // TキーでバイナリテストデータをESP32に送信 (データ格納用)
  if (key == 't' || key == 'T') {
    controlPort.write(testBrailleData);
    controlPort.write('\n'); // 終端文字
    statusMessage = "Sent NEW DATA ('T'). Total Chars: " + testBrailleData.length() / 6;
  }
  
  // Nキーで次のページコマンドを送信
  else if (key == 'n' || key == 'N') {
    controlPort.write('n');
    statusMessage = "Sent 'N' (Next Page) command.";
  }
  // Pキーで前のページコマンドを送信
  else if (key == 'p' || key == 'P') {
    controlPort.write('p');
    statusMessage = "Sent 'P' (Previous Page) command.";
  }
}