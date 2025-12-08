# コマンドラインからのファイル実行時に.mdファイルを読み込み、
# 文字列が格納された変数(final_binary_string)を表示する。

# 2025-12-08 全コード理解済
# 濁音・拗音の処理の部分が修正する必要あり

import sys
# システムモジュール。コマンドライン引数の取得、プログラムの終了、
# 標準入出力を操作したりするために使用。
import re # 正規表現モジュール
from pykakasi import kakasi # 日本語の漢字・カタカナ・ひらがなを変換できるライブラリ。

# --------------------------------------------------------
# 点字信号定義
# --------------------------------------------------------
BRAILLE_SIGNAL_MAP = {
    # 6桁のバイナリ文字列変換に関して、対応関係は'左上,左中,左下,右上,右中,右下' の順序に従う

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

    # 数字は'a'〜'j'の点字表現と重なっている部分があるため、それを利用
    # '1' -> 'a', '2' -> 'b', ..., '0' -> 'j'
}

DAKUTEN_MARKER = '000010' # 濁点の点字マーカー
HANDAKUTEN_MARKER = '000001' # 半濁点の点字マーカー
NUMBER_MARKER = '001111' # 数字の点字マーカー。これを数字の前に挿入することで、a〜jを1〜0として解釈させる。
CAPITAL_MARKER = '000001'# 大文字の点字マーカー。これを大文字の前に挿入する。

VOICED_MAP = { # 濁音・半濁音の対応表
    'が': ('か', DAKUTEN_MARKER), 'ぎ': ('き', DAKUTEN_MARKER), 'ぐ': ('く', DAKUTEN_MARKER), 'げ': ('け', DAKUTEN_MARKER), 'ご': ('こ', DAKUTEN_MARKER),
    'ざ': ('さ', DAKUTEN_MARKER), 'じ': ('し', DAKUTEN_MARKER), 'ず': ('す', DAKUTEN_MARKER), 'ぜ': ('せ', DAKUTEN_MARKER), 'ぞ': ('そ', DAKUTEN_MARKER),
    'だ': ('た', DAKUTEN_MARKER), 'ぢ': ('ち', DAKUTEN_MARKER), 'づ': ('つ', DAKUTEN_MARKER), 'で': ('て', DAKUTEN_MARKER), 'ど': ('と', DAKUTEN_MARKER),
    'ば': ('は', DAKUTEN_MARKER), 'び': ('ひ', DAKUTEN_MARKER), 'ぶ': ('ふ', DAKUTEN_MARKER), 'べ': ('へ', DAKUTEN_MARKER), 'ぼ': ('ほ', DAKUTEN_MARKER),

    'ぱ': ('は', HANDAKUTEN_MARKER), 'ぴ': ('ひ', HANDAKUTEN_MARKER), 'ぷ': ('ふ', HANDAKUTEN_MARKER), 'ぺ': ('へ', HANDAKUTEN_MARKER), 'ぽ': ('ほ', HANDAKUTEN_MARKER)
}


# --------------------------------------------------------
# Markdownクリーンアップとひらがな変換の関数定義
# --------------------------------------------------------

def extract_clean_text_from_md(file_path):
    """
    Markdownファイル(.md)を引数とし、不要な要素を除去してクリーンな文字列を抽出する。
    ファイルが存在せず読み込みに失敗した場合は None を返す。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # open()関数は、Pythonファイルを開き、中身を読み込むための組み込み関数。
            # 第一引数にファイルパス、第二引数にモード('r'は読み取り専用モード)、encodingで文字コードを指定。
            # 開いたファイルオブジェクトを変数fに代入している。
            md_content = f.read() # read()メソッドでファイル全体の内容を文字列として一括読み込み
    except FileNotFoundError:
        return None
    except Exception:
        return None

    text = md_content # 文字列が格納された変数
    # re.sub()は、文字列の中で パターンに一致した部分を置換する役割
    text = re.sub(r'<[^>]*>', '', text)          # HTMLタグ除去
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text) # リンク除去
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE) # 見出し除去
    text = re.sub(r'[*_`]', '', text)            # 強調・コード除去
    text = re.sub(r'\n{2,}', '\n', text)         # 連続改行を統一

    return text.strip()
    # strip()メゾットで文字列の前後の空白や改行を削除する。
    # 半角スペース,\t, \n, \rなど


def to_hiragana(text):
    """
    文字列(今回はtext.strip())を受け取り、可能な文字をすべてひらがなに変換して文字列を返す。
    """
    try:
        kakasi_inst = kakasi() # pykakasiライブラリのkakasiクラスのインスタンスを作成
        kakasi_inst.setMode("J", "H").setMode("K", "H").setMode("H", "H")
        # 変換モードを設定(J: 漢字, K: カタカナ, H: ひらがな)
        # 例えばsetMode("J", "H") は、漢字をひらがなに変換する設定
        # 今回はすべてひらがなに変換する
        conv = kakasi_inst.getConverter()# 実際に変換を行うコンバータ(変換器)を取得
        return conv.do(text).lower().replace('\u3000', ' ').strip()
        # do()メソッドで変換を実行、lower()で英字が含まれていた場合に小文字に変換、
        # replace()で全角スペース（Unicode U+3000）を半角スペースに置換、
        # strip()で前後の空白を削除して返す

    except AttributeError:
        # pykakasiエラー時のフォールバック処理 (このロジックは完全なものとは限らない)
        return text.lower().replace('\u3000', ' ').strip() # 漢字やカタカナはそのまま残る可能性あり


# --------------------------------------------------------
# 点字バイナリ信号への変換関数 (ロジック維持)
# --------------------------------------------------------

def to_braille_signals(text):
    """
    文字列(今回はひらがな変換後のテキスト)を受け取り、6桁のバイナリ信号リストに変換する。
    """
    # 初期化
    signals = [] # 出力となる点字信号のリスト
    i = 0 # 文字列インデックス
    is_number = False # 数字モードフラグ
    is_caps = False # 大文字モードフラグ


    while i < len(text):
        char = text[i]
        next_char = text[i+1] if i+1 < len(text) else ''
        # next_charは次の文字を見て「拗音（ゃゅょ）」などを判定するために使用

        # --- 数字/大文字符の挿入ロジック ---
        char_for_pattern = char # 点字パターン照合用の文字変数

        # 数字処理: 数符挿入
        if char.isdigit():# 文字列が数字かどうかを判定
            if not is_number:
                signals.append(NUMBER_MARKER)# 数符（NUMBER_MARKER） を挿入。
                is_number = True
                if char == '0':
                    char_for_pattern = 'j'
                else:
                    char_for_pattern = chr(ord('a') + int(char) - 1)
            # chr()関数は、数値（Unicodeコードポイント）を対応する文字に変換するための組み込み関数。
            # ord()関数は、文字を対応するUnicodeコードポイント（整数）に変換するための組み込み関数。
            # '1' -> 'a', '2' -> 'b', ..., '0' -> 'j'
        else:
            if is_number and not char.isalpha():# 数字モード終了判定
                is_number = False
            char_for_pattern = char
            # 数字以外の文字(アルファベット、ひらがな)はそのままcharを使用。
            # 漢字が混入している可能性もある。

        # 大文字処理: 大文字符を挿入
        if char.isalpha() and char.isupper():
            if not is_caps:
                signals.append(CAPITAL_MARKER)# 英字が大文字なら大文字符（CAPITAL_MARKER）を挿入。
                is_caps = True
            char_for_pattern = char.lower()
        else:# 大文字ではない文字の場合(小文字または数字、ひらがな、記号)
            is_caps = False
            char_for_pattern = char_for_pattern.lower() # 安全のため小文字化

        ### 要修正 ###
        # --- 濁音・拗音の処理 ---

        # 濁音・半濁音
        if char in VOICED_MAP:
            base_char, mark = VOICED_MAP[char]
            signals.append(mark)
            signals.append(BRAILLE_SIGNAL_MAP.get(base_char, '000000'))
            # get()メソッドは、辞書からキーに対応する値を取得するためのメソッド。
            # 対応表に存在しなければ '000000'（空白扱い）を返す安全策
            i += 1
            continue

        # 拗音（分割）※対象は「きゃ」「しゅ」「ちょ」など。
        # 上で濁音・半濁音処理を先にしているため、「じゃ」「びょ」などはここには来ない。
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
# メイン実行ブロック (標準出力にバイナリ文字列を出力)
# --------------------------------------------------------
if __name__ == '__main__':
    # 上記のif文により、このファイルが直接実行された場合にのみ以下のコードを実行する。
    # 他のモジュールからインポートされた場合にメインコードが実行されるのを防ぐ。

    # コマンドライン引数のチェック (エラーメッセージは標準エラー出力へ)
    if len(sys.argv) < 2:
        # sys.argv[0] → 実行ファイル名
        # sys.argv[1] → ユーザーが指定した.mdファイルのパス
        print("エラー: 処理対象のMarkdownファイルパスを引数として指定してください。", file=sys.stderr)
        sys.exit(1)
        # プログラムを終了させるための関数。
        # 引数1は異常終了を示す。

    md_file_path = sys.argv[1]

    # Markdownクリーンアップとテキスト抽出
    extracted_text = extract_clean_text_from_md(md_file_path)
    if extracted_text is None:
        sys.exit(1)

    # 可能な文字を全てひらがなへ変換
    hiragana_output = to_hiragana(extracted_text)

    # 点字信号へ変換
    braille_signals = to_braille_signals(hiragana_output)

    # 標準出力 (stdout) にバイナリ信号の連続文字列のみを出力
    final_binary_string = "".join(s for s in braille_signals if s != '\n')
    print(final_binary_string)

    # ------------------------------------------------------------------
    #  視覚化/デバッグ情報は、すべて標準エラー出力 (sys.stderr) に出す
    # ------------------------------------------------------------------
    # sys.stderrは標準出力(stdout)とは別のチャンネルに出力されるため、
    # stdoutのバイナリデータが他のプロセスでキャプチャされるのをさまたげない

    def print_debug_info(title, content):
        """
        本番の出力（PC3に渡す生の点字バイナリ列）と補助情報（ログ・可視化・デバッグ）
        を別チャンネルに分離する設計。

        標準出力は他プロセスへ渡すための純粋なデータ専用にし、デバッグは標準エラーに流す。
        """
        print(f"\n--- {title} ---", file=sys.stderr)
        print(content, file=sys.stderr)

    # print_debug_info("デバッグ情報", f"入力ファイル: {md_file_path}")
    # print_debug_info("ひらがな変換結果", hiragana_output)
    print_debug_info("バイナリ信号総数", len(final_binary_string))