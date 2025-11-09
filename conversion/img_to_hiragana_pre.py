#2025-10-5

#ファイル内容をOCR処理をしてひらがな変換、点字変換してターミナルへプリントする
#yomitokuとは別のOCR処理方式であり、こっちのが精度低い
#ただ、ひらがな変換の精度はよい(漢字をひらがなに等)

import cv2
import pytesseract
from PIL import Image
import numpy as np
from pykakasi import kakasi

# Tesseractのパス（必要に応じて）
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 画像読み込みと前処理
image_path = "imgs/mail2.png"
img = cv2.imread(image_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
_, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
kernel = np.ones((2, 2), np.uint8)
morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
resized = cv2.resize(morphed, None, fx=2, fy=2, interpolation=cv2.INTER_LINEAR)
pil_img = Image.fromarray(resized)

# OCR実行（日本語指定）
ocr_text = pytesseract.image_to_string(pil_img, lang="jpn")

# ひらがな変換（pykakasi使用）
def to_hiragana(text):
    kakasi_inst = kakasi()
    kakasi_inst.setMode("J", "H")
    kakasi_inst.setMode("K", "H")
    kakasi_inst.setMode("H", "H")
    conv = kakasi_inst.getConverter()
    return conv.do(text)

hiragana_text = to_hiragana(ocr_text)

# 点字マッピング（ひらがな＋アルファベット）
braille_map = {
    # ひらがな
    'あ': '⠁', 'い': '⠃', 'う': '⠉', 'え': '⠋', 'お': '⠊',
    'か': '⠡', 'き': '⠣', 'く': '⠩', 'け': '⠫', 'こ': '⠪',
    'さ': '⠱', 'し': '⠳', 'す': '⠹', 'せ': '⠻', 'そ': '⠺',
    'た': '⠕', 'ち': '⠗', 'つ': '⠝', 'て': '⠟', 'と': '⠞',
    'な': '⠅', 'に': '⠇', 'ぬ': '⠍', 'ね': '⠏', 'の': '⠎',
    'は': '⠥', 'ひ': '⠧', 'ふ': '⠭', 'へ': '⠯', 'ほ': '⠮',
    'ま': '⠵', 'み': '⠷', 'む': '⠽', 'め': '⠿', 'も': '⠾',
    'や': '⠌', 'ゆ': '⠬', 'よ': '⠜',
    'ら': '⠑', 'り': '⠓', 'る': '⠙', 'れ': '⠛', 'ろ': '⠚',
    'わ': '⠄', 'を': '⠔', 'ん': '⠴',
    'ゃ': '⠣', 'ゅ': '⠩', 'ょ': '⠜', 'ー': '⠒', '、': '⠂', '。': '⠆', ' ': ' ',
    # アルファベット（小文字）
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽', 'z': '⠵'
}

dakuten = '⠐'
handakuten = '⠠'
capital_marker = '⠠'

voiced_map = {
    'が': ('か', dakuten), 'ぎ': ('き', dakuten), 'ぐ': ('く', dakuten),
    'げ': ('け', dakuten), 'ご': ('こ', dakuten),
    'ざ': ('さ', dakuten), 'じ': ('し', dakuten), 'ず': ('す', dakuten),
    'ぜ': ('せ', dakuten), 'ぞ': ('そ', dakuten),
    'だ': ('た', dakuten), 'ぢ': ('ち', dakuten), 'づ': ('つ', dakuten),
    'で': ('て', dakuten), 'ど': ('と', dakuten),
    'ば': ('は', dakuten), 'び': ('ひ', dakuten), 'ぶ': ('ふ', dakuten),
    'べ': ('へ', dakuten), 'ぼ': ('ほ', dakuten),
    'ぱ': ('は', handakuten), 'ぴ': ('ひ', handakuten), 'ぷ': ('ふ', handakuten),
    'ぺ': ('へ', handakuten), 'ぽ': ('ほ', handakuten)
}

def to_braille(text):
    result = ''
    i = 0
    while i < len(text):
        char = text[i]
        next_char = text[i+1] if i+1 < len(text) else ''

        # 拗音（きゃ、しゅ等）
        if next_char in ['ゃ', 'ゅ', 'ょ'] and char + next_char not in voiced_map:
            result += braille_map.get(char, '⍰') + braille_map.get(next_char, '⍰')
            i += 2
            continue

        # 濁音・半濁音
        if char in voiced_map:
            base, mark = voiced_map[char]
            result += braille_map.get(base, '⍰') + mark
        # アルファベット大文字
        elif char.isalpha() and char.isupper():
            result += capital_marker + braille_map.get(char.lower(), '⍰')
        # 通常文字
        else:
            result += braille_map.get(char, '⍰')
        i += 1
    return result

braille_text = to_braille(hiragana_text)

# 結果表示＆保存
print("OCR抽出テキスト:\n", ocr_text)
print("\nひらがな変換:\n", hiragana_text)
print("\n点字変換:\n", braille_text)

with open("braille_output.txt", "w", encoding="utf-8") as f:
    f.write(braille_text)
