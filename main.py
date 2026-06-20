"""
main.py — 遊戲主迴圈（每步結束等待 ACK 版）
負責玩家互動與整體流程控制，不含任何棋盤或 AI 邏輯。
"""
import time
# 匯入你原本寫好的藍牙橋接模組（請確保檔名為 bluetooth_bridge.py）
from bluetooth import get_connected_bridge
from board import Board, other
from mcts import mcts_best_move

AI_THINK_TIME = 2.0   # AI 每步思考時間（秒）
# 1. 設定藍牙連線參數
TARGET_PORT = 'COM3'
TARGET_NAME = 'carcar'

def wait_for_ack(bluetooth_bridge, token="ACK_DONE"):
    """
    阻塞式等待，直到從藍牙端接收到指定的確認字串（預設為 ACK_DONE）才允許放行。
    """
    print(f"⏳ [實體動作執行中] 等待下位機回傳完成訊號 '{token}'...")
    while True:
        if hasattr(bluetooth_bridge, 'ser') and bluetooth_bridge.ser.in_waiting > 0:
            try:
                # 讀取一行，進行解碼並去除前後空白換行
                raw_line = bluetooth_bridge.ser.readline().decode('utf-8').strip()
                if raw_line:
                    if token in raw_line:
                        print(f"✅ [動作完成] 收到 '{token}'，準備進入下一回合。")
                        break
            except Exception as e:
                pass
        time.sleep(0.01)  # 微幅休眠避免 CPU 飆高

def choose_piece() -> tuple[str, str]:
    """讓玩家選擇棋子，回傳 (human_piece, ai_piece)"""
    print("╔══════════════════════════╗")
    print("║    四子棋 × MCTS AI      ║")
    print("╚══════════════════════════╝\n")
    print("選擇你的棋子：")
    print("  1. 黑子 O（先手）")
    print("  2. 白子 X（後手）")

    while True:
        choice = input("輸入 1 或 2：").strip()
        if choice in ('1', '2'):
            break
        print("請輸入 1 或 2。")

    human = 'O' if choice == '1' else 'X'
    ai    = other(human)
    label = {'O': '黑子(O)', 'X': '白子(X)'}
    print(f"\n你是 {label[human]}，AI 是 {label[ai]}\n")
    return human, ai

def human_turn(board: Board, piece: str) -> int:
    """取得玩家輸入的合法欄位"""
    label = '黑子(O)' if piece == 'O' else '白子(X)'
    legal = board.legal_moves()
    print(f"你的回合 {label}，可落子欄位：{legal}")
    while True:
        try:
            col = int(input("選擇欄位（0–6）："))
            if col in legal:
                return col
            print(f"欄位 {col} 無效，請重試。")
        except ValueError:
            print("請輸入整數。")

def ai_turn(board: Board, piece: str) -> int:
    """執行 AI 搜尋並回傳選定欄位"""
    label = '黑子(O)' if piece == 'O' else '白子(X)'
    print(f"\nAI 思考中 {label}…")
    return mcts_best_move(board, piece, time_limit=AI_THINK_TIME)

def game_loop(human: str, ai: str, bluetooth_bridge):
    board = Board()
    board.display()
    turn  = 'O'   # O 永遠先手

    while True:
        # ── 選擇落子欄位 ──────────────────────
        if turn == human:
            col = human_turn(board, human)
            print(f"玩家落子於欄位 {col}")
        else:
            col = ai_turn(board, ai)
            print(f"AI 落子於欄位 {col}")
    
        # 根據目前落子顏色轉換前綴 (O -> B, X -> W)
        prefix = 'B' if turn == 'O' else 'W'
        msg = f"{prefix}{col}"
        
        # 立即傳送指令給 Arduino 驅動硬體
        bluetooth_bridge.send(msg)

        # ── 落子並顯示棋盤 ────────────────────
        row = board.drop(col, turn)
        board.display()

        # ── 勝負判定 ──────────────────────────
        if board.check_win(col, row):
            if turn == human:
                print("🎉 恭喜你獲勝！")
            else:
                print("AI 獲勝！再接再厲！")
            # 💡 即使分出勝負，若想確保硬體下完最後一步，可視情況決定是否要在 break 前加上 wait_for_ack
            wait_for_ack(bluetooth_bridge, "ACK_DONE")
            break

        if board.is_full():
            print("平局！")
            wait_for_ack(bluetooth_bridge, "ACK_DONE")
            break
        
        # 💡【關鍵修正點】：在每一步的邏輯徹底跑完後，阻塞等待 Arduino 傳回動作完成訊號
        wait_for_ack(bluetooth_bridge, "ACK_DONE")
        
        time.sleep(1)
        turn = other(turn)

def connect_bluetooth_device(port='COM7', name='carcar', max_retries=3):
    """
    專門負責建立藍牙連線的函式。
    """
    print(f"📡 正在嘗試連線藍牙設備... [Port: {port}, Name: {name}]")
    
    for attempt in range(1, max_retries + 1):
        print(f"🔄 正在進行第 {attempt}/{max_retries} 次連線嘗試...")
        bridge = get_connected_bridge(port, name)
        
        if bridge is not None:
            print(f"✨ 藍牙連線成功！成功連接至 [{name}]")
            return bridge
            
        print(f"⚠️ 第 {attempt} 次連線失敗。")
        if attempt < max_retries:
            print("等待 3 秒後重新嘗試...")
            time.sleep(3)
            
    print(f"❌ 已達最大重試次數 {max_retries}，藍牙連線宣告失敗。")
    return None

def main():
    bluetooth_bridge = connect_bluetooth_device(port=TARGET_PORT, name=TARGET_NAME)
    
    if not bluetooth_bridge:
        print("🚨 無法建立藍牙連線，主程式終止。請檢查硬體電源或 COM Port。")
        return
    
    print("\n--- 主控制程式開始 ---")
    bluetooth_bridge.send("S")
    try:
        # 這裡維持發送開局指令，並等 Arduino 初始化就緒的 ACK
        print("測試：發送指令")
        bluetooth_bridge.send("S")
        human, ai = choose_piece()
        game_loop(human, ai, bluetooth_bridge)

    except Exception as e:
        print(f"💥 主程式執行期間發生錯誤: {e}")
        
    finally:
        bluetooth_bridge.send("E")
        if hasattr(bluetooth_bridge, 'ser') and bluetooth_bridge.ser.is_open:
            bluetooth_bridge.ser.close()
            print("🔌 藍牙序列埠已安全關閉。")
    
if __name__ == '__main__':
    main()