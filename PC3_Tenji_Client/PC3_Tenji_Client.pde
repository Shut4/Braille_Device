import processing.net.*; //ネットワークライブラリの使用宣言
import processing.serial.*;

Client   myClient; //クライアントクラスclientの宣言
Serial myport;
String[] SendMsg = new String[3]; //送信文字列の配列
String RecvMsg;  //受信メッセージ用文字列
ArrayList<StringList> twoDList = new ArrayList<StringList>(); // 二次元リスト

int selectedI = 0;
int selectedJ = 0;
//******************************************************************************
// 初期設定関数
//******************************************************************************
void setup( ){

  size( 800, 300 ); // ウィンドウを生成(横400,縦200)

  // 日本語フォント(BIZ UDゴシック)で、サイズ16のフォントを生成
  PFont font = createFont("BIZ UDゴシック", 16, true);
  textFont(font); // 生成したフォントを設定
  println(Serial.list());
  // サーバーに接続
  myClient = new Client( this, "localhost", 12345 );
  myport = new Serial(this, "COM3", 9600);

  RecvMsg = " "; //メッセージの初期値
}

void draw( ) //画面描画(100ms毎に起動)
{
  background(#2D3986); //青に塗りつぶす．

  //左上にクライアントと自分のIPアドレスを表示
  text( "クライアント: " + myClient.ip(), 30, 20 );

  //受信文字列を表示
  text(RecvMsg, 30, 60 );

}

//*******************************************************************************
//ネットワーク経由でデータを受信したら起動される関数(引数は送信先の情報)
//*******************************************************************************
void clientEvent(Client c){

  int NumBytes = 0;

  NumBytes = c.available( ); //受信データがあるか確認

  if( NumBytes >= 1 ){ //受信データがあったら
    String recv = c.readString().trim(); //文字列を受信バッファから取り出す．

    myport.write(recv);
    myport.write('\n');
  }
}

//******************************************************************************
// マウスのボタンが押されたら起動される関数
//******************************************************************************
int numSendMsg = 0;
void mousePressed( )
{
  //サーバに文字列を送信
  myport.write("101010\n");
  println("SEND TO ESP32");
}