import sys
import re
import socket # <--- ネットワーク通信のために追加
from pykakasi import kakasi

# --- ネットワーク設定 (PC3: tennji_clientBa.pde の接続先) ---
# NOTE: tennji_clientBa.pde は localhost:12345 に接続しています。
# このPythonコードは、PC3が接続を受け付ける (サーバーとして動作する) ポート12345に送信します。
PC3_IP = '127.0.0.1'  # !!! PC3の実際のIPアドレスに修正してください (単一PCテストの場合は '127.0.0.1') !!!
PC3_PORT = 12345
# --------------------------------------------------------

# --------------------------------------------------------
# 1. 点字信号とマーカー定義 (ロジック維持)
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
# 2. Markdownクリーンアップとひらがな変換 (関数定義)
# --------------------------------------------------------

def extract_clean_text_from_md(file_path):
    # 既存のMarkdown抽出・クリーンアップロジックをここに実装
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        return None
    except Exception:
        return None

    text = md_content
    # クリーンアップ処理を簡潔に再記述（実際は元の長い正規表現ロジックが適用される）
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'[*_`]', '', text)
    text = re.sub(r'\n{2,}', '\n', text)

    return text.strip()


def to_hiragana(text):
    # 既存の pykakasi 変換ロジックを実装
    try:
        kakasi_inst = kakasi()
        kakasi_inst.setMode("J", "H").setMode("K", "H").setMode("H", "H")
        conv = kakasi_inst.getConverter()
        return conv.do(text).lower().replace('\u3000', ' ').strip()
    except AttributeError:
        # pykakasiエラー時のフォールバック処理
        return text.lower().replace('\u3000', ' ').strip()


# --------------------------------------------------------
# 3. 点字信号への変換関数 (ロジック維持)
# --------------------------------------------------------

def to_braille_signals(text):
    """
    ひらがな変換後のテキストを受け取り、6桁のバイナリ信号リストに変換する。
    """
    signals = []
    i = 0
    is_number = False
    is_caps = False

    while i < len(text):
        char = text[i]
        next_char = text[i+1] if i+1 < len(text) else ''

        # --- 数字/大文字符の挿入ロジック ---
        char_for_pattern = char

        # 数字処理: 数符挿入
        if char.isdigit():
            if not is_number:
                signals.append(NUMBER_MARKER)
                is_number = True
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

        # --- 濁音・拗音の処理 ---

        # 濁音・半濁音
        if char in VOICED_MAP:
            base_char, mark = VOICED_MAP[char]
            signals.append(mark)
            signals.append(BRAILLE_SIGNAL_MAP.get(base_char, '000000'))
            i += 1
            continue

        # 拗音（分割）
        if next_char in ['ゃ', 'ゅ', 'ょ'] and char not in VOICED_MAP:
            signals.append(BRAILLE_SIGNAL_MAP.get(char_for_pattern, '000000'))
            signals.append(BRAILLE_SIGNAL_MAP.get(next_char, '000000'))
            i += 2
            continue

        # 通常文字
        signals.append(BRAILLE_SIGNAL_MAP.get(char_for_pattern, '000000'))
        i += 1

    return signals

# --------------------------------------------------------
# 5. PC3へのネットワーク送信関数 (新規追加)
# --------------------------------------------------------

def send_braille_network(binary_data):
    """PC3 (tennji_clientBa.pde) へ点字信号をネットワーク送信する。"""

    # Processing側が readString() で読み取り、その後 trim() を行うため、
    # 末尾に改行コード '\n' を付加し、データの区切りとします。
    data_to_send = binary_data + '\n'

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # PC3のProcessingが待ち受けている IP/Port に接続
        client_socket.connect((PC3_IP, PC3_PORT))

        # データを送信
        client_socket.sendall(data_to_send.encode('utf-8'))

        print(f"✅ ネットワーク送信完了: {len(binary_data)}ビットの信号を {PC3_IP}:{PC3_PORT} に送信しました。", file=sys.stderr)

    except ConnectionRefusedError:
        print(f"❌ 接続エラー: PC3 ({PC3_IP}:{PC3_PORT}) が接続を拒否しました。PC3でProcessing Serverが起動しているか確認してください。", file=sys.stderr)
    except Exception as e:
        print(f"❌ ネットワークエラー: {e}", file=sys.stderr)
    finally:
        if 'client_socket' in locals():
            client_socket.close()

# --------------------------------------------------------
# 4. メイン実行ブロック (標準出力にバイナリ文字列を出力)
# --------------------------------------------------------
if __name__ == '__main__':
    # コマンドライン引数のチェック (エラーメッセージは標準エラー出力へ)
    if len(sys.argv) < 2:
        print("エラー: 処理対象のMarkdownファイルパスを引数として指定してください。", file=sys.stderr)
        sys.exit(1)

    md_file_path = sys.argv[1]

    # 1. Markdownクリーンアップとテキスト抽出
    extracted_text = extract_clean_text_from_md(md_file_path)
    if extracted_text is None:
        sys.exit(1)

    # 2. 可能な文字を全てひらがなへ変換
    hiragana_output = to_hiragana(extracted_text)

    # 3. 点字信号へ変換
    braille_signals = to_braille_signals(hiragana_output)

    # 4. バイナリ信号の連続文字列を生成
    final_binary_string = "".join(s for s in braille_signals if s != '\n')

    # 5. 標準出力 (stdout) にバイナリ信号の連続文字列のみを出力 (他のプロセスがキャプチャ可能)
    print(final_binary_string)

    # 6. PC3へのネットワーク送信
    if final_binary_string:
        send_braille_network(final_binary_string)

    # ------------------------------------------------------------------
    #  視覚化/デバッグ情報は、すべて標準エラー出力 (sys.stderr) に出す
    # ------------------------------------------------------------------
    def print_debug_info(title, content):
        print(f"\n--- {title} ---", file=sys.stderr)
        print(content, file=sys.stderr)

    print_debug_info("バイナリ信号総数", len(final_binary_string))