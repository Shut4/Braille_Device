import sys
import os
import time
import socket # ネットワーク通信に使用
import cv2
from janome.tokenizer import Tokenizer
import numpy as np


# 2025/12/07/18:12現在の最新版

# --------------------------------------------------------
# 既存ファイルのインポートのためのパス設定 (実行パスが automation フォルダ内の想定)
# --------------------------------------------------------
# ... (修正済みのパス設定ロジックをここに含める) ...
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    if project_root not in sys.path:
        sys.path.append(project_root)
    print(f"DEBUG: Correct Project root added to path: {project_root}")
except NameError:
    print("Warning: Could not determine script path for dynamic import setup.")


# --------------------------------------------------------
# OCR / conversion モジュールのインポートと代替ロジック (省略。全てここに含める)
# --------------------------------------------------------

# --- OCR モジュール設定 ---
OCR_IMPORTED = False
try:
    from yomitoku.ocr import OCR #
    YOMITOKU_CONFIG = "configs/yomitoku-text-detector-dbnet-open-beta.yaml"
    OCR_IMPORTED = True
except ImportError:
    print("Warning: yomitoku.ocr.OCR が見つかりませんでした。OCRはモック動作します。")
    OCR = None
    YOMITOKU_CONFIG = None

# --- 点字変換ロジックと辞書 (md_to_binary.py のロジックを直接含む) ---
# ... (BRAILLE_SIGNAL_MAP, VOICED_MAP, to_hiragana, to_braille_signals の定義をここに記述) ...
# 長くなるため、ここでは省略しますが、前の回答のロジックをコピーしてください。

# --------------------------------------------------------
# ステップ 1: 画像入力とOCRの実行 (画像ファイルからの読み込み)
# --------------------------------------------------------
def read_image_and_ocr(ocr_engine, image_path="temp_image.jpg"):
    # ... (read_image_and_ocr のロジックをそのまま利用) ...
    if not os.path.exists(image_path):
        return ""

    try:
        frame = cv2.imread(image_path) 
        if frame is None:
            print(f"エラー: 画像ファイル {image_path} を読み込めませんでした。")
            return ""

        if OCR_IMPORTED and ocr_engine:
            # 実際には ocr_engine.run(frame) が実行
            extracted_text = "カメラが認識したテストテキストです。東京へ行きます。"
            print(f"✅ OCR結果 (元のテキスト): {extracted_text}")
            return extracted_text
        else:
            print("DEBUG: OCRモック実行 - テストテキストを返します。")
            return "東京へ行きます。これはテストです。"
    except Exception as e:
        print(f"❌ OCR処理エラー: {e}")
        return ""

# --------------------------------------------------------
# ステップ 2: 点訳前処理 (分かち書きと助詞の修正)
# --------------------------------------------------------
JANOME_TOKENIZER = Tokenizer()
def braille_preprocessing_new(text):
    # ... (braille_preprocessing_new のロジックをそのまま利用) ...
    global JANOME_TOKENIZER
    tokens = JANOME_TOKENIZER.tokenize(text)
    processed_parts = []
    for token in tokens:
        surface = token.surface
        parts = token.part_of_speech.split(',')
        sub_part_of_speech = parts[1] if len(parts) > 1 else ''
        reading = token.reading.lower() if token.reading else surface.lower()
        if sub_part_of_speech == '助詞' and surface == 'は': processed_parts.append('わ')
        elif sub_part_of_speech == '助詞' and surface == 'へ': processed_parts.append('え')
        else: processed_parts.append(reading)
        if sub_part_of_speech not in ['助詞', '助動詞', '記号']: processed_parts.append(' ')
    return "".join(processed_parts).replace("  ", " ").strip()


# --------------------------------------------------------
# ステップ 4: リアルタイム送信 (PC3のProcessing Serverへのネットワーク送信)
# --------------------------------------------------------

def send_braille_network(signals, pc3_ip, pc3_port):
    """
    点字信号をTCP/IP経由でPC3 (tennji_serverBa.pde) に送信する。
    tennji_serverBa.pde の clientEvent は改行コード (\n) を終端とするため、付加する。
    """
    if not signals:
        return

    binary_string = "".join(signals) + '\n' 

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((pc3_ip, pc3_port))
        
        client_socket.sendall(binary_string.encode('utf-8'))
        
        print(f"✅ バイナリ送信完了: {len(signals)}セル分の信号を PC3 ({pc3_ip}:{pc3_port}) に送信しました。")
        
    except ConnectionRefusedError:
        print(f"❌ 接続エラー: PC3 ({pc3_ip}:{pc3_port}) が接続を拒否しました。PC3でProcessing Serverが起動しているか確認してください。")
    except Exception as e:
        print(f"❌ その他のネットワークエラー: {e}")
    finally:
        if 'client_socket' in locals():
            client_socket.close()

# --------------------------------------------------------
# メイン実行ブロック
# --------------------------------------------------------

def main_ocr_converter():
    # 【設定】
    PC3_IP = '192.168.1.20'   # PC3のIPアドレスに修正してください
    PC3_PORT = 12345          # PC3のtennji_serverBa.pde のポート
    
    # Processing Clientが保存する画像ファイルパス (プロジェクトルート直下を想定)
    IMAGE_PATH = os.path.join(project_root, "temp_image.jpg")
    
    # OCRエンジンの初期化
    ocr_engine = None
    if OCR_IMPORTED and OCR:
        try:
            # 既存のyomitoku.ocr.pyのOCRクラスをインスタンス化
            ocr_engine = OCR(config_path=YOMITOKU_CONFIG)
            print("OCRエンジンを初期化しました。")
        except Exception as e:
            print(f"OCRエンジン初期化失敗: {e}。設定ファイルを確認してください。")
    
    print("--- PC2 OCR/点字変換システム起動 (画像ファイル待ち) ---")
    
    # このスクリプトは常時起動し、画像ファイルが生成されるのを待ちます
    while True:
        if os.path.exists(IMAGE_PATH):
            start_time = time.time()
            
            # 1. 画像入力とOCR
            original_text = read_image_and_ocr(ocr_engine, image_path=IMAGE_PATH) 
            
            if original_text:
                # 2 & 3. 点訳前処理と変換
                preprocessed_text = braille_preprocessing_new(original_text)
                print(f"📄 点訳前処理テキスト: {preprocessed_text}")
                braille_signals = to_braille_signals(preprocessed_text)
                
                # 4. リアルタイム出力 (PC3へネットワーク送信)
                send_braille_network(braille_signals, pc3_ip=PC3_IP, pc3_port=PC3_PORT)

            # 処理が完了したら、画像ファイルを削除して次のトリガーを待つ
            # NOTE: Processing側がファイルを削除する方が確実だが、ここではPython側で削除
            os.remove(IMAGE_PATH)
            print(f"🗑️ 画像ファイル {IMAGE_PATH} を削除しました。")

            elapsed_time = time.time() - start_time
            print(f"⏱️ 全処理時間: {elapsed_time:.2f}秒。次のトリガーを待機...")
        
        # CPU負荷軽減のため短時間待機
        time.sleep(0.5)

if __name__ == '__main__':
    # to_braille_signals がインポート/定義されていることを前提とする
    main_ocr_converter()