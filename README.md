
---

# PC2

## 画像受信・OCR・点字信号変換サーバー ドキュメント(説明されているファイル以外は無視してね☺)

本ドキュメントは、PC2 における **役割・環境構築・スクリプト仕様・実行フロー** をまとめたものです。
PC2 は、**画像受信 → OCR → テキスト整形 → 点字信号生成** を担う中核サーバーです

---

## PC2 の役割

PC2 は、本システム内で次の処理を担当します。

1. **画像受信**
   PC1（撮影端末）から送られてくる画像データを Processing (ここではVSCode環境を使用)により受信。
2. **OCR処理**
   受信した画像を `yomitoku` で OCR して Markdown 形式のテキストを生成。
3. **データ変換**
   Python スクリプト（`conversion/md_to_binary2.py`）で
   Markdown → テキスト整形 → ひらがな変換 → 点字信号（6bit）に変換。
4. **信号送信**
   作成した点字信号を PC3（ESP32 制御PC）へ渡す。

---

## システムフロー（PC2 が担当する処理）

1. **画像受信**（Processing / `processing/client.pde`）
2. **OCR処理**（yomitoku）
3. **テキスト整形・ひらがな化・点字信号変換**（Python）
4. **PC3への信号転送**

---

## 必要環境

### ソフトウェア

* OS: Windows
* Python 3.8 以上
* Processing 4.3.4(最新バージョンだと動作しないよ！気をつけてね☺参考サイト:https://qiita.com/Hutaba-Makura/items/a7e49b6b43633fa5b2e5)
* OCRエンジン: yomitoku

### Pythonライブラリ

```bash
pip install pykakasi opencv-python
# yomitoku の依存関係も別途インストールが必要
```

---

## ファイル構成

```
PBL_imgproc2/
│
├── conversion/
│   ├── md_to_binary2.py      # [主要] 点字信号変換スクリプト
│   └── md_to_hiragana.py     # 補助モジュール
│
├── processing/
│   └── client.pde            # [主要] 画像受信サーバー
│
├── imgs/                     # OCR結果(.md)や画像を保存
│   └── received.png          # 受信画像
│
└── yomitoku/                 # OCR エンジン
```

---

## 各スクリプトの詳細

### ### 1. 画像受信サーバー（`client.pde`）

PC1 からの画像データを受信し保存する Processing スケッチ。

**主な機能**

* TCP ポート **5554** でサーバー待機
* クライアント接続後、**画像サイズ（高さ・幅）** のヘッダを受信
* RGB 生データを受信し `imgss/received.png` として保存
* GUI に受信ステータスを表示
* VSCode から実行する運用を想定

---

### 2. 点字信号変換スクリプト（`md_to_binary2.py`）

OCR 結果（Markdown）を解析し、ESP32 用の **6bit 点字信号列** に変換。

**主な機能**

* Markdown クリーニング
* 文字列を **ひらがな** に変換（pykakasi）
* 各文字を点字規則に従って **6bit のバイナリ**（例: `100000`※"あ"を表す）に変換
* 変換結果を標準出力へ出力

**使用方法**

```bash
python conversion/md_to_binary2.py results/received.md
```

---

## 実行手順

### **Step 1: PC2で画像受信サーバー起動**

VSCode で `test.pde` を開き、実行(Ctrl + Shift + B)。
緑色の待受画面が表示され、PC1 からの接続を待つ。

---

### **Step 2: PC1 から画像が送信される**

PC1 の `camera_capture_save.py` と Processing クライアントが動作すると、
PC2 の画面に画像が表示され、`imgss/received.png` に保存される。

---

### **Step 3: OCR → 点字信号変換**

#### ● OCR（yomitoku）

```bash
// yomitoku単体での動作時
yomitoku received.png -f md -o results
```

#### ● 点字信号生成

```bash
python conversion/md_to_binary2.py imgs/received.md
```

---

### **Step 4: 出力確認**

ターミナルに次のような 6bit の点字コード列が表示される：

```
"100000110000100100 ..."
```

これが **ESP32 へ送信されるデータ**。

---

## 注意事項・課題

* **濁点・半濁点の処理**は `md_to_binary2.py` の TODO にあり、改良中
* **は(wa) / へ(e) の文脈変換**も未実装
* 現状、Processing の受信完了と OCR 開始は **手動 or ファイル監視**で連携

---

必要であれば、
* 自動化用のバッチスクリプト
* test.pde や md_to_binary2.py のレビュー

も作成可能
