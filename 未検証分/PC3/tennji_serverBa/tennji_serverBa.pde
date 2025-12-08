// 2025/12/07/18:12現在の最新版

import processing.net.*; // ネットワークライブラリの使用宣言
import processing.serial.*; // シリアルライブラリを追加

Server   myServer; 
Serial   controlPort; // シリアルポートの宣言
String[] SendMsg = new String[3]; 
String RecvMsg; 

// --- シリアル設定 ---
final String PORT_NAME = "COM5"; // AE-FT234X-ISOが割り当てられたポート名に修正
final int BAUD_RATE = 115200; // ESP32側の設定に合わせる (例: 9600, 115200)

void setup()
{
  size( 400, 200 );
  
  PFont font = createFont("BIZ UDゴシック", 16, true);
  textFont(font); 

  // 1. ネットワークサーバーの起動 (ポート番号は12345)
  myServer = new Server(this, 12345); //
  
  // 2. シリアルポートの初期化
  try {
    controlPort = new Serial(this, PORT_NAME, BAUD_RATE);
    RecvMsg = "Server: Port " + PORT_NAME + " Ready.";
  } catch (Exception e) {
    RecvMsg = "ERROR: シリアルポート接続失敗。";
    println(e);
  }
}
// ... (stop, draw 関数はそのまま) ...

// networkEvent 関数を削除し、clientEvent でデータ受信処理を行う
void clientEvent(Client client) 
{ 
  int NumBytes = client.available();
  
  if (NumBytes > 0) {
    // Pythonスクリプトはデータ末尾に '\n' を付加して送信しているため、readStringUntil('\n')を使用
    String receivedBinary = client.readStringUntil('\n'); 
    
    if (receivedBinary != null) {
      receivedBinary = receivedBinary.trim(); 
      
      if (receivedBinary.length() > 0) {
        // --- シリアル送信ロジック ---
        if (controlPort != null) {
          controlPort.write(receivedBinary);
          controlPort.write('\n'); // ESP32側でデータの区切りとして利用できるよう改行コードを付加
          
          RecvMsg = "✅ Received & Sent: " + receivedBinary.substring(0, min(receivedBinary.length(), 20)) + "...";
        } else {
          RecvMsg = "❌ Received, but Serial Port not initialized.";
        }
      }
    }
  }
}

// 既存の mousePressed イベントは、テストやデバッグ用としてそのまま残します
// int numSendMsg = 0;
// void mousePressed...