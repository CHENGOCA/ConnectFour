"""
rollout.py — 模擬對局
提供啟發式落子選擇（smart_pick）與隨機展開模擬（rollout）。
只依賴 board.py，不含 MCTS 樹結構。
"""

import random
from board import Board, other, COLS, ROWS


def smart_pick(board: Board, moves: list[int], piece: str) -> int:
    """
    啟發式落子選擇，優先序：
    1. 立即獲勝
    2. 擋住對手獲勝
    3. 中間欄位優先 + 隨機
    """
    opp = other(piece)

    for col in moves:                  # 1. 立即獲勝
        b = board.copy()
        row = b.drop(col, piece)
        if b.check_win(col, row):
            return col

    for col in moves:                  # 2. 擋對手
        b = board.copy()
        row = b.drop(col, opp)
        if b.check_win(col, row):
            return col

    # 3. 偏好中間欄位
    center_sorted = sorted(moves, key=lambda c: abs(c - 3))
    return center_sorted[0] if random.random() < 0.7 else random.choice(moves)


def rollout(board: Board, turn: str, ai_piece: str) -> float:
    """
    從 board 狀態、由 turn 先手，隨機模擬至終局。
    回傳值：1.0 = AI 贏, 0.5 = 平局, 0.0 = AI 輸
    """
    sim = board.copy()
    cur = turn
    while True:
        moves = sim.legal_moves()
        if not moves:
            return 0.5              # 平局
        col = smart_pick(sim, moves, cur)
        row = sim.drop(col, cur)
        if sim.check_win(col, row):
            return 1.0 if cur == ai_piece else 0.0
        cur = other(cur)