// 2025/12/07/18:12現在の最新版

import processing.net.*; //ネットワークライブラリの使用宣言
// import processing.serial.*; // シリアルはPC3で処理するため不要

final int MAX_CLIENT = 2;
Server   myServer;
String[] Message = new String[3];
int      state   = 0;
PImage   RecvImg; 

// --- 追加 ---
final String TEMP_IMAGE_PATH = "C:/Users/syuuu/workspace/PBL_imgproc2/temp_image.jpg"; 
final String PYTHON_SCRIPT_PATH = "C:/Users/syuuu/workspace/PBL_imgproc2/automation/pc2_ocr_converter.py";
final String PYTHON_EXE_PATH = "C:/Users/syuuu/AppData/Local/Programs/Python/Python310/python.exe"; 
// ------------

void setup()
{
  size( 860, 580 );
  
  PFont font = createFont("BIZ UDゴシック", 16, true);
  textFont(font);

  //サーバの起動 (ポート番号は5554)
  myServer = new Server(this, 5554); //
  
  Message[0] = "サーバ： " + myServer.ip( );
  Message[1] = "待機中...";
  Message[2] = " ";
}
// ... (draw, stop 関数はそのまま) ...

// networkEvent 関数内の state=1 ブロックを修正
void networkEvent( Server ConServer, Client RecvClient ) 
{
  // ... (state=0 のヘッダー受信処理はそのまま) ...
    
    //--------------------------------------------------------------------------------------------------
    case 1 : // 画像データの受信(総画素数×RGBの3バイト)
    //--------------------------------------------------------------------------------------------------
      int NumBytes = RecvClient.available( ); //受信データのバイト数を確認
    
      if( NumBytes >= ImgHeight * ImgWidth * 3 ){ //全画像データ(RGB×高さ×幅)を受信したら
        
        Message[2] += " => 受信完了: " + NumBytes + "[バイト]";
        
        byte[] TmpBuff = RecvClient.readBytes(NumBytes);//受信バッファ内の全画像データを読み出す。
        
        //画像を格納するメモリ領域を確保
        RecvImg = createImage(ImgWidth, ImgHeight, RGB);
        int idx = 0;
        
        // 受信したRAW RGBデータをPImageに変換
        for(int y = 0; y < ImgHeight; y++ ){
          for(int x = 0; x < ImgWidth; x++ ){
             RecvImg.pixels[y * ImgWidth + x] = color(TmpBuff[idx+0] & 0xFF, TmpBuff[idx+1] & 0xFF, TmpBuff[idx+2] & 0xFF);
             idx += 3;
          }
        }
        
        RecvImg.updatePixels();

        // --- 追加ロジック: 画像をファイルに保存し、Pythonスクリプトを起動 ---
        RecvImg.save(TEMP_IMAGE_PATH);
        Message[1] = "画像保存: " + TEMP_IMAGE_PATH;
        
        // Python OCR/変換スクリプトを非同期で実行
        try {
           // exec() を使用して Python スクリプトを実行
           // ProcessBuilder を使って実行するとより安定
           ProcessBuilder pb = new ProcessBuilder(PYTHON_EXE_PATH, PYTHON_SCRIPT_PATH);
           pb.directory(new File("C:/Users/syuuu/workspace/PBL_imgproc2")); // プロジェクトルートをワーキングディレクトリに設定
           pb.start();
           Message[1] += " | Python実行中...";
        } catch (IOException e) {
           Message[1] = "ERROR: Pythonスクリプト実行失敗: " + e.getMessage();
        }
        // -------------------------------------------------------------------
        
        state = 0; // 状態をリセットし、次のヘッダー受信を待機
      }
      
      break;
}