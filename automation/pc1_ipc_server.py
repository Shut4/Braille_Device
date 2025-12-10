import cv2
import socket
import numpy as np
import time
import struct
import sys
import os

# --- 設定 (Processingと共有する設定) ---
IPC_HOST = '127.0.0.1'
IPC_PORT = 6000          # Processingが接続するポート
CAMERA_INDEX = 0         
# ----------------------

def send_frame_to_pc2(frame):
    """取得したフレームをPC1 Processingクライアントに送信する。"""
    
    # 1. RAW RGBデータとヘッダーの準備
    ImgHeight, ImgWidth, ImgChannels = frame.shape
    # OpenCVはBGR形式のため、RGBに変換
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_data = rgb_frame.tobytes() 
    
    # Processingのプロトコルに合わせるヘッダー (高さ, 幅を4バイトintで)
    header = struct.pack('<iiii', ImgHeight, ImgWidth, 0, 0)

    # 2. IPCサーバーの起動 (一時的なTCPサーバー)
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((IPC_HOST, IPC_PORT))
        server_socket.listen(1)
        server_socket.settimeout(20.0) 
        
        sys.stderr.write(f"✅ IPCサーバー起動。Processingクライアントからの接続を待機中...\n")
        
        # 3. クライアント接続の受け入れ
        client_conn, client_addr = server_socket.accept()
        sys.stderr.write(f"✅ Processingクライアント ({client_addr[0]}:{client_addr[1]}) と接続しました。\n")
        
        # 4. ヘッダー送信 
        client_conn.sendall(header)
        
        # 5. ACKを待機 (Processingがヘッダーを受信したことを示す1バイト)
        ack = client_conn.recv(1)
        if ack != b'\x01':
            sys.stderr.write("❌ エラー: ProcessingクライアントからACK (1) を受信できませんでした。\n")
            return False

        # 6. 画像データ本体を送信
        client_conn.sendall(img_data)
        sys.stderr.write(f"✅ 画像データ送信完了。サイズ: {len(img_data)} bytes\n")
        
        return True
    
    except socket.timeout:
        sys.stderr.write("❌ タイムアウト: Processingクライアントからの接続がありませんでした。\n")
        return False
    except Exception as e:
        sys.stderr.write(f"❌ IPCサーバーエラー: {e}\n")
        return False
    finally:
        if 'server_socket' in locals():
            server_socket.close()

def main_camera_shooter_sender():
    """カメラプレビューを表示し、Spaceキーで画像をキャプチャ/IPCサーバーを起動する。"""
    
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        sys.stderr.write("❌ エラー: カメラを開けませんでした。プログラムを終了します。\n")
        sys.exit(1)

    sys.stderr.write("--- PC1 カメラクライアント起動 (Python) ---\n")
    
    while True:
        ret, frame = cap.read()
        if not ret: break

        cv2.imshow("PC1 Camera Preview - Press [SPACE] to Shoot & Send", frame)

        key = cv2.waitKey(1) & 0xFF
        
        # Spaceキー (ASCIIコード 32)
        if key == 32: 
            sys.stderr.write("\n--- [SPACE] キーが押されました。画像キャプチャとIPCサーバーを起動します... ---\n")
            
            # カメラをリリースして再度オープンすることで、撮影時のカメラバッファの古いフレームを防ぐ
            cap.release()
            
            # 再度キャプチャ
            temp_cap = cv2.VideoCapture(CAMERA_INDEX)
            if temp_cap.isOpened():
                ret, captured_frame = temp_cap.read()
                temp_cap.release()
                if ret:
                    send_frame_to_pc2(captured_frame)
            
            # メインループのプレビューのためにカメラを再オープン
            cap = cv2.VideoCapture(CAMERA_INDEX)

            sys.stderr.write("\n--- IPCサーバーシャットダウン。次の撮影を待機中。 ---\n")
            
        elif key == ord('q') or key == ord('Q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    sys.stderr.write("--- PC1 カメラクライアントを終了しました。 ---\n")

if __name__ == '__main__':
    main_camera_shooter_sender()