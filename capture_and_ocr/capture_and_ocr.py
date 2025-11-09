import cv2
import os
import subprocess
import sys
import time

CAMERA_INDEX = 1
OUTPUT_FILENAME = "captured_image.png"
YOMITOKU_SCRIPT = "yomitoku" # 環境によっては 'python yomitoku.py'かも
YOMITOKU_ARGS = "-f md -o results -v --figure"

# OCR結果出力ディレクトリ
RESULTS_DIR = "results"

def capture_image_and_run_ocr():
    """
    外部カメラから画像をキャプチャし、yomitokuを実行する。
    """

    print("1. カメラ初期化")
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print(f"エラー: カメラ (インデックス {CAMERA_INDEX}) を開けませんでした。")
        return

    print("カメラ起動中... [Space]で撮影、[Esc]で終了")

    while True:
        # フレーム読み込み
        ret, frame = cap.read()
        if not ret:
            print("エラー: フレームを読み込めませんでした。")
            break

        # プレビュー表示
        cv2.imshow("Camera Preview (Press SPACE to Capture)", frame)

        key = cv2.waitKey(1) & 0xFF

        # Spaceキーで撮影
        if key == ord(' '):
            # 2. 画像の保存
            if os.path.isdir(RESULTS_DIR) is False:
                os.makedirs(RESULTS_DIR)
                print(f"ディレクトリ '{RESULTS_DIR}' を作成しました。")

            output_path = os.path.join(RESULTS_DIR, OUTPUT_FILENAME)
            cv2.imwrite(output_path, frame)
            print(f"画像を '{output_path}' に保存しました。")

            # 3. yomitoku OCRの実行
            print("\n2. yomitoku OCR処理の開始")

            # yomitoku コマンドを構築
            # 形式: yomitoku [画像ファイルパス] [その他の引数]
            yomitoku_command = [YOMITOKU_SCRIPT, output_path] + YOMITOKU_ARGS.split()

            try:
                # サブプロセスとしてyomitokuを実行
                # NOTE: yomitokuをシステム全体で実行できるようにパスが通っている必要あり
                subprocess.run(yomitoku_command, check=True)
                print(f"✅ yomitoku 処理が完了しました。結果は '{RESULTS_DIR}' に出力されています。")
            except subprocess.CalledProcessError as e:
                print(f"yomitoku 実行中にエラーが発生しました: {e}")
            except FileNotFoundError:
                print(f"'{YOMITOKU_SCRIPT}' コマンドが見つかりません。パスが通っているか確認して")

            # OCR処理後にプレビューを閉じるためにループを抜ける
            break

        # Escキーで終了
        elif key == 27:
            break

    # リソース解放
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # 実行前に、yomitokuがインストール、パスが通っているか確認して
    capture_image_and_run_ocr()