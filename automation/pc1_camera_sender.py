import cv2
import socket
import os
import time
import struct # 32bit整数をバイトデータに変換するために追加

# --- 設定 ---
CAMERA_INDEX = 0
SERVER_HOST = '192.168.x.x' # 🚨 PC2のIPアドレスに置き換えてください
SERVER_PORT = 5554          # Processingサーバーのポート
IMAGE_QUALITY = 90
# 🚨 Processingは生のRGBバイト配列を期待しているため、JPG圧縮はしないが、
# 🚨 ヘッダー形式をProcessingのコードに合わせる

def capture_and_send():
    print("--- 1. サーバー接続 ---")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((SERVER_HOST, SERVER_PORT))
        print(f"✅ サーバー {SERVER_HOST}:{SERVER_PORT} に接続しました。")
    except Exception as e:
        print(f"❌ サーバー接続エラー: {e}")
        return

    print("--- 2. カメラ初期化 ---")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("エラー: カメラが開けませんでした。")
        s.close()
        return

    print("カメラ起動中... [Spaceキー]で撮影し送信、[Escキー]で終了します。")

    while True:
        ret, frame = cap.read()
        if not ret: break

        cv2.imshow("Camera Feed (Press SPACE to Capture)", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            # 3. 画像のエンコードと送信
            
            # 生のRGBバイトデータに変換
            # Processingのコードは BGR ではなく RGB の並びを期待しているため変換
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_data = rgb_frame.tobytes() 
            
            h, w, _ = frame.shape
            size = len(image_data)
            
            # 🚨 1. ヘッダーの送信 (Processingのコードに合わせたリトルエンディアンの32bit整数4バイト x 2)
            # Processing側が (H, H, H, H) (W, W, W, W) の順序で4バイトずつ整数を読み込んでいると仮定
            # Pythonで同じバイト順を送信するのは複雑なため、ここではサイズだけを送信し、
            # Processing側でバイト形式を合わせることを推奨します。
            
            # Processingのバイト順序に合わせる (リトルエンディアン)
            # 4バイトの高さ(H)と4バイトの幅(W)を送信
            height_bytes = struct.pack('<I', h)
            width_bytes = struct.pack('<I', w)

            try:
                s.sendall(height_bytes) # 高さ (4バイト)
                s.sendall(width_bytes)  # 幅 (4バイト)
                
                # Processing側が返答 (1) を送るまで待機
                s.recv(1) 
                
                # 2. 生画像データ本体を送信
                s.sendall(image_data)
                print(f"✅ 画像データ {h}x{w} ({size} バイト) をPC2に送信完了。")
                
            except Exception as e:
                print(f"❌ データ送信エラー: {e}")
                break
            
            break
        
        elif key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    s.close()

if __name__ == "__main__":
    capture_and_send()