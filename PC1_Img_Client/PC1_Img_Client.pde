import processing.net.*; //ネットワークライブラリの使用宣言

Client   myClient; //クライアントクラスclientの宣言
String[] FileName = new String[4]; //画像ファイル名を格納する文字列配列
String[] Message  = new String[2];  //メッセージ用文字列

PImage[] img = new PImage[4]; //イメージ型配列imgを宣言

int state = 0;

void setup( ){ // 初期設定関数

  size( 500, 200 ); // ウィンドウを生成(横400,縦200)

  // 日本語フォント(BIZ UDゴシック)で、サイズ16のフォントを生成
  PFont font = createFont("BIZ UDゴシック", 16, true);
  textFont(font); // 生成したフォントを設定

  // サーバーに接続
  myClient = new Client( this, "localhost", 5554 );

  // 画像ファイルを読み出す。
  for( int i = 0; i < 1; i++ ){
    FileName[i] = "test1" + ".png";
    img[i] = loadImage(FileName[i]);
  }

  Message[0] = Message[1] = " "; //メッセージの初期値
}

void draw( ) //画面描画(100ms毎に起動)
{
  background(#2D3986); //青に塗りつぶす．

  //左上に"クライアントA"と状態の表示
  text( "クライアント " + myClient.ip(), 30, 20 );
  text( "状態 " + state, 30, 40 );
  text( Message[1]     , 30, 60 );
}

//*******************************************************************************
//データを受信したら起動される関数(引数は送信先の情報)
//*******************************************************************************
int    numImg    = 0; //画像番号
int    ImgHeight = 0;
int    ImgWidth  = 0;
byte[] SendImgData;
void clientEvent(Client c){

  int NumBytes = 0;

  switch( state ){
    //---------------------------------------------------------------------------------
    case 0 : //画像の高さと幅の送信
    //---------------------------------------------------------------------------------

      NumBytes = c.available( );

      if( NumBytes >= 1 ){

        c.clear( ); //受信バッファを空にする。

        //画像の高さと幅を送信(それぞれint型4バイト)
        ImgHeight = img[numImg].height;
        ImgWidth  = img[numImg].width;
        byte[] SendHW = new byte [8]; //送信用バッファ

        //画像の高さを送信バッファに詰める。
        SendHW[0] = (byte) ImgHeight;
        SendHW[1] = (byte)(ImgHeight >>  8);
        SendHW[2] = (byte)(ImgHeight >> 16);
        SendHW[3] = (byte)(ImgHeight >> 24);
        //画像の幅を送信バッファに詰める。
        SendHW[4] = (byte) ImgWidth;
        SendHW[5] = (byte)(ImgWidth >>  8);
        SendHW[6] = (byte)(ImgWidth >> 16);
        SendHW[7] = (byte)(ImgWidth >> 24);

        myClient.write(SendHW); //バッファをサーバに送信
        state = 1; //状態遷移
      }
      break;

    //---------------------------------------------------------------------------------
    case 1 : //画像データの送信
    //---------------------------------------------------------------------------------
      NumBytes = c.available( );

      if( NumBytes >= 1 ){

        c.clear( ); //受信バッファを空にする。

        //送信バッファの動的確保(総画素数×RGBの3バイト分)
        SendImgData = new byte [ImgWidth * ImgHeight * 3];
        int idx = 0;
        //画像データを全部、送信バッファに詰め込む。
        for(int i = 0; i < ImgWidth * ImgHeight; i++ ){
          color pix = img[numImg].pixels[i];//画像データから1画素を取り出す。
          SendImgData[idx+0] = (byte)red  (pix); //画素の赤成分を送信バッファに詰める。
          SendImgData[idx+1] = (byte)green(pix); //画素の緑成分を送信バッファに詰める。
          SendImgData[idx+2] = (byte)blue (pix); //画素の青成分を送信バッファに詰める。
          idx += 3;
        }
        myClient.write(SendImgData); //送信バッファをサーバに送信

        state = 2; //状態遷移
      }
      break;

    //---------------------------------------------------------------------------------
    case 2: //サーバーから画像データの受信完了が来るまで待つ
    //---------------------------------------------------------------------------------
    NumBytes = c.available();

    if( NumBytes >= 1 ){
      c.clear( ); //受信バッファを空にする。
      Message[1] =  FileName[numImg] + " : 画像送信の完了 " + SendImgData.length + "[バイト]";
      numImg++;
      state = 0;
    }

    break;
  }

  if( numImg >= 4 ) numImg = 0;
}