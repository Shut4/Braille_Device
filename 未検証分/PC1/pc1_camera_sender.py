import cv2
import socket
import numpy as np
import time
import struct
import os
import sys

# --- 設定 ---
PC2_IP = '192.168.1.10'    # PC2のIPアドレスに修正してください
PC2_PORT = 5554           # PC2のimg_Net_Server.pde のポート
CAMERA_INDEX = 0          # カメラのインデックス (通常は 0)

def send_frame_to_pc2(frame):
    """取得したフレームをPC2へRAW RGBデータとして送信する。"""

    # 1. 画像寸法とデータ形式の準備
    ImgHeight, ImgWidth, ImgChannels = frame.shape
    # OpenCVはBGR形式で読み込むため、RGBに変換
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # RAW RGBデータをバイト配列に変換
    img_data = rgb_frame.tobytes()

    # ヘッダーデータを作成 (高さ, 幅を4バイトリトルエンディアンで送信)
    # <i: 4バイトint little-endian
    header = struct.pack('<iiii', ImgHeight, ImgWidth, 0, 0)

    # --- ネットワーク送信 ---
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((PC2_IP, PC2_PORT))

        # 1. ヘッダー (高さ, 幅) を送信
        s.sendall(header)
        print(f"✅ ヘッダー送信完了: H={ImgHeight}, W={ImgWidth}")

        # 2. ACK (1バイト) を待機 (img_Net_Server.pde の状態遷移待ち)
        s.settimeout(5.0) # 5秒でタイムアウト設定
        ack = s.recv(1)
        if ack != b'\x01':
            print("❌ エラー: PC2からのACK (1) を受信できませんでした。")
            return False

        # 3. 画像データを送信
        s.sendall(img_data)
        print(f"✅ 画像データ送信完了。サイズ: {len(img_data)} bytes -> PC2:{PC2_PORT}")
        return True

    except ConnectionRefusedError:
        print(f"❌ 接続エラー: PC2 ({PC2_IP}:{PC2_PORT}) が接続を拒否しました。")
        return False
    except socket.timeout:
        print("❌ 接続タイムアウト: PC2からの応答がありませんでした。")
        return False
    except Exception as e:
        print(f"❌ 送信エラー: {e}")
        return False
    finally:
        if 's' in locals():
            s.close()

def main_camera_shooter():
    """
    カメラプレビューを表示し、キー入力によって画像送信をトリガーする。
    """
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("❌ エラー: カメラを開けませんでした。プログラムを終了します。")
        sys.exit(1)

    print("--- PC1 カメラ画像送信クライアント起動 ---")
    print("▶️ プレビューが表示されます。")
    print("▶️ **'S'** キーを押すと、現在の画像をキャプチャし、PC2へ送信します。")
    print("▶️ **'Q'** キーを押すと、プログラムを終了します。")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ エラー: フレームの読み込みに失敗しました。")
            break

        # プレビューを表示
        cv2.imshow("Camera Preview (PC1) - Press 'S' to Send", frame)

        # キー入力を待機 (1ミリ秒)
        key = cv2.waitKey(1) & 0xFF

        # 'S' キーで送信をトリガー
        if key == ord('s') or key == ord('S'):
            print("\n--- 'S' キーが押されました。画像送信を開始します... ---")
            send_frame_to_pc2(frame)
            print("\n--- 送信完了。次のページを撮影してください。 ---")

        # 'Q' キーで終了
        elif key == ord('q') or key == ord('Q'):
            break

    # クリーンアップ
    cap.release()
    cv2.destroyAllWindows()
    print("--- PC1 カメラクライアントを終了しました。 ---")

if __name__ == '__main__':
    main_camera_shooter()