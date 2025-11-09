import sys
import re

#.mdファイルをコマンドライン引数として受け取り、抽出された純粋なテキストを出力
#ただ、.mdファイルの受け取りまではうまくいったが、抽出された純粋なテキストを出力するのは出来ていない

def extract_clean_text_from_md(file_path):
    """
    Markdownファイルの内容を読み込み、正規表現を使用してMarkdown記号とHTMLタグをすべて除去し、
    純粋なテキスト文字列のみを抽出する。
    """
    try:
        # 1. ファイルを読み込む (OCR結果は通常UTF-8)
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"エラー: 指定されたファイル '{file_path}' が見つかりません。")
        sys.exit(1)
    except Exception as e:
        print(f"ファイル読み込み中にエラーが発生しました: {e}")
        sys.exit(1)

    # ---------------------------------------------------
    # 2. 正規表現によるクリーンアップ処理
    # ---------------------------------------------------

    text = md_content

    # 2.1. HTMLタグの除去（<img ...> や <br> を含む）
    # 例: <img src="..." width="200px"> や <br> を削除
    text = re.sub(r'<[^>]*>', '', text)

    # 2.2. リンク/画像 ([text](url)) からテキスト部分のみを抽出
    # 例: [PyTorch](http://example.com) -> PyTorch
    text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)

    # 2.3. 見出し (#) やリスト記号 (*, -, 1.) の除去
    # 行頭のMarkdown構造を削除
    text = re.sub(r'^\s*#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

    # 2.4. 強調、コードブロック (*, _, `) の除去
    # 例: **太字**, `コード`
    text = re.sub(r'[*_`]', '', text)

    # 2.5. 連続する改行を一つの改行に統一
    text = re.sub(r'\n{2,}', '\n', text)

    # 2.6. 前後の空白行やスペースを削除
    return text.strip()

# =========================================================
# メイン実行ブロック
# =========================================================
if __name__ == '__main__':
    # コマンドライン引数のチェック
    if len(sys.argv) < 2:
        print("エラー: 処理対象のMarkdownファイルパスを引数として指定してください。")
        print("使用法: python md_text_cleaner.py [ファイル名.md]")
        sys.exit(1)

    md_file_path = sys.argv[1] # ファイルパスを取得

    # 実行
    extracted_text = extract_clean_text_from_md(md_file_path)

    # 抽出された純粋なテキストを出力
    print("--- 抽出された純粋なテキスト ---")
    print(extracted_text)
    print("------------------------------")