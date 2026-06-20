"""
board.py — 棋盤引擎
負責棋盤狀態、落子、勝負判定，不含任何 AI 邏輯。
"""

COLS, ROWS = 7, 6


def other(piece: str) -> str:
    """回傳對手棋子"""
    return 'X' if piece == 'O' else 'O'


class Board:
    """
    grid[col][row]：col 0–6（左到右），row 0–5（下到上）
    heights[col]  ：該欄下一個可落子的列索引
    """

    def __init__(self):
        self.grid    = [['_'] * ROWS for _ in range(COLS)]
        self.heights = [0] * COLS

    def copy(self) -> 'Board':
        b          = Board()
        b.grid     = [col[:] for col in self.grid]
        b.heights  = self.heights[:]
        return b

    # ── 查詢 ──────────────────────────────────

    def legal_moves(self) -> list[int]:
        return [c for c in range(COLS) if self.heights[c] < ROWS]

    def is_full(self) -> bool:
        return all(h >= ROWS for h in self.heights)

    # ── 落子 ──────────────────────────────────

    def drop(self, col: int, piece: str) -> int:
        """落子，回傳落子的列號（row）"""
        row = self.heights[col]
        self.grid[col][row] = piece
        self.heights[col] += 1
        return row

    # ── 勝負判定 ──────────────────────────────

    def check_win(self, col: int, row: int) -> bool:
        piece = self.grid[col][row]
        if piece == '_':
            return False
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            r, c = row + dr, col + dc
            while 0 <= c < COLS and 0 <= r < ROWS and self.grid[c][r] == piece:
                count += 1; r += dr; c += dc
            r, c = row - dr, col - dc
            while 0 <= c < COLS and 0 <= r < ROWS and self.grid[c][r] == piece:
                count += 1; r -= dr; c -= dc
            if count >= 4:
                return True
        return False

    # ── 顯示 ──────────────────────────────────

    def display(self):
        print()
        # 1. 每一行從最上面的 row 開始往下印
        for row in range(ROWS - 1, -1, -1):
            # 💡 將欄位 (col) 的走訪順序對調：從 COLS-1 (6) 倒數到 0
            print(' '.join(self.grid[col][row] for col in range(COLS - 1, -1, -1)))
            
        print('─' * (COLS * 2 - 1))
        
        # 💡 2. 底部的欄位編號也同步對調：從 COLS-1 (6) 倒數到 0
        print(' '.join(str(c) for c in range(COLS - 1, -1, -1)))
        print()