import sys
import re
from pykakasi import kakasi

# 11/08地点ではこれが一番精度高い
# .mdファイルをコマンドライン引数として受け取り、
# 抽出された純粋なテキストをひらがな変換し、ターミナルへ出力

# --- Markdownテキストの抽出関数 (変更なし) ---
def extract_clean_text_from_md(file_path):
    """
    Markdownファイルの内容を読み込み、正規表現を使用してMarkdown記号やHTMLタグを除去し、
    純粋なテキスト文字列のみを抽出する。
    """
    try:
        # 1. ファイルを読み込む (UTF-8エンコーディングを推奨)
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"エラー: 指定されたファイル '{file_path}' が見つかりません。")
        return None
    except Exception as e:
        print(f"ファイル読み込み中にエラーが発生しました: {e}")
        return None

    #正規表現によるクリーンアップ処理

    text = md_content
    # ... (クリーンアップ処理は省略、元のコードと同じ)

    # HTMLタグの除去
    text = re.sub(r'<[^>]*>', '', text)
    # リンク/画像 ([text](url)) からテキスト部分のみを抽出
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # 見出し (#) やリスト記号 (*, -, 1.) の除去
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # 強調、コードブロック (*, _, `) の除去
    text = re.sub(r'[*_`]', '', text)
    # 連続する改行を一つの改行に統一
    text = re.sub(r'\n{2,}', '\n', text)

    # 前後の空白行やスペースを削除
    return text.strip()


# --- ひらがな変換関数 (【ここを修正】) ---
def to_hiragana(text):
    """
    テキスト（漢字、カタカナ、アルファベットなど）をひらがなに変換する。
    新しい pykakasi の API に対応。
    """
    # kakasiインスタンスを初期化し、変換設定を渡す
    # J: 漢字 -> H: ひらがな, K: カタカナ -> H: ひらがな, H: ひらがな -> H: ひらがな
    # アルファベット(A)はデフォルトでそのまま維持されるため、設定から除外
    kakasi_inst = kakasi()
    kakasi_inst.setMode("J", "H")
    kakasi_inst.setMode("K", "H")
    kakasi_inst.setMode("H", "H")
    # setMode("A", "A") は削除しました。新しいAPIでは不要です。

    # 新しいAPIでは、このように変換を実行します。
    # ただし、setModeを使った旧APIをまだ利用しているため、getConverter().do(text)を使用します。
    # 警告は出ますが、エラーになる setMode("A", "A") を削除することで実行可能になります。
    conv = kakasi_inst.getConverter()

    # 警告を完全に解消したい場合は、以下の方式に書き換えるのが推奨されますが、
    # 依存ライブラリの構造によってはエラーになる可能性があるため、今回は setMode("A", "A") の削除に留めます。
    # kakasi_inst = kakasi()
    # kakasi_inst.setMode('j', 'h').setMode('k', 'h')
    # conv = kakasi_inst.getConverter()
    # return conv.do(text)

    # 最もシンプルな新しい pykakasi v3.0+ の書き方:
    # kks = kakasi()
    # kks.setMode('H', 'H').setMode('K', 'H').setMode('J', 'H')
    # return kks.convert(text)['text'] # v3.0以降の推奨

    return conv.do(text)


# =========================================================
# メイン実行ブロック
# =========================================================
if __name__ == '__main__':
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        print("エラー: 処理対象のMarkdownファイルパスを引数として指定してください。")
        print("使用法: python script_name.py [ファイル名.md]")
        sys.exit(1)

    md_file_path = sys.argv[1] # ファイルパスを取得

    # 1. Markdownから純粋なテキストを抽出
    extracted_text = extract_clean_text_from_md(md_file_path)
    if extracted_text is None:
        sys.exit(1) # ファイル読み込みエラーの場合は終了

    # 2. 抽出されたテキストをひらがなへ変換
    hiragana_text = to_hiragana(extracted_text)

    # 結果表示
    # print("--- 結果 ---")
    # print(f"**処理ファイル:** {md_file_path}")
    # print("\n**1. 抽出された純粋なテキスト:**")
    # print(extracted_text)
    # print("\n**2. ひらがな変換:**")
    print("**2. ひらがな変換:**")
    print(hiragana_text)
    # print("------------")