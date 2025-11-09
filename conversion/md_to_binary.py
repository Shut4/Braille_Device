import sys
from md_to_hiragana import to_hiragana, extract_clean_text_from_md
# import re

# .mdファイルをコマンドライン引数として受け取り、
# 抽出された純粋なテキストをひらがな変換し、バイナリ形式に変換したものをターミナルに出力する


# 現時点での課題・TODOリスト:
# --------------------------------------------------------
# * 点字デバイス表示の際に濁点などの2セットで一文字が途切れたら面倒なのでそこ改良する必要あり
# * 「わたしは」の「は」や、「本屋へ」の「へ」は、点字では話すように「わ」「え」と書くため、そこを修正する必要あり
# * 点字で文を書く時には、意味のまとまりごとに1マスあけて書く必要あり
# * 「う段」の音がのびる時はのばす記号を使う。「きょうは」が「きょーわ」になる
# * 外国語引用符(外国文字が、文または語句になっているときに挟むように使用する符号)の実装検討
# * すべての文字が大文字の場合は、外字符の後に二重大文字符を置く
# * 外字符、二重大文字符、アクセント符の実装検討
# --------------------------------------------------------


# --------------------------------------------------------
# 点字信号とマーカー定義 (バイナリ形式: 1=ON, 0=OFF)
# --------------------------------------------------------
BRAILLE_SIGNAL_MAP = {
    # 中身正誤チェック済み◎
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

    # 数字 (0-9)はアルファベットの a-j と同じパターンなため省略
}

DAKUTEN_MARKER = '000010'    # 濁点符(濁点を表す符号)
HANDAKUTEN_MARKER = '000001' # 半濁点符(半濁点を表す符号)
NUMBER_MARKER = '001111'     # 数符(数を表す符号)
CAPITAL_MARKER = '000001'    # 大文字符(大文字を表す符号)


# 濁音・半濁音のマッピング
# 'が' => ('か', 濁点符) のようにベースの文字とマーカーの"セット"とした
VOICED_MAP = {
    'が': ('か', DAKUTEN_MARKER), 'ぎ': ('き', DAKUTEN_MARKER), 'ぐ': ('く', DAKUTEN_MARKER), 'げ': ('け', DAKUTEN_MARKER), 'ご': ('こ', DAKUTEN_MARKER),
    'ざ': ('さ', DAKUTEN_MARKER), 'じ': ('し', DAKUTEN_MARKER), 'ず': ('す', DAKUTEN_MARKER), 'ぜ': ('せ', DAKUTEN_MARKER), 'ぞ': ('そ', DAKUTEN_MARKER),
    'だ': ('た', DAKUTEN_MARKER), 'ぢ': ('ち', DAKUTEN_MARKER), 'づ': ('つ', DAKUTEN_MARKER), 'で': ('て', DAKUTEN_MARKER), 'ど': ('と', DAKUTEN_MARKER),
    'ば': ('は', DAKUTEN_MARKER), 'び': ('ひ', DAKUTEN_MARKER), 'ぶ': ('ふ', DAKUTEN_MARKER), 'べ': ('へ', DAKUTEN_MARKER), 'ぼ': ('ほ', DAKUTEN_MARKER),
    'ぱ': ('は', HANDAKUTEN_MARKER), 'ぴ': ('ひ', HANDAKUTEN_MARKER), 'ぷ': ('ふ', HANDAKUTEN_MARKER), 'ぺ': ('へ', HANDAKUTEN_MARKER), 'ぽ': ('ほ', HANDAKUTEN_MARKER)
}


# --------------------------------------------------------
# 点字のバイナリ信号への変換
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

        # 記号処理（数字、アルファベット）
        # BRAILLE_SIGNAL_MAPが認識できる基本的な文字パターン、
        # （主に小文字のアルファベット）に一時的に変換するための変数
        char_for_pattern = char

        # 数字処理: 数符挿入
        if char.isdigit():
            if not is_number:
                signals.append(NUMBER_MARKER)
                is_number = True
            # 数字はアルファベットの a-j のパターンを使用
            # 下の1行で、点字の変換ロジックの中で数字の文字 ('1', '2', '3'...) を
            # 対応するアルファベットの文字 ('a', 'b', 'c'...) に変換する
            char_for_pattern = chr(ord('a') + int(char))
        else:
            # 数字の連鎖が途切れたらフラグをリセット
            if is_number and not char.isalpha(): # アルファベットの直前ではリセットしない
                 is_number = False
            char_for_pattern = char # この行不要じゃね？

        # 大文字処理: 大文字符を挿入
        if char.isalpha() and char.isupper():
            if not is_caps:
                signals.append(CAPITAL_MARKER)
                is_caps = True
            char_for_pattern = char.lower()
        else:
            # char.isalpha():Falseで and char.isupper():True になることはないのでは？想定していない特殊な文字ではあり得るんかな？
            is_caps = False
            char_for_pattern = char_for_pattern.lower() # ひらがな変換結果は小文字前提
            # char_for_pattern = char.lower()ではだめ？

        # 拗音、濁音、清音の処理

        # 濁音・半濁音
        if char in VOICED_MAP:
            base_char, mark = VOICED_MAP[char]
            signals.append(mark)
            signals.append(BRAILLE_SIGNAL_MAP.get(base_char, '000000'))# 清音バイナリ信号取得。'000000'は未定義文字用のダミー
            i += 1
            continue

        #処理うまく出来てないと思うので再検討する必要あり
        # 拗音（'きゃ'='き'+'ゃ'） - 拗音は点字では基本的に一文字扱い (ここでは分割)
        # char not in VOICED_MAPにより「ぎゃ」等の一文字目濁音は取り扱っていない
        if next_char in ['ゃ', 'ゅ', 'ょ'] and char not in VOICED_MAP: # char + next_char not in VOICED_MAP不要じゃね？
            # 拗音の「ゃゅょ」自体も点字パターンを持つ
            signals.append(BRAILLE_SIGNAL_MAP.get(char_for_pattern, '000000'))
            signals.append(BRAILLE_SIGNAL_MAP.get(next_char, '000000'))
            i += 2
            continue

        # 通常文字 (ひらがな、アルファベット小文字、記号)
        signals.append(BRAILLE_SIGNAL_MAP.get(char_for_pattern, '000000'))
        i += 1

    return signals


# --------------------------------------------------------
# メイン実行ブロック
# --------------------------------------------------------
if __name__ == '__main__':
    # コマンドライン引数のチェック
    # sys.argv: 実行時にコマンドラインに入力された引数（argument）リストで、
    # sys.argv[0]には、常に実行されたスクリプト自身のファイル名が格納される
    if len(sys.argv) < 2:
        print("エラー: 処理対象のMarkdownファイルパスを引数として指定して")
        sys.exit(1)

    # 解析対象のMarkdownファイルパス
    md_file_path = sys.argv[1]

    # Markdownクリーンアップとテキスト抽出
    extracted_text = extract_clean_text_from_md(md_file_path)

    # 可能な文字を全てひらがなへ変換
    hiragana_output = to_hiragana(extracted_text) # "ROS とはなにか"

    # 点字信号へ変換
    braille_signals = to_braille_signals(hiragana_output)


    # 以降不要であればコメント化可能

    # 結果の出力
    print("--- 処理結果 ---")
    print(f"入力ファイル: {md_file_path}")
    print("\n--- 1. 可能な文字全てをひらがなへ変換した結果 ---")
    print(hiragana_output)
    print("\n--- 2. 点字信号 ---")

    # 信号の表示（Processing/ESP32への送信形式）
    print("ピン配置順番:\n   14 |\n   25 |\n   36 |\n")

    for signal in braille_signals:
        if signal == '\n':
            print("\n[改行]")
        else:
            # バイナリ信号とピン配置を視覚的に表示
            pin_14 = signal[0] + signal[3]
            pin_25 = signal[1] + signal[4]
            pin_36 = signal[2] + signal[5]
            print(f"   {pin_14} |\n   {pin_25} |\n   {pin_36} |\n (Signal: {signal})\n")

    print("\n----------------------------------")

    # ファイルへの保存 (Processing/ESP32での読み込みを想定し、カンマ区切りなしで保存)
    with open("braille_signals.txt", "w", encoding="utf-8") as f:
        # 信号を連続した文字列として保存
        f.write("".join(s for s in braille_signals if s != '\n'))
    print(" 6桁バイナリ信号の連なりは braille_signals.txt として保存済")