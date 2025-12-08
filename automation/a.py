import sys
import os
import time
import serial
import cv2
from janome.tokenizer import Tokenizer
import numpy as np

# --------------------------------------------------------
# 既存ファイルの利用と設定
# --------------------------------------------------------

# yomitoku ライブラリからOCRクラスをインポート（別途インストールが必要です）
try:
    # 実際には、from yomitoku.ocr import OCR を使用します
    # ここでは便宜上、クラス定義をスキップし、実行時にモック関数を使用します。
    # OCR = __import__('yomitoku.ocr', fromlist=['OCR']).OCR
    OCR = object # 仮のクラス定義
    YOMITOKU_CONFIG = "configs/yomitoku-text-detector-dbnet-open-beta.yaml" 
except ImportError:
    print("Warning: yomitokuモジュールが見つかりません。OCRはモック動作します。")
    OCR = None 
    YOMITOKU_CONFIG = None

# --- md_to_binary.py の内容を直接定義 ---
# to_braille_signals 関数内で使用する点字信号とマーカーを定義します。
# --------------------------------------------------------
# 点字信号とマーカー定義 (md_to_binary.py より)
# --------------------------------------------------------
BRAILLE_SIGNAL_MAP = {
    # 変換は'左上,左中,左下,右上,右中,右下' の順序に従う (1=ON, 0=OFF)
    'あ': '100000', 'い': '110000', 'う': '100100', 'え': '110100', 'お': '010100',
    'か': '100001', 'き': '110001', 'く': '100101', 'け': '110101', 'こ': '010101',
    'さ': '100011', 'し': '110011', 'す': '100111', 'せ': '110111', 'そ': '010111',
    'た': '101010', 'ち': '111010', 'つ': '101110', 'て': '111110', 'と': '011110',
    'な': '101000', 'に': '111000', 'ぬ': '101100', 'ね': '111100', 'の': '011100',
    'は': '101001', 'ひ': '111001', 'ふ': '101101', 'へ': '111101', 'ほ': '011101',
    'ま': '101011', 'み': '111011', 'む': '101111', 'め': '111111', 'も': '011111',
    'や': '001100', 'ゆ': '001101', 'よ': '001110',
    'ら': '100010', 'り': '110010', 'る': '100110', 'れ': '110110', 'ろ': '010110',
    'わ': '001000', 'を': '001010', 'ん': '001011',
    'ゃ': '100001', 'ゅ': '100101', 'ょ': '010101',
    'ー': '010010', '、': '000011', '。': '010011', ' ': '000000', 
    'っ': '010000', '!': '011010', '?': '010001', #

    # アルファベット (小文字)
    'a': '100000', 'b': '110000', 'c': '100100', 'd': '100110', 'e': '100010',
    'f': '110100', 'g': '110110', 'h': '110010', 'i': '010100', 'j': '010110',
    'k': '101000', 'l': '111000', 'm': '101100', 'n': '101110', 'o': '101010',
    'p': '111100', 'q': '111110', 'r': '111010', 's': '011100', 't': '011110',
    'u': '101001', 'v': '111001', 'w': '010111', 'x': '101101', 'y': '101111',
    'z': '101011', #
}

DAKUTEN_MARKER = '000010'    # 濁点符
HANDAKUTEN_MARKER = '000001' # 半濁点符
NUMBER_MARKER = '001111'     # 数符
CAPITAL_MARKER = '000001'    # 大文字符

# 濁音・半濁音のマッピング (md_to_binary.py より)
VOICED_MAP = {
    'が': ('か', DAKUTEN_MARKER), 'ぎ': ('き', DAKUTEN_MARKER), 'ぐ': ('く', DAKUTEN_MARKER), 'げ': ('け', DAKUTEN_MARKER), 'ご': ('こ', DAKUTEN_MARKER),
    'ざ': ('さ', DAKUTEN_MARKER), 'じ': ('し', DAKUTEN_MARKER), 'ず': ('す', DAKUTEN_MARKER), 'ぜ': ('せ', DAKUTEN_MARKER), 'ぞ': ('そ', DAKUTEN_MARKER),
    'だ': ('た', DAKUTEN_MARKER), 'ぢ': ('ち', DAKUTEN_MARKER), 'づ': ('つ', DAKUTEN_MARKER), 'で': ('て', DAKUTEN_MARKER), 'ど': ('と', DAKUTEN_MARKER),
    'ば': ('は', DAKUTEN_MARKER), 'び': ('ひ', DAKUTEN_MARKER), 'ぶ': ('ふ', DAKUTEN_MARKER), 'べ': ('へ', DAKUTEN_MARKER), 'ぼ': ('ほ', DAKUTEN_MARKER),
    'ぱ': ('は', HANDAKUTEN_MARKER), 'ぴ': ('ひ', HANDAKUTEN_MARKER), 'ぷ': ('ふ', HANDAKUTEN_MARKER), 'ぺ': ('へ', HANDAKUTEN_MARKER), 'ぽ': ('ほ', HANDAKUTEN_MARKER)
} #


# --- md_to_hiragana.py のプロキシ関数 ---
def to_hiragana(text):
    """
    md_to_hiragana.py の機能を簡易的に再現（漢字をひらがなに変換）。
    今回は Janome の形態素解析で読みを取得するため、ここでは主にそのまま返します。
    """
    # 実際は md_to_hiragana.py のロジックを使用します
    return text.lower() # 一応小文字に統一


# --- md_to_binary.py の to_braille_signals 関数 ---
def to_braille_signals(text):
    """
    ひらがな変換後のテキストを受け取り、6桁のバイナリ信号リストに変換する。
    (md_to_binary.pyのロジックをそのまま利用)
    """
    signals = []
    i = 0
    is_number = False
    is_caps = False

    while i < len(text):
        char = text[i]
        next_char = text[i+1] if i+1 < len(text) else ''

        char_for_pattern = char

        # 数字処理: 数符挿入
        if char.isdigit():
            if not is_number:
                signals.append(NUMBER_MARKER)
                is_number = True
            # 数字はアルファベットの a-j のパターンを使用
            char_for_pattern = chr(ord('a') + int(char))
        else:
            if is_number and not char.isalpha(): 
                 is_number = False
            char_for_pattern = char 

        # 大文字処理: 大文字符を挿入
        if char.isalpha() and char.isupper():
            if not is_caps:
                signals.append(CAPITAL_MARKER)
                is_caps = True
            char_for_pattern = char.lower()
        else:
            is_caps = False
            char_for_pattern = char_for_pattern.lower()

        # 濁音・半濁音 (md_to_binary.pyのVOICED_MAPを使用)
        if char in VOICED_MAP:
            base_char, mark = VOICED_MAP[char] 
            signals.append(mark)
            signals.append(BRAILLE_SIGNAL_MAP.get(base_char, '000000')) # 清音バイナリ信号取得
            i += 1
            continue

        # 拗音（「ゃゅょ」など）
        if next_char in ['ゃ', 'ゅ', 'ょ'] and char not in VOICED_MAP:
            signals.append(BRAILLE_SIGNAL_MAP.get(char_for_pattern, '000000'))
            signals.append(BRAILLE_SIGNAL_MAP.get(next_char, '000000'))
            i += 2
            continue

        # 通常文字 (ひらがな、アルファベット小文字、記号)
        signals.append(BRAILLE_SIGNAL_MAP.get(char_for_pattern, '000000'))
        i += 1

    return signals


# --------------------------------------------------------
# ステップ 1: 画像入力とOCRの実行
# --------------------------------------------------------

def capture_and_ocr(ocr_engine, camera_index=0):
    """
    カメラから画像をキャプチャし、yomitokuのOCRエンジンでテキストに変換する（モック含む）。
    """
    # camera_capture_png.py のロジックをCV2で再現
    cap = cv2.VideoCapture(camera_index) 
    if not cap.isOpened():
        print("エラー: カメラを開けませんでした。インデックスを確認してください。")
        return ""
    
    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()
    
    if not ret:
        print("エラー: 画像の読み込みに失敗しました。")
        return ""
    
    if ocr_engine:
        # 実際にはここで ocr_engine.run(frame) が実行されます
        try:
            # ocr_result = ocr_engine.run(frame)
            # extracted_text = ... (yomitoku.reading_order.py による整理後のテキスト)
            extracted_text = "カメラが認識したテストテキストです。東京へ行きます。"
            print(f"✅ OCR結果 (元のテキスト): {extracted_text}")
            return extracted_text
        except Exception as e:
            print(f"❌ OCR実行エラー: {e}")
            return ""
    else:
        # OCRモック（yomitokuがない場合のテスト用）
        print("DEBUG: OCRモック実行 - テストテキストを返します。")
        return "東京へ行きます。これはテストです。" 

# --------------------------------------------------------
# ステップ 2: 点訳前処理 (分かち書きと助詞の修正)
# --------------------------------------------------------

# JanomeのTokenizerを初期化
JANOME_TOKENIZER = Tokenizer()

def braille_preprocessing_new(text):
    """
    日本語の点字ルールに合わせてテキストを整形する。
    1. 助詞の修正: 「は」を「わ」に、「へ」を「え」に変換 (md_to_binary.pyのTODOに対応)
    2. 分かち書き: 形態素解析を利用し、意味のまとまりごとにスペース ' ' を挿入
    """
    global JANOME_TOKENIZER
    # 形態素解析用に事前に to_hiragana を通す（md_to_hiragana.pyの機能の一部）
    initial_processed_text = to_hiragana(text) 
    tokens = JANOME_TOKENIZER.tokenize(initial_processed_text)
    
    processed_parts = []
    
    for token in tokens:
        surface = token.surface
        parts = token.part_of_speech.split(',')
        sub_part_of_speech = parts[1] if len(parts) > 1 else ''
        
        # 形態素解析の結果の読み（カタカナ）を取得し、ひらがなとして処理
        reading = token.reading.lower() if token.reading else surface.lower()
        
        # 1. 助詞の修正
        if sub_part_of_speech == '助詞' and surface == 'は':
            processed_parts.append('わ')
        elif sub_part_of_speech == '助詞' and surface == 'へ':
            processed_parts.append('え')
        else:
            processed_parts.append(reading) 
            
        # 2. 分かち書き 
        # 形態素の区切りにスペースを挿入するシンプルなロジック
        if sub_part_of_speech not in ['助詞', '助動詞', '記号']:
             processed_parts.append(' ')

    # 連続するスペースや文頭/文末のスペースを削除
    processed_text = "".join(processed_parts).replace("  ", " ").strip()
    return processed_text

# --------------------------------------------------------
# ステップ 4: リアルタイム送信
# --------------------------------------------------------

def send_braille_signals(signals, port='COM3', baudrate=9600):
    """
    点字信号をシリアルポート経由で点字デバイスに送信する。
    """
    if not signals:
        return

    try:
        # シリアルポートを開く
        ser = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2) # 接続確立待ち
        
        # 信号を連続した文字列に結合
        binary_string = "".join(signals)
        
        # デバイス側が読み取れる形式でデータを送信
        # ESP32/Arduino側でこの文字列を6文字ずつ区切ってピン制御を行います
        ser.write(binary_string.encode('utf-8'))
        
        print(f"✅ シリアル送信完了: {len(signals)}セル ({len(binary_string)}ビット) の信号を {port} に送信。")
        
    except serial.SerialException as e:
        print(f"❌ シリアル通信エラーが発生しました: {e}")
        print(f"ポート: {port} を確認してください。")
    except Exception as e:
        print(f"❌ その他のエラー: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()

# --------------------------------------------------------
# メイン実行ブロック
# --------------------------------------------------------

def main_realtime_automation():
    # 【設定】
    CAP_INTERVAL = 2  # 画像キャプチャの間隔（秒）
    SERIAL_PORT = 'COM3' # 環境に合わせて設定 (C:\Users\syuuu\... のためCOMポートを推奨)
    BAUDRATE = 9600
    
    # OCRエンジンの初期化
    ocr_engine = None
    if OCR:
        try:
            # 既存のyomitoku.ocr.pyのOCRクラスをインスタンス化
            ocr_engine = OCR(config_path=YOMITOKU_CONFIG)
            print("OCRエンジンを初期化しました。")
        except Exception as e:
            print(f"OCRエンジン初期化失敗: {e}。設定ファイルを確認してください。")
    
    print("--- リアルタイム点字変換システム起動 ---")
    
    while True:
        start_time = time.time()
        
        # 1. 画像入力とOCR
        original_text = capture_and_ocr(ocr_engine) 
        
        if original_text:
            # 2. 点訳前処理 (分かち書きと助詞の修正)
            preprocessed_text = braille_preprocessing_new(original_text)
            print(f"📄 点訳前処理テキスト: {preprocessed_text}")
            
            # 3. 点字バイナリ信号への変換 (md_to_binary.py のロジックを使用)
            braille_signals = to_braille_signals(preprocessed_text)
            
            # 4. リアルタイム出力 (点字デバイスへの送信)
            send_braille_signals(braille_signals, port=SERIAL_PORT, baudrate=BAUDRATE)

        # リアルタイム性の確保
        elapsed_time = time.time() - start_time
        wait_time = max(0, CAP_INTERVAL - elapsed_time)
        # print(f"⏱️ 処理時間: {elapsed_time:.2f}秒, 次のキャプチャまで: {wait_time:.2f}秒待機...")
        time.sleep(wait_time)

if __name__ == '__main__':
    main_realtime_automation()