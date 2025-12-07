import cv2
import os

#PC1カメラ撮影用の.pyコード

# --- 設定 ---
CAMERA_INDEX = 0      # 使用するカメラのデバイスID (通常0が内蔵カメラ)
OUTPUT_FILENAME = "captured_image.png"
OUTPUT_DIR = "imgs/captured_images" # 画像を保存するディレクトリ

# ----------------------------------------------------
# カメラ初期化
# ----------------------------------------------------
cap = cv2.VideoCapture(CAMERA_INDEX)

# カメラが開けたか確認
if not cap.isOpened():
    print("エラー: カメラが開けませんでした。デバイスIDを確認してください。")
    exit()

print("カメラ起動中... [Spaceキー]で撮影し保存、[Escキー]で終了します。")

# ----------------------------------------------------
# 映像表示とキャプチャループ
# ----------------------------------------------------
while True:
    ret, frame = cap.read()  # 1フレーム分取得
    if not ret:
        print("エラー: フレーム取得失敗")
        break

    cv2.imshow("Camera Feed (Press SPACE to Capture)", frame)  # ウィンドウに表示

    # キー入力を待機
    key = cv2.waitKey(1) & 0xFF

    # Spaceキーが押されたかチェック
    if key == ord(' '):
        # 画像の保存処理を実行

        # ディレクトリが存在しなければ作成
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)

        # PNG形式で画像を保存 (OpenCVのデフォルトはPNG対応)
        success = cv2.imwrite(output_path, frame)

        if success:
            print(f" 画像を正常に保存しました: {output_path}")
        else:
            print(f" 画像の保存に失敗しました。")

        break # 保存後にループを抜ける

    # Escキー (ASCII 27) で終了
    elif key == 27:
        print("ユーザー操作により終了します。")
        break

# ----------------------------------------------------
# 終了処理
# ----------------------------------------------------
cap.release()
cv2.destroyAllWindows()