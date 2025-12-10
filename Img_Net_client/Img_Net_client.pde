import processing.net.*; //ネットワークライブラリの使用宣言
import java.io.File; // ファイル操作のために追加

Client   myClient; 
String[] Message  = new String[2];  

PImage   imgToSend; // 送信画像を保持する変数
// !!! 以下のパスは、Pythonスクリプトと連携する絶対パスに修正してください !!!
String   ImageFilePath = "C:/Users/syuuu/workspace/PBL_imgproc2/captured_image.png"; 
String   TriggerFilePath = "C:/Users/syuuu/workspace/PBL_imgproc2/SEND_TRIGGER.txt"; 

int state = 0;
int ImgHeight = 0;
int ImgWidth  = 0;
byte[] SendImgData; // 送信データバッファ


void setup( ){ // 初期設定関数
  
  size( 500, 200 ); 
  
  // 日本語フォント(BIZ UDゴシック)で、サイズ16のフォントを生成
  PFont font = createFont("BIZ UDゴシック", 16, true);
  textFont(font); 

  // サーバーに接続 (PC2のIPアドレスとポート5554に修正)
  // !!! IPアドレスをPC2に修正、または '127.0.0.1' に修正 !!!
  myClient = new Client( this, "127.0.0.1", 5554 ); 
  
  Message[0] = Message[1] = " "; 
  Message[0] = "PC1: 接続完了。撮影を待っています...";
}

void draw( ) //画面描画(100ms毎に起動)
{
  background(#2D3986); 
  
  // クライアントIPと状態の表示
  text( "クライアント " + myClient.ip(), 30, 20 );
  text( "状態 " + state, 30, 40 );
  text( Message[1], 30, 60 ); 

  // ----------------------------------------------------
  // --- 自動送信のトリガーロジック (状態 0 で実行) ---
  // ----------------------------------------------------
  if (myClient.active() && state == 0) {
      File triggerFile = new File(TriggerFilePath);
      
      // トリガーファイルが存在する場合 (Pythonが撮影を完了した)
      if (triggerFile.exists()) {
          Message[0] = "PC2と接続完了。送信トリガー検出！";
          
          // 1. Pythonが保存した最新の画像を読み込む
          imgToSend = loadImage(ImageFilePath); 
          
          if (imgToSend != null) {
              
              // 2. 送信シーケンスの開始 (ヘッダー送信)
              ImgHeight = imgToSend.height;
              ImgWidth  = imgToSend.width;
              
              byte[] SendHW = new byte [8];
              // 画像の高さと幅を送信バッファに詰める (元のロジック)
              SendHW[0] = (byte) ImgHeight;
              SendHW[1] = (byte)(ImgHeight >>  8);
              SendHW[2] = (byte)(ImgHeight >> 16);
              SendHW[3] = (byte)(ImgHeight >> 24); 
              SendHW[4] = (byte) ImgWidth;
              SendHW[5] = (byte)(ImgWidth >>  8);
              SendHW[6] = (byte)(ImgWidth >> 16);
              SendHW[7] = (byte)(ImgWidth >> 24);
              
              myClient.write(SendHW); // ヘッダーを送信 (state=0 の仕事はここまで)
              
              state = 1; // ACK待ちに遷移
              Message[1] = "ヘッダー送信: H=" + ImgHeight + ", W=" + ImgWidth;

          } else {
              Message[1] = "ERROR: 画像ファイルが見つからないか、読み込めません。";
          }
      } else {
          Message[1] = "PC2と接続済。[SPACE]キーによる撮影を待っています。";
      }
  }
}

//*******************************************************************************
// PC2からACKなどデータを受信したら起動される関数
//*******************************************************************************
void clientEvent(Client c){ 
  
  int NumBytes = c.available( );
  
  switch( state ){
    //---------------------------------------------------------------------------------
    case 0 : // (ヘッダー送信ロジックをdraw()に移動したため、ここはスキップ)
    //---------------------------------------------------------------------------------
      c.clear();
      break;
      
    //---------------------------------------------------------------------------------
    case 1 : //画像データの送信 (PC2からACK (1) を受信したら起動)
    //---------------------------------------------------------------------------------
      if( NumBytes >= 1 ){
          
        c.clear( ); //受信バッファを空にする。
        
        // --- 画像データ送信ロジック (元のロジック) ---
        SendImgData = new byte [ImgWidth * ImgHeight * 3];
        int idx = 0;
        
        imgToSend.loadPixels();
        for(int i = 0; i < ImgWidth * ImgHeight; i++ ){
          color pix = imgToSend.pixels[i];
          SendImgData[idx+0] = (byte)red  (pix); 
          SendImgData[idx+1] = (byte)green(pix); 
          SendImgData[idx+2] = (byte)blue (pix); 
          idx += 3;  
        }
        myClient.write(SendImgData); //送信バッファをサーバに送信
        
        state = 2; //状態遷移 (受信完了待ち)
        Message[0] = "✅ 画像データ送信完了。PC2からの受信完了を待っています。";
      }
      break;
      
    //---------------------------------------------------------------------------------
    case 2: //サーバーから画像データの受信完了 (ACK) が来るまで待つ
    //---------------------------------------------------------------------------------
      if( NumBytes >= 1 ){
        c.clear( ); //受信バッファを空にする。
        
        // --- トリガーファイル削除と状態リセット ---
        File triggerFile = new File(TriggerFilePath);
        if (triggerFile.exists()) {
            triggerFile.delete(); // 送信完了後にトリガーファイルを削除
        }

        Message[1] = "✅ PC2受信完了。次ページ準備完了。";
        state = 0; // 状態をリセットし、次の送信トリガーを待機
      }
      break;
  }
}

// ... (draw() 外の他の関数は元のコードのまま) ...