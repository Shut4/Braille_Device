import sys
import os
import time
import socket
import cv2
import re
from janome.tokenizer import Tokenizer
from pykakasi import kakasi

# --- パス設定 ---
PROJECT_ROOT = "C:\\Users\\syuuu\\workspace\\PBL_imgproc2"
IMAGE_PATH = os.path.join(PROJECT_ROOT, "temp_image.png")
# --- ネットワーク設定 ---
PC3_IP = '127.0.0.1'   # PC3のIPアドレス
PC3_PORT = 12345       # tennji_serverBa.pde のポート
# ----------------------

# --------------------------------------------------------
# 1. 点字信号とマーカー定義 (md_to_binary.py より)
# --------------------------------------------------------
BRAILLE_SIGNAL_MAP = {
    # 変換は'左上,左中,左下,右上,右中,右下' の順序に従う
    # ひらがな
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
    'っ': '010000', '!': '011010', '?': '010001',
    # アルファベット (小文字)
    'a': '100000', 'b': '110000', 'c': '100100', 'd': '100110', 'e': '100010',
    'f': '110100', 'g': '110110', 'h': '110010', 'i': '010100', 'j': '010110',
    'k': '101000', 'l': '111000', 'm': '101100', 'n': '101110', 'o': '101010',
    'p': '111100', 'q': '111110', 'r': '111010', 's': '011100', 't': '011110',
    'u': '101001', 'v': '111001', 'w': '010111', 'x': '101101', 'y': '101111',
    'z': '101011',
}

DAKUTEN_MARKER = '000010'
HANDAKUTEN_MARKER = '000001'
NUMBER_MARKER = '001111'
CAPITAL_MARKER = '000001'

VOICED_MAP = {
    'が': ('か', DAKUTEN_MARKER), 'ぎ': ('き', DAKUTEN_MARKER), 'ぐ': ('く', DAKUTEN_MARKER), 'げ': ('け', DAKUTEN_MARKER), 'ご': ('こ', DAKUTEN_MARKER),
    'ざ': ('さ', DAKUTEN_MARKER), 'じ': ('し', DAKUTEN_MARKER), 'ず': ('す', DAKUTEN_MARKER), 'ぜ': ('せ', DAKUTEN_MARKER), 'ぞ': ('そ', DAKUTEN_MARKER),
    'だ': ('た', DAKUTEN_MARKER), 'ぢ': ('ち', DAKUTEN_MARKER), 'づ': ('つ', DAKUTEN_MARKER), 'で': ('て', DAKUTEN_MARKER), 'ど': ('と', DAKUTEN_MARKER),
    'ば': ('は', DAKUTEN_MARKER), 'び': ('ひ', DAKUTEN_MARKER), 'ぶ': ('ふ', DAKUTEN_MARKER), 'べ': ('へ', DAKUTEN_MARKER), 'ぼ': ('ほ', DAKUTEN_MARKER),
    'ぱ': ('は', HANDAKUTEN_MARKER), 'ぴ': ('ひ', HANDAKUTEN_MARKER), 'ぷ': ('ふ', HANDAKUTEN_MARKER), 'ぺ': ('へ', HANDAKUTEN_MARKER), 'ぽ': ('ほ', HANDAKUTEN_MARKER)
}

# --------------------------------------------------------
# 2. 点字信号への変換関数 (ロジック維持)
# --------------------------------------------------------
def to_braille_signals(text):
    # (省略なしの to_braille_signals 関数ロジック)
    signals = []
    i = 0
    is_number = False
    is_caps = False

    while i < len(text):
        char = text[i]
        next_char = text[i+1] if i+1 < len(text) else ''
        char_for_pattern = char

        if char.isdigit():
            if not is_number:
                signals.append(NUMBER_MARKER)
                is_number = True
            char_for_pattern = chr(ord('a') + int(char))
        else:
            if is_number and not char.isalpha():
                is_number = False
            char_for_pattern = char

        if char.isalpha() and char.isupper():
            if not is_caps:
                signals.append(CAPITAL_MARKER)
                is_caps = True
            char_for_pattern = char.lower()
        else:
            is_caps = False
            char_for_pattern = char_for_pattern.lower()

        if char in VOICED_MAP:
            base_char, mark = VOICED_MAP[char]
            signals.append(mark)
            signals.append(BRAILLE_SIGNAL_MAP.get(base_char, '000000'))
            i += 1
            continue

        if next_char in ['ゃ', 'ゅ', 'ょ'] and char not in VOICED_MAP:
            signals.append(BRAILLE_SIGNAL_MAP.get(char_for_pattern, '000000'))
            signals.append(BRAILLE_SIGNAL_MAP.get(next_char, '000000'))
            i += 2
            continue

        signals.append(BRAILLE_SIGNAL_MAP.get(char_for_pattern, '000000'))
        i += 1

    return signals


# --------------------------------------------------------
# 3. OCRと前処理 (モックと形態素解析による点訳前処理)
# --------------------------------------------------------

def run_ocr(image_path):
    """画像ファイルを読み込み、OCR (モック) を実行する。"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # 実際にはここで yomitoku の OCR 処理が実行される
    # frame = cv2.imread(image_path)
    return "今日は晴れです。学校へ行きます。123"

def braille_preprocessing_new(text):
    """Janomeとto_hiraganaロジックを統合した点訳前処理。"""
    try:
        # 漢字/カタカナをひらがなにする (pykakasiのロジックを使用)
        kakasi_inst = kakasi()
        kakasi_inst.setMode("J", "H").setMode("K", "H").setMode("H", "H")
        conv = kakasi_inst.getConverter()
        hiragana_text = conv.do(text).lower().replace('\u3000', ' ').strip()
    except AttributeError:
        # pykakasiが利用できない場合はパス
        hiragana_text = text.lower().replace('\u3000', ' ').strip()
        
    # Janomeによる分かち書きと助詞修正
    t = Tokenizer()
    tokens = t.tokenize(hiragana_text)
    processed_parts = []
    
    for token in tokens:
        surface = token.surface
        parts = token.part_of_speech.split(',')
        sub_part_of_speech = parts[1] if len(parts) > 1 else ''
        
        reading = token.reading.lower() if token.reading else surface.lower()

        # 助詞の修正: 「は」->「わ」、「へ」->「え」
        if sub_part_of_speech == '助詞' and surface == 'は': processed_parts.append('わ')
        elif sub_part_of_speech == '助詞' and surface == 'へ': processed_parts.append('え')
        else: processed_parts.append(reading) 
            
        # 分かち書きの挿入
        if sub_part_of_speech not in ['助詞', '助動詞', '記号']: processed_parts.append(' ')

    return "".join(processed_parts).replace("  ", " ").strip()


# --------------------------------------------------------
# 4. PC3へのネットワーク送信関数
# --------------------------------------------------------

def send_braille_network(binary_data):
    """PC3 (tennji_serverBa.pde) へ点字信号をネットワーク送信する。"""
    
    data_to_send = binary_data + '\n' 

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((PC3_IP, PC3_PORT))
        
        client_socket.sendall(data_to_send.encode('utf-8'))
        
        sys.stderr.write(f"✅ ネットワーク送信完了: {len(binary_data)}ビットの信号を {PC3_IP}:{PC3_PORT} に送信しました。\n")
        
    except ConnectionRefusedError:
        sys.stderr.write(f"❌ 接続エラー: PC3 ({PC3_IP}:{PC3_PORT}) が接続を拒否しました。PC3でProcessing Serverが起動しているか確認してください。\n")
    except Exception as e:
        sys.stderr.write(f"❌ ネットワークエラー: {e}\n")
    finally:
        if 'client_socket' in locals():
            client_socket.close()

# --------------------------------------------------------
# 5. メイン実行ブロック
# --------------------------------------------------------

def main_ocr_converter():
    
    sys.stderr.write("--- PC2 OCR/点字変換システム起動 ---\n")

    try:
        # 1. 画像入力とOCR
        original_text = run_ocr(IMAGE_PATH) 
        
        if original_text:
            # 2. 点訳前処理と変換
            preprocessed_text = braille_preprocessing_new(original_text)
            sys.stderr.write(f"📄 点訳前処理テキスト: {preprocessed_text}\n")
            
            braille_signals = to_braille_signals(preprocessed_text)
            final_binary_string = "".join(s for s in braille_signals if s != '\n')
            
            # 3. PC3へネットワーク送信
            send_braille_network(final_binary_string)

            # 4. 処理完了後、画像を削除
            if os.path.exists(IMAGE_PATH):
                os.remove(IMAGE_PATH)
                sys.stderr.write(f"🗑️ 処理完了。画像ファイル {IMAGE_PATH} を削除しました。\n")
        
    except FileNotFoundError as e:
        sys.stderr.write(f"❌ ERROR: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"❌ OCR/変換中にエラー: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    # このスクリプトは Processing から exec() で起動されることを想定
    main_ocr_converter()