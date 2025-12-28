
---

# 点字デバイス

![完成理想図](device.png)

## 画像受信・OCR・点字信号変換サーバー ドキュメント

本ドキュメントは、 点字デバイス作成における、**役割・環境構築・スクリプト仕様・実行フロー** をまとめたものです。このデバイス開発において、現段階では、Processingを使用したかったので、PCを3台(PC1,PC2,PC3)意図的に使用しています。それぞれの役割に関して、

* PC1: 画像撮影 → 画像送信(Processing: △△△)
* PC2: 画像受信(Processing: PC2_processing_Server.pde) →
 OCR処理(yomitoku) → テキスト整形(conversion/md_to_binary.py) → バイナリ点字信号生成(conversion/md_to_binary.py)
 ※以降点字信号と呼ぶ
  → 点字信号送信(Processing: PC2_processing_Tenji_Server.pde)
* PC3: 点字信号受信(Processing: △△△) → ESP32へシリアル通信により点字信号送信
* ESP32: PC3から点字信号受信 → 点字信号を元にしてarduinoIDEによって書き込まれたコードから点字ピンの出力制御

---
## PC1 の役割
PC1 は、本システム内で以下の処理を担当する
1. **画像撮影**
   Pythonスクリプト(`PC1_camera_png.py`)で、ディレクトリ(`imgs/captured_images`)に`test1.png`としてpng形式で保存する。
2. **画像送信**
   撮影した画像データを Processing (ここではVSCode環境を使用)によりPC2へ送信。


## PC2 の役割
PC2 は、本システム内で以下の処理を担当する
1. **画像受信**
   PC1（撮影端末）から送られてくる画像データを Processingにより受信。
2. **OCR処理**
   受信した画像を `yomitoku` で OCR処理し、 Markdown形式のテキストを生成。
3. **テキスト整形・バイナリ点字信号生成**
   Python スクリプト（`conversion/md_to_binary.py`）で
   Markdown → テキスト整形 → ひらがな変換 → 点字信号（6bit * 文字数分）に変換。
4. **信号送信**
   作成した点字信号をProcessingにより、PC3(ESP32 制御PC)へ渡す。


## PC3 の役割
PC3 は、本システム内で以下の処理を担当する
1. **点字信号受信**
   ProcessingによりPC2から点字信号を受信する
2. **ESP32へシリアル通信により点字信号送信**
   PC3とUSB接続されているESP32へ点字信号を文字列形式で送信する。


## ESP32の役割
ESP32 は、本システム内で以下の処理を担当する
1. **点字信号受信**
   シリアル通信により、PC3から点字信号を文字列形式で受信する。
2. **点字ピンの出力制御**
   arduinoIDEによってESP32に書き込まれたコードが受信した点字信号を元にして、点字ピンの出力を制御する。

---

## 必要環境

### ソフトウェア

* OS: Windows
* Python 3.8 以上
* Processing 4.3.4(最新バージョンだと動作しないので気をつけてください。
参考サイト:https://qiita.com/Hutaba-Makura/items/a7e49b6b43633fa5b2e5)
* OCRエンジン: yomitoku

### Pythonライブラリ

```bash
pip install pykakasi opencv-python
# yomitoku の依存関係も別途インストールが必要
```

---

## ファイル構成(動作に必要なもののみ記載)
※2025-12-28時点ではPC1,PC3のProcessingコードはProcessing IDE上で動作させているため、ここに記載できていません

```
PBL_imgproc2/
│
├── conversion/
│   └── md_to_binary.py                      # [主要] 点字信号変換スクリプト
│
├── PC1_Img_Client/
│   └── PC1_Img_Client.pde                   # [主要] PC1画像送信クライアント(未記載:2025-12-28)
│
├── PC2_processing_Server/
│   └── PC2_processing_Server.pde            # [主要] PC2画像受信サーバー
│
├── PC2_processing_Tenji_Server/
│   └── PC2_processing_Tenji_Server.pde      # [主要] PC2バイナリ点字信号送信サーバー
│
├── PC3_Tenji_Client/
│   └── PC3_Tenji_Client.pde                 # [主要] PC3バイナリ点字信号受信クライアント(未記載:2025-12-28)
│
├── imgs/captured_images
│   └── received.png                         # PC1で撮影した画像をPC2が受信した際に保存される場所
│
├── results/
│   └── PBL_imgproc2_test_p1.md              # OCR処理結果
│
└── yomitoku/                                # OCR エンジン
```

---

## 実行手順(修正中: 2025-12-28時点)

### **Step 1: 画像撮影(PC1)**
右上の実行ボタン ▷ から`PC1_camera_png.py`を実行し、画像が`imgs/captured_imagesにtest1.pngとして保存される`

---

### **Step 2: 画像受信サーバー起動(PC2)**
VSCode で `PC2_processing_Server.pde` を開き、実行(Ctrl + Shift + B)。
緑色の待受画面が表示され、PC1 からの接続を待つ。

---

### **Step 3: 画像送信サーバ起動(PC1)**
Processing IDE で `PC1_Img_Client.pde` を開き、実行する。

---

### **Step 4: 画像データ送信(PC1)**
PC1 のProcessingクライアントが動作すると、PC2 の画面に画像が表示され、`PC2_processing_Server/received_imgs` に保存される。

---

### **Step 5: OCR → 点字信号変換(PC2)**

### ●OCR処理（yomitoku）
ターミナルにて以下を入力
```bash
yomitoku C:\Users\syuuu\workspace\PBL_imgproc2\PC2_processing_Server\received_imgs\test1.png -f md -o results -v --figure
```
上記により、処理結果として、マークダウン形式`results/PBL_imgproc2_test1_p1.md`で保存される。


### ●点字信号変換（`conversion/md_to_binary.py`）
ターミナルにて以下を入力
```bash
python conversion/md_to_binary.py　results/PBL_imgproc2_test1_p1.md
```
上記により不要な記号の削除、純粋なひらがなへの変換が行われ、最終的に対応したバイナリ信号(文字列)に変換される。

VSCodeターミナル上に、次のような 6bit * 文字数分の長さの点字コード列が表示される：

```
"100000110000100100 ..."
```
これが **ESP32 へ送信されるデータ**。

---

### **Step 6: ESP32コードのコンパイル・書き込み(ESP32)**
ESP32にsrduino IDEで、`ESP32_dec26.ino`をコンパイルして書き込む。

---

### **Step 7: バイナリ点字信号送信サーバー起動(PC2)**
VSCode で `PC2_processing_Tenji_Server,pde` を開き、実行(Ctrl + Shift + B)。
緑色の待受画面が表示され、PC3 からの接続を待つ。

---

### **Step 8: バイナリ点字信号受信クライアント起動(PC3)**
Processing IDE で `PC3_Tenji_Client.pde` を開き、実行する。

---

### **Step 9: バイナリ点字信号送信(PC2)**
PC2 のProcessingサーバが動作すると、PC3 のProcessingクライアントがバイナリ点字信号を受信する。その後、受信データをもとにしてピン制御が行われる。用意している点字ピンの数によって、一度に表示できる点字の数が異なり、「次へボタン」「戻るボタン」を使用することで前後の点字を表示することができます。電光掲示板の点字ver.のようなイメージ。

---

## 注意事項・課題

* **濁点・半濁点の処理**は改良中(2025-12-28時点)
* **は(wa) / へ(e) の文脈変換**も未実装
* 2025-12-28時点では、Processing の受信完了と OCR 開始は **手動**で連携
* カメラで画像を撮影すると、点字が出力されるように自動化中
* 

---

# Changelog

## 2025-12-07

### Changed
- 外部ライブラリのインストール手順を更新
  - 新たに以下のライブラリを追加
    - `opencv-python`
    - `janome`
    - `pyserial`

### Notes
- ライブラリは以下のコマンドでインストール可能:
```bash
pip install opencv-python janome pyserial
```

## 2025-12-08
### Notes
- 一連の動作に関して手順を確認した。※PC3のシリアル通信手前まで
   - PC1_camera_png.pyで画像(data/test1.png)を撮影(PC1)
   - Processingコード(VSCode環境のPC2_processing_Server.pde)を実行(Ctrl+Pから選択)し待機。(PC2)
   - 撮影した画像をProcessingコード(PC1_Img_Client.pde)によりPC2へ送信(PC1)
   - 撮影した画像データを入力としてyomitokuを実行(PC2)。ターミナルに以下を入力する。
   ```bash
   yomitoku C:\Users\syuuu\workspace\PBL_imgproc2\PC2_processing_Server\received_imgs\test1.png -f md -o results -v --figure
   ```
   - yomitokuのOCR処理で生成されたresults/received_imgs_test1_p1.mdをもとにして、バイナリ文字列に変換する。
   ```bash
   python conversion/md_to_binary.py results/received_imgs_test1_p1.md
   ```
   ※上記に関して、現在はPC2からPC3へ文字列(final_binary_string)を渡すコードを追加したファイルを作成中...(md_to_binary2.py)


## 2025-12-26
### Notes
- PC3のProcessingコード(client)から、シリアル通信を経て、ESP32へデータ送信可能となった。
(VSCode環境のPC2_processing_Tenji_Server.pde起動→ProcessingIDEのtenji_clientBa.pde起動→sketch_dec26bを書き込み、成功)
