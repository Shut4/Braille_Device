import processing.net.*; //ネットワークライブラリの使用宣言

Client   myClient; //クライアントクラスclientの宣言
String[] FileName = new String[4]; //画像ファイル名を格納する文字列配列
String[] Message  = new String[2];  //メッセージ用文字列

PImage[] img = new PImage[4]; //イメージ型配列imgを宣言

int state = 0;
int numImg = 0; // 送信する画像のインデックス (0番目の画像 'test1.png' を送信)

void setup( ){ // 初期設定関数

  size( 500, 200 ); // ウィンドウを生成

  PFont font = createFont("BIZ UDゴシック", 16, true);
  textFont(font); // 生成したフォントを設定

  // サーバーに接続 (PC2のIPアドレスとポート5554に修正)
  // !!! PC2の実際のIPアドレスに修正してください !!!
  myClient = new Client( this, "192.168.1.10", 5554 );

  // 画像ファイルを読み出す。
  // 送信したい画像ファイル (test1.pngなど) はこのスケッチのデータフォルダに配置
  for( int i = 0; i < 1; i++){
    FileName[i] = "test1" + ".png";
    img[i] = loadImage(FileName[i]);
    if (img[i] == null) {
      println("ERROR: " + FileName[i] + " ファイルが見つかりません。");
    }
  }
  
  Message[0] = Message[1] = " "; //メッセージの初期値
  Message[0] = "PC1: クライアント起動。'test1.png' を送信準備完了";
}

void draw( ) //画面描画(100ms毎に起動)
{
  background(#2D3986); //青に塗りつぶす．
  
  text(Message[0] + " :状態 " + state, 30, 30);
  text(Message[1], 30, 60); 

  if (myClient.active() && state == 0) {
      Message[1] = "PC2と接続完了。送信を開始します。";
      // 最初の状態遷移をトリガー
      networkEvent(myClient); 
  }
}

void clientEvent(Client c){ // クライアント接続時に起動されるイベント
  
  int ImgHeight = img[numImg].height;
  int ImgWidth  = img[numImg].width;
  
  switch( state ){
    //---------------------------------------------------------------------------------
    case 0 : //高さと幅の送信
    //---------------------------------------------------------------------------------
      c.write(ImgHeight); //画像の高さを送信
      c.write(ImgWidth);  //画像の幅を送信
      
      Message[1] = "ヘッダー送信: H=" + ImgHeight + ", W=" + ImgWidth;
      state = 1; //状態遷移
      break;
      
    //---------------------------------------------------------------------------------
    case 1 : //画像データの送信
    //---------------------------------------------------------------------------------
      int NumBytes = c.available( ); 
       
      if( NumBytes >= 1 ){ // PC2からACK (1) を受信したら
         
        c.clear( ); //受信バッファを空にする。
        
        //送信バッファの動的確保(総画素数×RGBの3バイト分)
        byte[] SendImgData = new byte [ImgWidth * ImgHeight * 3];
        int idx = 0;
        
        // 画像データを全部、送信バッファに詰め込む。(RGB形式)
        img[numImg].loadPixels();
        for(int i = 0; i < ImgWidth * ImgHeight; i++ ){
          color pix = img[numImg].pixels[i];
          SendImgData[idx+0] = (byte)red  (pix); 
          SendImgData[idx+1] = (byte)green(pix); 
          SendImgData[idx+2] = (byte)blue (pix); 
          idx += 3;  
        }
        myClient.write(SendImgData); //送信バッファをサーバに送信
       
        state = 2; //状態遷移
        Message[0] = "✅ 画像送信完了。次のページへ進んでください。";
      }
      break;
      
    //---------------------------------------------------------------------------------
    case 2 : // 終了
    //---------------------------------------------------------------------------------
      // 画像送信が完了し、次のページの手動操作を待つ
      break;
  }
}